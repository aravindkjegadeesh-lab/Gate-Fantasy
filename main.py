import streamlit as st
import pandas as pd
import sqlite3

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP ---
def get_connection():
    return sqlite3.connect('fantasy.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
    # Game State table (for Round and Deadline)
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT)''')
    # Initialize game state if empty
    c.execute("SELECT COUNT(*) FROM game_state")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO game_state (id, current_round, deadline) VALUES (1, 'Round 1', 'Not Set')")
    conn.commit()

init_db()

# --- LIGHT THEME STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1c1e21; }
    p, h1, h2, h3, h4, span, label { color: #38003c !important; font-weight: 600; }
    .fpl-header {
        background: #38003c;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 5px solid #00ff87;
        text-align: center;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #00ff87 !important;
        color: #38003c !important;
        font-weight: bold !important;
        border: 2px solid #38003c !important;
        border-radius: 8px !important;
    }
    .stDataFrame { background-color: white; border-radius: 10px; }
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
df_market = pd.DataFrame(MARKET_DATA)
price_dict = {row['name']: row['price'] for _, row in df_market.iterrows()}
player_options = [f"{p['name']} (£{p['price']}m)" for p in MARKET_DATA]

# --- HELPER FUNCTIONS ---
def get_game_info():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM game_state WHERE id=1", conn).iloc[0]

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# --- AUTH LOGIC ---
def login(u, p):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    if c.fetchone():
        st.session_state.authenticated = True
        st.session_state.username = u
        st.rerun()
    else:
        st.error("❌ Incorrect username or password.")

def signup(u, p):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, total_points, team) VALUES (?, ?, 0, 'No Team')", (u, p))
        conn.commit()
        st.success("✅ Account created! Please log in.")
    except sqlite3.IntegrityError:
        st.error("⚠️ Username taken.")

# --- APP FLOW ---
if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    with tab1:
        u_log = st.text_input("Username")
        p_log = st.text_input("Password", type="password")
        if st.button("Log In"): login(u_log, p_log)
    with tab2:
        u_sign = st.text_input("Choose Username")
        p_sign = st.text_input("Choose Password", type="password")
        if st.button("Sign Up"): signup(u_sign, p_sign)
else:
    info = get_game_info()
    st.sidebar.markdown(f"**{info['current_round']}**")
    st.sidebar.markdown(f"Deadline: `{info['deadline']}`")
    st.sidebar.divider()
    page = st.sidebar.radio("Menu", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.subheader(f"Hello, Manager {st.session_state.username}!")
        
        col1, col2 = st.columns(2)
        col1.metric("Current Round", info['current_round'])
        col2.metric("Deadline", info['deadline'])
        
        st.write("---")
        st.info("Make sure your squad is locked in before the deadline!")

    elif page == "My Squad":
        st.header("🏃 Team Selection")
        selected_display = st.multiselect("Pick 5 Players", player_options, max_selections=5)
        selected_names = [s.split(" (£")[0] for s in selected_display]
        
        if selected_names:
            cost = sum([price_dict[name] for name in selected_names])
            st.metric("Budget Remaining", f"£{90-cost:.1f}m")
            if len(selected_names) == 5 and cost <= 90:
                if st.button("Save Team"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE users SET team=? WHERE username=?", (", ".join(selected_names), st.session_state.username))
                    conn.commit()
                    st.success("✅ Team Saved!")

    elif page == "Leaderboard":
        st.header("🏆 Leaderboard & Rival Teams")
        conn = get_connection()
        # Showing the Team column so everyone can see the rival squads
        lb_df = pd.read_sql("SELECT username as Manager, total_points as Points, team as Squad FROM users ORDER BY total_points DESC", conn)
        st.dataframe(lb_df, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        st.header("🔑 Admin Control Room")
        admin_pass = st.text_input("Admin Key", type="password")
        if admin_pass == "gate2026":
            t1, t2, t3 = st.tabs(["Game Status", "User Management", "Delete Users"])
            
            with t1:
                st.write("### 📅 Set Round & Deadline")
                new_round = st.text_input("Set Round Name", value=info['current_round'])
                new_date = st.text_input("Set Deadline (e.g. Sunday 6pm)", value=info['deadline'])
                if st.button("Update Game Status"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE game_state SET current_round=?, deadline=? WHERE id=1", (new_round, new_date))
                    conn.commit()
                    st.success("Round Info Updated!")
                    st.rerun()

            with t2:
                st.write("### 👥 All Participants")
                conn = get_connection()
                all_u = pd.read_sql("SELECT username, password, total_points FROM users", conn)
                st.dataframe(all_u, use_container_width=True)

            with t3:
                st.write("### 🗑️ Remove Manager")
                user_del = st.selectbox("Select User", all_u['username'])
                if st.button("DELETE PERMANENTLY"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM users WHERE username=?", (user_del,))
                    conn.commit()
                    st.warning(f"Deleted {user_del}")
                    st.rerun()
