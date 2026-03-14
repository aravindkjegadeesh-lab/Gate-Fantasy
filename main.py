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
    # Users: tc_available tracks if they have the chip, tc_active tracks if they are using it THIS round
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, captain TEXT, 
                  tc_available INTEGER DEFAULT 1, tc_active INTEGER DEFAULT 0, total_points REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT, subjects TEXT)''')
    
    # Check for table updates (migration)
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    if 'tc_available' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN tc_available INTEGER DEFAULT 1")
    if 'tc_active' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN tc_active INTEGER DEFAULT 0")

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
    .stApp { background-color: #FFFFFF; }
    p, h1, h2, h3, h4, span, label { color: #38003c !important; font-weight: 600; }
    .fpl-header { background: #38003c; padding: 20px; border-radius: 10px; border-bottom: 5px solid #00ff87; text-align: center; margin-bottom: 25px; }
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

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# --- AUTH ---
if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["Login", "Sign Up"])
    with tabs[0]:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.authenticated = True
                st.session_state.username = u
                st.rerun()
    with tabs[1]:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Success!")
            except: st.error("Error")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Navigation", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    
    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.metric("Round", info['current_round'])
        st.info(f"Scoring Subjects: {info['subjects']}")

    elif page == "My Squad":
        st.header("🏃 Manage Squad")
        user = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.username,)).iloc[0]
        
        selected = st.multiselect("Pick 5 Players", player_names, max_selections=5, default=user['team'].split(", ") if user['team'] != "None" else None)
        
        if len(selected) == 5:
            cap = st.selectbox("Select Captain", selected, index=selected.index(user['captain']) if user['captain'] in selected else 0)
            
            # CHIP LOGIC: Check if tc_available is 1
            if user['tc_available'] == 1:
                tc_check = st.checkbox("🚀 USE TRIPLE CAPTAIN (3x Points - ONLY ONCE PER SEASON)")
            else:
                st.warning("✅ Triple Captain chip has already been used.")
                tc_check = False
            
            if st.button("Save Selection"):
                db_conn.execute("UPDATE users SET team=?, captain=?, tc_active=? WHERE username=?", 
                                (", ".join(selected), cap, 1 if tc_check else 0, st.session_state.username))
                db_conn.commit()
                st.success("Squad Locked!")

    elif page == "Leaderboard":
        st.header("🏆 Standings")
        lb = pd.read_sql("SELECT username as Manager, total_points as Points, team as Squad, captain as Captain FROM users ORDER BY total_points DESC", db_conn)
        st.dataframe(lb, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        pw = st.text_input("Admin Key", type="password")
        if pw == "gate2026":
            t1, t2 = st.tabs(["Control", "Enter Marks"])
            with t1:
                st.write("### Game Control")
                nr = st.text_input("Round Name", value=info['current_round'])
                ns = st.text_input("Subjects", value=info['subjects'])
                if st.button("Update Round"):
                    db_conn.execute("UPDATE game_state SET current_round=?, subjects=? WHERE id=1", (nr, ns))
                    db_conn.commit()
                    st.rerun()

            with t2:
                st.write("### Calculate & Add Points")
                student = st.selectbox("Student", player_names)
                mark = st.number_input("Mark (out of 100)", 0.0, 100.0)
                points = calculate_fpl_points(mark)
                st.write(f"Points to award: **{points}**")
                
                if st.button("Add Points to All Teams"):
                    c = db_conn.cursor()
                    managers = c.execute("SELECT username, team, captain, tc_active FROM users").fetchall()
                    for m_name, m_team, m_cap, m_tc_active in managers:
                        if student in m_team:
                            mult = 1
                            if student == m_cap:
                                mult = 3 if m_tc_active == 1 else 2
                            
                            earned = points * mult
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (earned, m_name))
                            
                            # CRITICAL: If they used TC, disable it permanently now
                            if m_tc_active == 1:
                                c.execute("UPDATE users SET tc_available = 0, tc_active = 0 WHERE username=?", (m_name,))
                    
                    db_conn.commit()
                    st.success(f"Scores processed for {student}!")
