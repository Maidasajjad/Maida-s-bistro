"""Password-protected admin dashboard."""
import hmac
import time
import pandas as pd
import streamlit as st
from utils import setup, get_secret
from database import db

setup("Admin · Maida's Bistro", "🔐")
st.title("🔐 Admin Dashboard")

ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")
if not ADMIN_PASSWORD or len(str(ADMIN_PASSWORD)) < 8:
    st.error("Admin is disabled. Set ADMIN_PASSWORD (8+ characters) in .env or Streamlit secrets. See README.")
    st.stop()

ss = st.session_state
ss.setdefault("admin_ok", False)
ss.setdefault("fails", 0)
ss.setdefault("locked_until", 0.0)

if not ss.admin_ok:
    if time.time() < ss.locked_until:
        st.error(f"Too many attempts. Try again in {int(ss.locked_until - time.time())} seconds.")
        st.stop()
    with st.form("login"):
        pw = st.text_input("Admin password", type="password")
        if st.form_submit_button("Log in"):
            if hmac.compare_digest(pw.encode(), str(ADMIN_PASSWORD).encode()):
                ss.admin_ok, ss.fails = True, 0
                st.rerun()
            ss.fails += 1
            if ss.fails >= 5:
                ss.locked_until, ss.fails = time.time() + 60, 0
            st.error("Incorrect password.")
    st.stop()

if st.button("Log out"):
    ss.admin_ok = False
    st.rerun()

menu = db.get_menu(include_inactive=True)
orders = db.get_orders()
resv = db.get_reservations()

tabs = st.tabs(["📊 Overview", "🍽️ Menu & Prices", "📦 Stock", "🧾 Orders", "🕯️ Reservations"])

with tabs[0]:
    m = st.columns(4)
    m[0].metric("Pending orders", sum(o["status"] == "Pending" for o in orders))
    m[1].metric("Revenue (completed)", f"PKR {sum(o['total'] for o in orders if o['status'] == 'Completed'):,}")
    m[2].metric("Pending bookings", sum(r["status"] == "Pending" for r in resv))
    m[3].metric("Low / out of stock", sum(i["status"] != "Available" and i["is_active"] for i in menu))
    alerts = [i for i in menu if i["status"] != "Available" and i["is_active"]]
    if alerts:
        st.subheader("⚠️ Stock alerts")
        st.dataframe(pd.DataFrame(alerts)[["name", "stock_qty", "status"]], hide_index=True, use_container_width=True)

with tabs[1]:
    st.subheader("Add or edit a dish")
    options = {"➕ New dish": None} | {f"{i['name']} (#{i['id']})": i for i in menu}
    pick = options[st.selectbox("Select dish", list(options))]
    d = pick or {"name": "", "category": "Main Course", "description": "", "price": 500, "image_url": "",
                 "emoji": "🍽️", "stock_qty": 10, "low_threshold": 5, "is_active": 1}
    with st.form(f"item_{d.get('id', 'new')}"):
        a, b = st.columns(2)
        name = a.text_input("Name", d["name"], max_chars=80)
        category = b.text_input("Category", d["category"], max_chars=40)
        desc = st.text_area("Description", d["description"], max_chars=250)
        a, b, c = st.columns(3)
        price = a.number_input("Price (PKR)", 0, 1_000_000, int(d["price"]), step=10)
        stock = b.number_input("Stock quantity", 0, 100_000, int(d["stock_qty"]))
        low = c.number_input("Low-stock alert at", 0, 1000, int(d["low_threshold"]))
        a, b = st.columns(2)
        img = a.text_input("Image URL (https://…, optional)", d["image_url"])
        emoji = b.text_input("Emoji (shown if no image)", d["emoji"], max_chars=4)
        active = st.checkbox("Show on menu", bool(d["is_active"]))
        s1, s2 = st.columns(2)
        save = s1.form_submit_button("Save dish")
        delete = s2.form_submit_button("Delete dish") if pick else False
        if save:
            if not name.strip() or not category.strip():
                st.error("Name and category are required.")
            elif img.strip() and not img.strip().startswith("https://"):
                st.error("Image URL must start with https://")
            else:
                db.save_item(d.get("id"), name, category, desc, price, img, emoji, stock, low, active)
                st.success("Saved.")
                st.rerun()
        if delete:
            db.delete_item(d["id"])
            st.rerun()

with tabs[2]:
    st.subheader("Stock levels")
    st.caption("Status updates automatically: Out of Stock at 0, Low Stock at or below the alert level.")
    df = pd.DataFrame(menu)[["id", "name", "stock_qty", "low_threshold", "status"]]
    edited = st.data_editor(df, hide_index=True, use_container_width=True, key="stock_ed",
                            disabled=["id", "name", "status"])
    if st.button("Save stock changes"):
        for _, r in edited.iterrows():
            db.update_stock(int(r["id"]), r["stock_qty"], r["low_threshold"])
        st.success("Stock updated.")
        st.rerun()

with tabs[3]:
    if not orders:
        st.info("No orders yet.")
    else:
        st.dataframe(pd.DataFrame(orders)[["id", "created_at", "customer_name", "phone", "items", "total", "status", "notes"]],
                     hide_index=True, use_container_width=True)
        with st.form("ord_status"):
            a, b = st.columns(2)
            oid = a.selectbox("Order #", [o["id"] for o in orders])
            stt = b.selectbox("New status", db.ORDER_STATUSES)
            if st.form_submit_button("Update order"):
                db.set_order_status(oid, stt)
                st.rerun()

with tabs[4]:
    if not resv:
        st.info("No reservations yet.")
    else:
        st.dataframe(pd.DataFrame(resv)[["id", "ref", "date", "time", "name", "phone", "party_size",
                                         "table_label", "status", "requests"]],
                     hide_index=True, use_container_width=True)
        with st.form("res_status"):
            a, b = st.columns(2)
            rid = a.selectbox("Reservation ID", [r["id"] for r in resv])
            stt = b.selectbox("New status", db.RES_STATUSES)
            if st.form_submit_button("Update reservation"):
                db.set_reservation_status(rid, stt)
                st.rerun()
