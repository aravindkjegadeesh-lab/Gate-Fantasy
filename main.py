import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('fantasy.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, captain TEXT, 
                  tc_available INTEGER DEFAULT 1, tc_active INTEGER DEFAULT 0, total_points REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT, subjects TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS score_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT, subject TEXT, mark REAL, points REAL, timestamp TEXT)''')
    
    # Ensure all columns exist to prevent KeyErrors
    c.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in c.fetchall()]
    for col, dtype in [('captain', 'TEXT DEFAULT "None"'), ('tc_available', 'INTEGER DEFAULT 1'), ('tc_active', 'INTEGER DEFAULT 0')]:
        if col not in user_cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
    
    c.execute("SELECT COUNT(*) FROM game_state")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO game_state (id, current_round, deadline, subjects) VALUES (1, 'Round 1', 'Not Set', 'None')")
    conn.commit()
    return conn

db_conn = init_db()

# --- SCORING & DATA ---
def calculate_fpl_points(mark):
    if mark <= 70: return 0
    return round(4 * math.pow((mark - 70), 1.2), 1)

MARKET_DATA = [
    {"name": "Ming", "price": 36.0}, {"name": "Cirrus", "price": 35.5}, {"name": "Gautham", "price": 33.0}, 
    {"name": "Dev", "price": 32.5}, {"name": "Forrest", "price": 30.0}, {"name": "Talal", "price": 28.5}, 
    {"name": "Geonhee", "price": 27.0}, {"name": "Hardy", "price": 23.0}, {"name": "Ethan Yuen", "price": 22.5}, 
    {"name": "Abdul", "price": 22.0}, {"name": "Lucas Yiu", "price": 22.0}, {"name": "Adhvik", "price": 21.0}, 
    {"name": "Sid", "price": 20.0}, {"name": "Barnabas", "price": 20.0}, {"name": "Komron", "price": 20.0}, 
    {"name": "Michael", "price": 20.0}, {"name": "Nathan", "price": 20.0}, {"name": "Ethan Wang", "price": 19.5}, 
    {"name": "Josh", "price": 19.0}, {"name": "Daren", "price": 17.5}, {"name": "Aravind", "price": 17.0}, 
    {"name": "Alfie", "price": 16.0}, {"name": "Musa", "price": 15.0}, {"name": "Maxwell", "price": 14.0}, 
    {"name": "Andre", "price": 14.0}, {"name": "Inesh", "price": 14.0}, {"name": "Maximus", "price": 13.0}, 
    {"name": "Jared", "price": 13.0}, {"name": "Lucas Lau", "price": 12.0}, {"name": "Alden", "price": 11.0}, 
    {"name": "Sanjit", "price": 10.5}, {"name": "Yashwant", "price": 10.5}, {"name": "Maxi", "price": 10.0}, 
    {"name": "Raymond", "price": 9.5}, {"name": "Hassan", "price": 9.0}, {"name": "Lucas Kong", "price": 8.0}
]
player_prices = {p['name']: p['price'] for p in MARKET_DATA}
player_options = [f"{p['name']} (£{p['price']}m)" for p in MARKET_DATA]

# --- STYLING ---
st.markdown("""<style>
    .stApp { background-color: #FFFFFF; color: #1c1e21; }
    p, h1, h2, h3, h4, span, label { color: #38003c !important; font-weight: 600; }
    .fpl-header { background: #38003c; padding: 20px; border-radius: 10px; border-bottom: 5px solid #00ff87; text-align: center; margin-bottom: 25px; }
    .stButton>button { background-color: #00ff87 !important; color: #38003c !important; font-weight: bold !important; border-radius: 8px !important; }
    .card { background: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #38003c; margin-bottom: 10px; }
    </style>""", unsafe_allow_html=True)

# --- AUTH LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.button("Log In"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.authenticated, st.session_state.username = True, u
                st.rerun()
    with t2:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("Register"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Success!")
            except: st.error("Error creating account.")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Nav", ["Dashboard", "Player Stats", "My Squad", "Leaderboard", "Admin"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.metric("Active Round", info['current_round'])
        st.markdown("### 📝 Recent Test Results")
        hist = pd.read_sql("SELECT student as Student, subject as Subject, mark as Mark, points as Points FROM score_history ORDER BY id DESC LIMIT 5", db_conn)
        if not hist.empty:
            st.table(hist)
        else:
            st.info("No test scores recorded yet.")

    elif page == "Player Stats":
        st.header("📊 Student Performance")
        stats_df = pd.read_sql("SELECT student as Name, SUM(points) as Total_Points, AVG(mark) as Avg_Mark FROM score_history GROUP BY student ORDER BY Total_Points DESC", db_conn)
        if not stats_df.empty:
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("Statistics will appear once marks are entered.")

    elif page == "My Squad":
        st.header("🏃 Squad Management")
        user = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.username,)).iloc[0]
        tab_pick, tab_view = st.tabs(["Pick Team", "My Team"])
        
        with tab_pick:
            sel = st.multiselect("Select 5 Players", player_options, max_selections=5)
            s_names = [s.split(" (£")[0] for s in sel]
            cost = sum(player_prices[n] for n in s_names)
            st.write(f"Budget: £{cost}m / £90m")
            if len(s_names) == 5 and cost <= 90:
                cap = st.selectbox("Captain", s_names)
                tc = st.checkbox("Triple Captain") if user['tc_available'] == 1 else False
                if st.button("Save Squad"):
                    db_conn.execute("UPDATE users SET team=?, captain=?, tc_active=? WHERE username=?", (", ".join(s_names), cap, 1 if tc else 0, st.session_state.username))
                    db_conn.commit()
                    st.rerun()
        
        with tab_view:
            if user['team'] != "None":
                t_names = user['team'].split(", ")
                t_cost = sum(player_prices[p] for p in t_names)
                st.markdown(f'<div class="card"><b>Team:</b> {user["team"]}<br><b>Captain:</b> {user["captain"]}<br><b>Budget Used:</b> £{t_cost}m</div>', unsafe_allow_index=True, unsafe_allow_html=True)
            else: st.info("Pick a team first!")

    elif page == "Leaderboard":
        st.header("🏆 Global Rankings")
        lb = pd.read_sql("SELECT username as Manager, total_points as Points FROM users ORDER BY total_points DESC", db_conn)
        st.dataframe(lb, use_container_width=True, hide_index=True)

    elif page == "Admin":
        if st.text_input("Key", type="password") == "gate2026":
            t1, t2 = st.tabs(["Scores", "Tools"])
            with t1:
                sb, st_n = st.selectbox("Subject", ["Maths", "Science", "English", "HASS"]), st.selectbox("Student", [p['name'] for p in MARKET_DATA])
                mk = st.number_input("Mark", 0.0, 100.0)
                if st.button("Apply Score"):
                    pts = calculate_fpl_points(mk)
                    ts = datetime.now().strftime("%H:%M")
                    db_conn.execute("INSERT INTO score_history (student, subject, mark, points, timestamp) VALUES (?, ?, ?, ?, ?)", (st_n, sb, mk, pts, ts))
                    c = db_conn.cursor()
                    for m_n, m_t, m_c, m_tc in c.execute("SELECT username, team, captain, tc_active FROM users").fetchall():
                        if m_t and st_n in m_t:
                            mult = 3 if (st_n == m_c and m_tc) else (2 if st_n == m_c else 1)
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (pts * mult, m_n))
                            if m_tc: c.execute("UPDATE users SET tc_available=0, tc_active=0 WHERE username=?", (m_n,))
                    db_conn.commit()
                    st.success("Points Added!")
            with t2:
                u_df = pd.read_sql("SELECT username, password, total_points FROM users", db_conn)
                st.dataframe(u_df)
                u_rst = st.selectbox("Restore TC for", u_df['username'])
                if st.button("Reset Chip"):
                    db_conn.execute("UPDATE users SET tc_available=1 WHERE username=?", (u_rst,))
                    db_conn.commit()
                if st.button("NEW ROUND"):
                    db_conn.execute("UPDATE game_state SET current_round='Round 2' WHERE id=1")
                    db_conn.commit()
