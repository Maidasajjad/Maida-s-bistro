"""Maida's Bistro - Homepage. Run with: streamlit run app.py"""
import streamlit as st
from utils import setup, hero, footer
from database import db

setup("Maida's Bistro")
hero("Maida's Bistro", "Fine Pakistani & continental dining in the heart of Islamabad")

c1, c2, c3 = st.columns(3)
c1.page_link("pages/menu.py", label="View Menu & Order", icon="📜")
c2.page_link("pages/reservations.py", label="Book a Table", icon="🕯️")
c3.page_link("pages/admin.py", label="Staff Login", icon="🔐")

st.markdown("## Our Story")
st.write("Maida's Bistro brings family recipes and slow-cooked tradition to a warm, candle-lit setting. "
         "Every dish is prepared fresh daily with the finest local ingredients.")

st.markdown("## Chef's Selection")
featured = [i for i in db.get_menu() if i["status"] != "Out of Stock"][:3]
cols = st.columns(3)
for col, i in zip(cols, featured):
    with col:
        st.markdown(f'<div class="card"><div class="img">{i["emoji"]}</div><div class="body">'
                    f'<h4>{__import__("html").escape(i["name"])}</h4>'
                    f'<span class="price">PKR {i["price"]:,}</span></div></div>', unsafe_allow_html=True)

st.markdown("## Visit Us")
st.write("📍 Islamabad, Pakistan  ·  🕛 Daily 12:00 – 23:00  ·  📞 +92 300 0000000")
footer()
