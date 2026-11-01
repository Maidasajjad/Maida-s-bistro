"""Shared helpers: page setup, CSS loading, secrets."""
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from database import db

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")  # loads .env for local development


def get_secret(name, default=None):
    """Read from Streamlit secrets (Cloud) first, then environment variables (local)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def setup(title, icon="🍽️"):
    """Call first on every page: config, styling, database creation."""
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    db.init_db()


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><div class="gold-line"></div><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def footer():
    st.markdown('<div class="footer">© Maida\'s Bistro · Islamabad, Pakistan · Open daily 12:00 – 23:00</div>',
                unsafe_allow_html=True)
