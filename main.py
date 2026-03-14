import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP & AUTO-FIXER ---
def init_db():
    conn = sqlite3.connect('fantasy.db', check_same_thread=False)
    c = conn.cursor()
    
    # 1. Ensure tables exist
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, captain TEXT, 
                  tc_available INTEGER DEFAULT 1, tc_active INTEGER DEFAULT 0, total_points REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT, subjects TEXT)''')

    # 2. Table for Score History
    c.execute('''CREATE TABLE IF NOT EXISTS score_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT, subject TEXT, mark REAL, points REAL, timestamp TEXT)''')
    
    # 3. Migration: Add missing columns if needed
    c.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in c.fetchall()]
    for col, dtype in [('captain', 'TEXT DEFAULT "None"'), ('tc_available', 'INTEGER DEFAULT 1'), ('tc_active', 'INTEGER DEFAULT 0')]:
        if col not in user_cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")

    c.execute("PRAGMA table_info(game_state)")
    state_cols = [col[1] for col in c.fetchall()]
    if 'subjects' not in state_cols:
        c.execute("ALTER TABLE game_state ADD COLUMN subjects TEXT DEFAULT 'None'")

    c.execute("SELECT COUNT(*) FROM game_state")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO game_state (id, current_round, deadline, subjects) VALUES (1, 'Round 1', 'Not Set', 'None')")
    
    conn.commit()
    return conn

db_conn = init_db()

# --- FORMULA: 4(mark-70)^1.2 ---
def calculate_fpl_points(mark):
    if mark <= 70: return 0
    return round(4 * math.pow((mark - 70), 1.2), 1)

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1c1e21; }
    p, h1, h2, h3, h4, span, label { color: #38003c !important; font-weight
