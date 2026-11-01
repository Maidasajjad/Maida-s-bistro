"""Customer table booking."""
import re
from datetime import timedelta
import streamlit as st
from utils import setup, hero, footer
from database import db

setup("Reservations · Maida's Bistro", "🕯️")
hero("Reserve a Table", "Secure your evening with us · tables held for 2 hours")

today = db.now().date()
c1, c2 = st.columns(2)
date = c1.date_input("Date", value=today, min_value=today, max_value=today + timedelta(days=60))
party = c2.number_input("Number of guests", min_value=1, max_value=10, value=2)

slots = db.available_slots(str(date), int(party))
if date == today:  # hide times that have already passed
    slots = [s for s in slots if int(s[:2]) > db.now().hour]

if not slots:
    st.warning("No tables available for that date and party size. Please try another day.")
else:
    with st.form("book"):
        time = st.selectbox("Available times", slots)
        name = st.text_input("Full name", max_chars=60)
        phone = st.text_input("Phone (e.g. 0300 1234567)", max_chars=20)
        req = st.text_area("Special requests (birthday, allergies...)", max_chars=300)
        if st.form_submit_button("Confirm Reservation"):
            if len(name.strip()) < 2:
                st.error("Please enter your name.")
            elif not re.fullmatch(r"[+0-9 \-]{10,16}", phone.strip()):
                st.error("Please enter a valid phone number.")
            else:
                try:
                    ref, table = db.create_reservation(name.strip(), phone.strip(), int(party), str(date), time, req.strip())
                    st.success(f"✅ Booked! Reference **{ref}** · Table {table} · {date} at {time}. "
                               "Please save your reference. Our team will confirm by phone.")
                except ValueError as e:
                    st.error(str(e))
footer()
