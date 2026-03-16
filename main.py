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
                 (id INTEGER PRIMARY KEY, current_round TEXT, prev_round TEXT, deadline TEXT, subjects TEXT, prev_subjects TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS score_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, round_name TEXT, student TEXT, subject TEXT, mark REAL, points REAL, timestamp TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

# SCORING LOGIC
def calculate_fpl_points(mark):
    diff = mark - 70
    if diff >= 0:
        return 4 * math.pow(diff, 1.2)
    else:
        return -4 * math.pow(abs(diff), 1.2)

# MARKET DATA
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

# --- STYLE ---
st.markdown("""<style>
    .stApp { background-color: #FFFFFF; }
    label, p, .stMarkdown { color: #000000 !important; font-weight: 700 !important; }
    input { color: #000000 !important; background-color: #fcfcfc !important; border: 2px solid #38003c !important; }
    .fpl-header { background: #38003c; padding: 20px; border-radius: 10px; border-bottom: 5px solid #00ff87; text-align: center; margin-bottom: 25px; }
    .card { background: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #38003c; margin-bottom: 10px; color: #38003c; }
    </style>""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = None
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False

# --- AUTH ---
if not st.session_state.auth:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        u_in, p_in = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Log In", type="primary"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u_in, p_in)).fetchone()
            if res:
                st.session_state.auth, st.session_state.user = True, u_in
                st.rerun()
    with t2:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("Register"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Registered!")
            except: st.error("User exists.")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Nav", ["Dashboard", "Leaderboard", "Grade Portal", "My Squad", "Admin"])
    
    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.metric("Current Round", info['current_round'])
        st.info(f"📍 Active Subjects: {info['subjects']}")
        hist = pd.read_sql("SELECT student, subject, mark, points FROM score_history ORDER BY id DESC LIMIT 5", db_conn)
        if not hist.empty: st.table(hist)

    elif page == "Leaderboard":
        st.header("🏆 Official Standings")
        st.dataframe(pd.read_sql("SELECT username as Manager, total_points as Points FROM users ORDER BY total_points DESC", db_conn), use_container_width=True, hide_index=True)

    elif page == "Grade Portal":
        st.header("📝 Subject Performance")
        raw = pd.read_sql("SELECT student, subject, mark FROM score_history", db_conn)
        if not raw.empty: st.dataframe(raw.pivot_table(index='student', columns='subject', values='mark').fillna("-"), use_container_width=True)

    elif page == "My Squad":
        user = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.user,)).iloc[0]
        st.write(f"Budget: £90m | Current Team: {user['team']}")
        sel = st.multiselect("Select 5 Players", player_options, max_selections=5)
        s_names = [s.split(" (£")[0] for s in sel]
        cost = sum(player_prices[n] for n in s_names)
        if st.button("Lock Squad") and cost <= 90 and len(s_names) == 5:
            db_conn.execute("UPDATE users SET team=? WHERE username=?", (", ".join(s_names), st.session_state.user))
            db_conn.commit()
            st.success("Squad Saved!")

    elif page == "Admin":
        st.header("🔐 Admin Controls")
        pw = st.text_input("Admin Key", type="password")
        if pw == "gate2026":
            t1, t2, t3 = st.tabs(["Set Round", "Apply/Edit Score", "Nuclear Reset"])
            
            with t1:
                nr = st.text_input("Round Name (e.g. Week 1)")
                ns = st.text_input("Active Exams (e.g. Maths Test, HASS Essay)")
                if st.button("Update Season State"):
                    db_conn.execute("UPDATE game_state SET current_round=?, subjects=? WHERE id=1", (nr, ns))
                    db_conn.commit()
                    st.rerun()

            with t2:
                st.write("If you select a Student/Subject combo that already exists, it will **overwrite** the old score.")
                st_n = st.selectbox("Student", [p['name'] for p in MARKET_DATA])
                sub_n = st.selectbox("Subject/Exam", [s.strip() for s in info['subjects'].split(",")])
                mk = st.number_input("Mark", 0.0, 100.0)
                
                if st.button("Apply Score"):
                    new_pts = calculate_fpl_points(mk)
                    
                    # UNDO LOGIC: Check if this combo exists
                    existing = db_conn.execute("SELECT points FROM score_history WHERE student=? AND subject=? AND round_name=?", (st_n, sub_n, info['current_round'])).fetchone()
                    
                    if existing:
                        old_pts = existing[0]
                        # Remove old points from everyone who had this player
                        c = db_conn.cursor()
                        for u_n, u_t, u_c, u_tc in c.execute("SELECT username, team, captain, tc_active FROM users").fetchall():
                            if u_t and st_n in u_t:
                                m = 3 if (st_n == u_c and u_tc) else (2 if st_n == u_c else 1)
                                c.execute("UPDATE users SET total_points = total_points - ? WHERE username=?", (old_pts * m, u_n))
                        db_conn.execute("DELETE FROM score_history WHERE student=? AND subject=? AND round_name=?", (st_n, sub_n, info['current_round']))
                    
                    # ADD NEW SCORE
                    db_conn.execute("INSERT INTO score_history (round_name, student, subject, mark, points) VALUES (?,?,?,?,?)", (info['current_round'], st_n, sub_n, mk, new_pts))
                    c = db_conn.cursor()
                    for u_n, u_t, u_c, u_tc in c.execute("SELECT username, team, captain, tc_active FROM users").fetchall():
                        if u_t and st_n in u_t:
                            m = 3 if (st_n == u_c and u_tc) else (2 if st_n == u_c else 1)
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (new_pts * m, u_n))
                    db_conn.commit()
                    st.success(f"Score updated for {st_n}!")

            with t3:
                st.warning("This will delete ALL score history and reset everyone to 0 points.")
                if st.button("⚠️ FULL RESET (WIPE EVERYTHING)"):
                    db_conn.execute("DELETE FROM score_history")
                    db_conn.execute("UPDATE users SET total_points = 0")
                    db_conn.commit()
                    st.rerun()
