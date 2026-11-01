"""Customer menu with live stock status and ordering."""
import re
from html import escape
import streamlit as st
from utils import setup, hero, footer
from database import db

setup("Menu · Maida's Bistro", "📜")
hero("Our Menu", "Prices in Pakistani Rupees (PKR) · availability updates live")

st.session_state.setdefault("cart", {})
cart = st.session_state.cart
menu = db.get_menu()
by_id = {i["id"]: i for i in menu}

# --- Filters ---
categories = ["All"] + sorted({i["category"] for i in menu})
f1, f2 = st.columns([2, 1])
cat = f1.selectbox("Category", categories)
query = f2.text_input("Search dishes", max_chars=40)

shown = [i for i in menu if (cat == "All" or i["category"] == cat) and query.lower() in i["name"].lower()]
BADGE = {"Available": "b-ok", "Low Stock": "b-low", "Out of Stock": "b-out"}

for cat_name in sorted({i["category"] for i in shown}):
    st.markdown(f"## {escape(cat_name)}")
    items = [i for i in shown if i["category"] == cat_name]
    for start in range(0, len(items), 3):
        cols = st.columns(3)
        for col, i in zip(cols, items[start:start + 3]):
            with col:
                url = i["image_url"]
                img = (f'<img src="{escape(url)}" alt="{escape(i["name"])}">'
                       if url.startswith("https://") else i["emoji"])
                st.markdown(
                    f'<div class="card"><div class="img">{img}</div><div class="body">'
                    f'<span class="badge {BADGE[i["status"]]}">{i["status"]}</span><h4>{escape(i["name"])}</h4>'
                    f'<p>{escape(i["description"])}</p><span class="price">PKR {i["price"]:,}</span></div></div>',
                    unsafe_allow_html=True)
                if i["status"] == "Out of Stock":
                    st.button("Unavailable", key=f"b{i['id']}", disabled=True, use_container_width=True)
                elif st.button("Add to order", key=f"b{i['id']}", use_container_width=True):
                    if cart.get(i["id"], 0) < i["stock_qty"]:
                        cart[i["id"]] = cart.get(i["id"], 0) + 1
                    else:
                        st.warning("Maximum available quantity added.")
                    st.rerun()

if not shown:
    st.info("No dishes match your search.")

# --- Cart & checkout ---
st.markdown("## 🧾 Your Order")
cart_items = {k: v for k, v in cart.items() if k in by_id}
if not cart_items:
    st.caption("Your order is empty. Add dishes above.")
else:
    total = 0
    for iid, qty in list(cart_items.items()):
        it = by_id[iid]
        total += it["price"] * qty
        a, b, c = st.columns([4, 2, 1])
        a.write(f"**{it['name']}**")
        b.write(f"{qty} × PKR {it['price']:,}")
        if c.button("✕", key=f"rm{iid}"):
            del cart[iid]
            st.rerun()
    st.markdown(f"### Total: PKR {total:,}")
    with st.form("checkout"):
        name = st.text_input("Your name", max_chars=60)
        phone = st.text_input("Phone (e.g. 0300 1234567)", max_chars=20)
        notes = st.text_area("Notes (optional)", max_chars=200)
        if st.form_submit_button("Place Order"):
            if len(name.strip()) < 2:
                st.error("Please enter your name.")
            elif not re.fullmatch(r"[+0-9 \-]{10,16}", phone.strip()):
                st.error("Please enter a valid phone number.")
            else:
                try:
                    oid, t = db.place_order(name.strip(), phone.strip(), notes.strip(), cart_items)
                    st.session_state.cart = {}
                    st.success(f"✅ Order #{oid} placed! Total PKR {t:,}. We'll contact you shortly.")
                except ValueError as e:
                    st.error(str(e))
footer()
