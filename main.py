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
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT, subject TEXT, mark REAL, points REAL, timestamp TEXT)''')
    
    c.execute("PRAGMA table_info(game_state)")
    cols = [col[1] for col in c.fetchall()]
    if 'prev_round' not in cols: c.execute("ALTER TABLE game_state ADD COLUMN prev_round TEXT DEFAULT 'None'")
    if 'prev_subjects' not in cols: c.execute("ALTER TABLE game_state ADD COLUMN prev_subjects TEXT DEFAULT 'None'")
    
    c.execute("SELECT COUNT(*) FROM game_state")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO game_state (id, current_round, prev_round, deadline, subjects, prev_subjects) VALUES (1, 'Round 1', 'None', 'Not Set', 'None', 'None')")
    conn.commit()
    return conn

db_conn = init_db()

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

# --- STYLE ---
st.markdown("""<style>
    .stApp { background-color: #FFFFFF; }
    .fpl-header { background: #38003c; padding: 20px; border-radius: 10px; border-bottom: 5px solid #00ff87; text-align: center; margin-bottom: 25px; }
    .card { background: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #38003c; margin-bottom: 10px; color: #38003c; }
    </style>""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login", "Sign Up"])
    with t1:
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.button("Log In"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.auth, st.session_state.user = True, u
                st.rerun()
    with t2:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("Register"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Success!")
            except: st.error("User exists")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Nav", ["Dashboard", "Grade Portal", "Player Stats", "My Squad", "Review Teams", "Leaderboard", "Admin"])
    
    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.metric("Active Round", info['current_round'])
        st.write(f"**Subjects in Play:** {info['subjects']}")
        st.markdown("---")
        hist = pd.read_sql("SELECT student, subject, mark, points FROM score_history ORDER BY id DESC LIMIT 5", db_conn)
        if not hist.empty: st.table(hist)

    elif page == "Grade Portal":
        st.header("📝 Student Grade Portal")
        raw_marks = pd.read_sql("SELECT student, subject, mark FROM score_history", db_conn)
        if not raw_marks.empty:
            grade_chart = raw_marks.pivot_table(index='student', columns='subject', values='mark', aggfunc='last')
            active_list = [s.strip() for s in info['subjects'].split(",")]
            display_cols = [col for col in ["Maths", "English", "Science", "HASS"] if col in active_list and col in grade_chart.columns]
            if display_cols: st.dataframe(grade_chart[display_cols].fillna("-"), use_container_width=True)
            else: st.info("No marks for current subjects.")
        else: st.info("No marks recorded yet.")

    elif page == "Player Stats":
        st.header("📊 Student Stats")
        stats = pd.read_sql("SELECT student as Name, SUM(points) as Total_Points FROM score_history GROUP BY student ORDER BY Total_Points DESC", db_conn)
        st.dataframe(stats, use_container_width=True, hide_index=True)

    elif page == "My Squad":
        user = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.user,)).iloc[0]
        t1, t2 = st.tabs(["Pick Team", "My Team"])
        with t1:
            sel = st.multiselect("Select 5", player_options, max_selections=5)
            s_names = [s.split(" (£")[0] for s in sel]
            cost = sum(player_prices[n] for n in s_names)
            st.write(f"**Current Spending: £{cost}m / £90m**")
            if len(s_names) == 5 and cost <= 90:
                cap = st.selectbox("Captain", s_names)
                if st.button("Save Squad"):
                    db_conn.execute("UPDATE users SET team=?, captain=? WHERE username=?", (", ".join(s_names), cap, st.session_state.user))
                    db_conn.commit()
                    st.rerun()
        with t2:
            if user['team'] != "None":
                t_names = user['team'].split(", ")
                t_cost = sum(player_prices[p] for p in t_names)
                st.markdown(f"""<div class="card">
                    <b>Team:</b> {user["team"]}<br>
                    <b>Captain:</b> {user["captain"]}<br><br>
                    <b>Total Budget Used:</b> £{t_cost}m / £90m<br>
                    <b>Bank:</b> £{90 - t_cost}m
                    </div>""", unsafe_allow_html=True)
            else: st.info("Pick a team first!")

    elif page == "Review Teams":
        st.header("👀 Review Other Teams")
        others = pd.read_sql("SELECT username, team, captain FROM users WHERE team != 'None'", db_conn)
        if not others.empty:
            for idx, row in others.iterrows():
                t_names = row['team'].split(", ")
                t_cost = sum(player_prices[p] for p in t_names)
                with st.expander(f"Manager: {row['username']}"):
                    st.write(f"**Squad:** {row['team']}")
                    st.write(f"**Captain:** {row['captain']}")
                    st.write(f"**Value:** £{t_cost}m")
        else: st.info("No managers have locked their teams yet.")

    elif page == "Leaderboard":
        lb = pd.read_sql("SELECT username as Manager, total_points as Points FROM users ORDER BY total_points DESC", db_conn)
        st.dataframe(lb, use_container_width=True, hide_index=True)

    elif page == "Admin":
        if st.text_input("Admin Key", type="password") == "gate2026":
            t1, t2, t3 = st.tabs(["Add Round", "Scoring", "User Tools"])
            with t1:
                nr = st.text_input("New Round Name")
                ns = st.multiselect("Select Round Subjects", ["Maths", "English", "HASS", "Science", "Music"])
                if st.button("START ROUND"):
                    db_conn.execute("UPDATE game_state SET prev_round=current_round, prev_subjects=subjects, current_round=?, subjects=? WHERE id=1", (nr, ", ".join(ns)))
                    db_conn.commit()
                    st.success("New Round Active!")
                if st.button("⏪ UNDO"):
                    db_conn.execute("UPDATE game_state SET current_round=prev_round, subjects=prev_subjects WHERE id=1")
                    db_conn.commit()
                    st.rerun()
            with t2:
                sb, st_n = st.selectbox("Sub", ["Maths", "English", "HASS", "Science", "Music"]), st.selectbox("Student", [p['name'] for p in MARKET_DATA])
                mk = st.number_input("Mark", 0.0, 100.0)
                if st.button("Apply"):
                    pts = calculate_fpl_points(mk)
                    db_conn.execute("INSERT INTO score_history (student, subject, mark, points, timestamp) VALUES (?,?,?,?,?)", (st_n, sb, mk, pts, datetime.now().strftime("%H:%M")))
                    c = db_conn.cursor()
                    for m_n, m_t, m_c in c.execute("SELECT username, team, captain FROM users").fetchall():
                        if m_t and st_n in m_t:
                            mult = 2 if st_n == m_c else 1
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (pts * mult, m_n))
                    db_conn.commit()
                    st.success("Points Added!")
            with t3:
                u_df = pd.read_sql("SELECT username, total_points FROM users", db_conn)
                st.dataframe(u_df)
                if st.button("Reset Points"):
                    db_conn.execute("UPDATE users SET total_points = 0")
                    db_conn.commit()
                    st.rerun()
