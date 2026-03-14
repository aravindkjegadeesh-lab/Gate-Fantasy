import streamlit as st
import pandas as pd
import sqlite3
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('fantasy.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
    conn.commit()
    return conn

conn = init_db()

# --- BRIGHT THEME CSS ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #f0f2f5; color: #1c1e21; }
    
    /* Header Styling */
    .fpl-header {
        background: #38003c;
        padding: 25px;
        border-radius: 12px;
        border-bottom: 5px solid #00ff87;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Text and Labels */
    h1, h2, h3, p, label { color: #38003c !important; font-weight: 600; }
    .stMarkdown { color: #333333; }

    /* Button Styling */
    .stButton>button {
        background-color: #00ff87 !important;
        color: #38003c !important;
        font-weight: bold !important;
        border: 1px solid #38003c !important;
        border-radius: 8px !important;
    }

    /* Input Boxes */
    .stTextInput>div>div>input { background-color: white !important; color: #1c1e21 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PLAYER DATA ---
MARKET_DATA = [
    {"name": "Ming", "price": 36.0}, {"name": "Cirrus", "price": 35.5}, {"name": "Gautham", "price": 33.0}, 
    {"name": "Dev", "price": 32.5}, {"name": "Forrest", "price": 30.0}, {"name": "Talal", "price": 28.5}, 
    {"name": "Geonhee", "price": 27.0}, {"name": "Hardy", "price": 23.0}, {"name": "Ethan Yuen", "price": 22.5}, 
    {"name": "Abdul", "price": 22.0}, {"name": "Lucas Yiu", "price": 22.0}, {"name": "Adhvik", "price": 21.0}, 
    {"name": "Sid", "price": 20.0}, {"name": "Barnabas", "price": 20.0}, {"name": "Komron", "price": 20.0}, 
    {"name": "Michael", "price": 20.0}, {"name": "Nathan", "price": 20.0}, {"name": "Ethan Wang", "price": 19.5}, 
    {"name": "Josh", "price":}
