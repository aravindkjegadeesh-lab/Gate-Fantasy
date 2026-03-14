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
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, captain TEXT, 
                  tc_available INTEGER DEFAULT 1, tc_active INTEGER DEFAULT 0, total_points REAL DEFAULT 0)''')
    # Game State table
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT, subjects TEXT)''')
    
    # Check for missing columns (Migration)
    c.execute("PRAGMA table_info(game_state)")
    cols = [col[1] for col in c.fetchall()]
    if 'subjects' not in cols:
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
    p, h1, h2, h3, h4, span, label { color: #38003c !important; font-weight: 600; }
    .fpl-header { background: #38003c; padding: 20px; border-radius: 10px; border-bottom: 5px solid #00ff87; text-align: center; margin-bottom: 25px; }
    .stButton>button { background-color: #00ff87 !important; color: #38003c !important; font-weight: bold !important; border-radius: 8px !important; }
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
    {"name": "Josh", "price": 19.0}, {"name": "Daren", "price": 17.5}, {"name": "Aravind", "price": 17.0}, 
    {"name": "Alfie", "price": 16.0}, {"name": "Musa", "price": 15.0}, {"name": "Maxwell", "price": 14.0}, 
    {"name": "Andre", "price": 14.0}, {"name": "Inesh", "price": 14.0}, {"name": "Maximus", "price": 13.0}, 
    {"name": "Jared", "price": 13.0}, {"name": "Lucas Lau", "price": 12.0}, {"name": "Alden", "price": 11.0}, 
    {"name": "Sanjit", "price": 10.5}, {"name": "Yashwant", "price": 10.5}, {"name": "Maxi", "price": 10.0}, 
    {"name": "Raymond", "price": 9.5}, {"name": "Hassan", "price": 9.0}, {"name": "Lucas Kong", "price": 8.0}
]
player_names = [p['name'] for p in MARKET_DATA]
player_options = [f"{p['name']} (£{p['price']}m)" for p in MARKET_DATA]

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# --- AUTH ---
if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["Login", "Create Account"])
    with tabs[0]:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.authenticated = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Wrong credentials")
    with tabs[1]:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Account created!")
            except: st.error("Username already exists")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Navigation", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.metric("Current Round", info['current_round'])
        st.info(f"Active Subjects: **{info['subjects']}**")
        st.write(f"Deadline: `{info['deadline']}`")

    elif page == "My Squad":
        st.header("🏃 Manage Squad")
        user = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.username,)).iloc[0]
        
        selected_display = st.multiselect("Pick 5 Players (£90m Budget)", player_options, max_selections=5)
        selected_names = [s.split(" (£")[0] for s in selected_display]
        
        if len(selected_names) == 5:
            cap = st.selectbox("Select Captain (2x Points)", selected_names)
            
            if user['tc_available'] == 1:
                tc_active = st.checkbox("🚀 ACTIVATE TRIPLE CAPTAIN (3x Points - ONCE PER SEASON)")
            else:
                st.warning("Triple Captain: Already Used")
                tc_active = False

            if st.button("Save Team"):
                db_conn.execute("UPDATE users SET team=?, captain=?, tc_active=? WHERE username=?", 
                                (", ".join(selected_names), cap, 1 if tc_active else 0, st.session_state.username))
                db_conn.commit()
                st.success("Squad Locked!")

    elif page == "Leaderboard":
        st.header("🏆 Standings")
        lb = pd.read_sql("SELECT username as Manager, total_points as Points, team as Squad, captain as Captain FROM users ORDER BY total_points DESC", db_conn)
        st.dataframe(lb, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        pw = st.text_input("Admin Key", type="password")
        if pw == "gate2026":
            st.success("Admin Access Granted")
            t1, t2, t3 = st.tabs(["Round & Subjects", "Point Scoring", "User Management"])
            
            with t1:
                st.write("### Set Game State")
                nr = st.text_input("Round Name", value=info['current_round'])
                nd = st.text_input("Deadline", value=info['deadline'])
                ns = st.multiselect("Active Subjects", ["Maths", "English", "HASS", "Science", "Music"], 
                                   default=info['subjects'].split(", ") if info['subjects'] != "None" else None)
                if st.button("Update Round"):
                    db_conn.execute("UPDATE game_state SET current_round=?, deadline=?, subjects=? WHERE id=1", 
                                    (nr, nd, ", ".join(ns) if ns else "None"))
                    db_conn.commit()
                    st.rerun()

            with t2:
                st.write("### Award Points")
                st.info(f"Current Scoring Subject(s): {info['subjects']}")
                student = st.selectbox("Select Student", player_names)
                mark = st.number_input("Enter Student Mark", 0.0, 100.0)
                pts = calculate_fpl_points(mark)
                st.write(f"Base Points: **{pts}**")
                
                if st.button("Distribute Points to Managers"):
                    c = db_conn.cursor()
                    all_m = c.execute("SELECT username, team, captain, tc_active FROM users").fetchall()
                    for m_name, m_team, m_cap, m_tc_active in all_m:
                        if m_team and student in m_team:
                            mult = 1
                            if student == m_cap:
                                mult = 3 if m_tc_active else 2
                            
                            earned = pts * mult
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (earned, m_name))
                            
                            if m_tc_active:
                                c.execute("UPDATE users SET tc_available=0, tc_active=0 WHERE username=?", (m_name,))
                    db_conn.commit()
                    st.success(f"Added {pts} (multiplied) points for {student} to all relevant teams!")

            with t3:
                st.write("### Manage Participants")
                all_users = pd.read_sql("SELECT username, password, tc_available FROM users", db_conn)
                st.dataframe(all_users, use_container_width=True)
                
                u_del = st.selectbox("Select User to Remove", all_users['username'])
                if st.button("DELETE USER PERMANENTLY"):
                    db_conn.execute("DELETE FROM users WHERE username=?", (u_del,))
                    db_conn.commit()
                    st.warning(f"Deleted {u_del}")
                    st.rerun()
