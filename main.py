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
    
    # Ensure columns exist (Migration)
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
    .stButton>button { background-color: #00ff87 !important; color: #38003c !important; font-weight: bold !important; border-radius: 8px !important; width: 100%; }
    .stDataFrame { border: 1px solid #38003c; border-radius: 10px; }
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

# --- AUTH FLOW ---
if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    auth_tabs = st.tabs(["Login", "Create Account"])
    with auth_tabs[0]:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            res = db_conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.authenticated = True
                st.session_state.username = u
                st.rerun()
            else: st.error("Invalid credentials.")
    with auth_tabs[1]:
        nu = st.text_input("Choose Username")
        np = st.text_input("Choose Password", type="password")
        if st.button("Sign Up"):
            try:
                db_conn.execute("INSERT INTO users (username, password, team, captain) VALUES (?, ?, 'None', 'None')", (nu, np))
                db_conn.commit()
                st.success("Account created successfully!")
            except: st.error("Username already exists.")
else:
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    page = st.sidebar.radio("Navigation", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.subheader(f"Manager Dashboard: {st.session_state.username}")
        c1, c2 = st.columns(2)
        c1.metric("Current Round", info['current_round'])
        c2.metric("Deadline", info['deadline'])
        st.info(f"Active Subjects this round: **{info['subjects']}**")

    elif page == "My Squad":
        st.header("🏃 Manage Your Team")
        user_row = pd.read_sql("SELECT * FROM users WHERE username=?", db_conn, params=(st.session_state.username,)).iloc[0]
        
        selected_display = st.multiselect("Select 5 Students (£90m Budget)", player_options, max_selections=5)
        selected_names = [s.split(" (£")[0] for s in selected_display]
        
        if len(selected_names) == 5:
            cap = st.selectbox("Select Captain (2x Points)", selected_names)
            
            if user_row['tc_available'] == 1:
                tc_active = st.checkbox("🚀 ACTIVATE TRIPLE CAPTAIN (3x Points - ONCE PER SEASON)")
            else:
                st.warning("Triple Captain chip has been used.")
                tc_active = False

            if st.button("Lock In Team"):
                db_conn.execute("UPDATE users SET team=?, captain=?, tc_active=? WHERE username=?", 
                                (", ".join(selected_names), cap, 1 if tc_active else 0, st.session_state.username))
                db_conn.commit()
                st.success("Team saved successfully!")

    elif page == "Leaderboard":
        st.header("🏆 Global Leaderboard")
        # Fetching fresh data to ensure leaderboard is always accurate
        lb_query = "SELECT username as Manager, total_points as Points, team as Squad, captain as Captain FROM users ORDER BY total_points DESC"
        lb_df = pd.read_sql(lb_query, db_conn)
        st.dataframe(lb_df, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        admin_key = st.text_input("Enter Admin Key", type="password")
        if admin_key == "gate2026":
            st.success("Admin access granted.")
            t1, t2, t3 = st.tabs(["Round Setup", "Subject Scoring", "User Management"])
            
            with t1:
                st.write("### Round & Subject Config")
                new_r = st.text_input("Round Name", value=info['current_round'])
                new_d = st.text_input("Deadline Info", value=info['deadline'])
                # Subject picker for the ROUND
                subs_list = ["Maths", "English", "HASS", "Science", "Music", "Languages"]
                active_subs = st.multiselect("Active Subjects for this Round", subs_list, 
                                           default=info['subjects'].split(", ") if info['subjects'] != "None" else None)
                if st.button("Update Round"):
                    db_conn.execute("UPDATE game_state SET current_round=?, deadline=?, subjects=? WHERE id=1", 
                                    (new_r, new_d, ", ".join(active_subs) if active_subs else "None"))
                    db_conn.commit()
                    st.rerun()

            with t2:
                st.write("### Add Student Marks")
                # Specific subject selector for adding marks
                scoring_sub = st.selectbox("Which subject are you adding marks for?", subs_list)
                student = st.selectbox("Select Student", player_names)
                mark = st.number_input(f"Enter {student}'s {scoring_sub} Mark", 0.0, 100.0)
                
                points_to_award = calculate_fpl_points(mark)
                st.write(f"Calculated Base Points: **{points_to_award}**")
                
                if st.button(f"Submit {scoring_sub} Score"):
                    c = db_conn.cursor()
                    managers = c.execute("SELECT username, team, captain, tc_active FROM users").fetchall()
                    for m_name, m_team, m_cap, m_tc_active in managers:
                        if m_team and student in m_team:
                            multiplier = 1
                            if student == m_cap:
                                multiplier = 3 if m_tc_active else 2
                            
                            final_award = points_to_award * multiplier
                            c.execute("UPDATE users SET total_points = total_points + ? WHERE username=?", (final_award, m_name))
                            
                            if m_tc_active:
                                c.execute("UPDATE users SET tc_available=0, tc_active=0 WHERE username=?", (m_name,))
                    db_conn.commit()
                    st.success(f"Distributed points for {student} in {scoring_sub}!")

            with t3:
                st.write("### Manager Database")
                user_list = pd.read_sql("SELECT username, password, tc_available as TC_Left, total_points FROM users", db_conn)
                st.dataframe(user_list, use_container_width=True)
                
                target_user = st.selectbox("Select Manager to Delete", user_list['username'])
                if st.button("DELETE MANAGER"):
                    db_conn.execute("DELETE FROM users WHERE username=?", (target_user,))
                    db_conn.commit()
                    st.warning(f"User {target_user} removed.")
                    st.rerun()
