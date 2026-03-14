import streamlit as st
import pandas as pd
import sqlite3

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP (Fixed for Stability) ---
def init_db():
    # 'check_same_thread=False' is vital for Streamlit to prevent crashes
    conn = sqlite3.connect('fantasy.db', check_same_thread=False)
    c = conn.cursor()
    # Ensure tables exist
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_state 
                 (id INTEGER PRIMARY KEY, current_round TEXT, deadline TEXT, subjects TEXT)''')
    
    # Check if game_state has data, if not, insert default
    c.execute("SELECT COUNT(*) FROM game_state")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO game_state (id, current_round, deadline, subjects) VALUES (1, 'Round 1', 'Not Set', 'None')")
    conn.commit()
    return conn

# Global connection object
db_conn = init_db()

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
    input { color: black !important; background-color: #f0f2f5 !important; }
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

# --- SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# --- AUTH FUNCTIONS ---
def login(u, p):
    c = db_conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    if c.fetchone():
        st.session_state.authenticated = True
        st.session_state.username = u
        st.rerun()
    else:
        st.error("❌ Incorrect username or password.")

def signup(u, p):
    c = db_conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, total_points, team) VALUES (?, ?, 0, 'No Team Set')", (u, p))
        db_conn.commit()
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
    # Get game info every page load
    info = pd.read_sql("SELECT * FROM game_state WHERE id=1", db_conn).iloc[0]
    
    st.sidebar.markdown(f"**{info['current_round']}**")
    st.sidebar.markdown(f"Deadline: `{info['deadline']}`")
    st.sidebar.divider()
    page = st.sidebar.radio("Menu", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.subheader(f"Welcome, Manager {st.session_state.username}!")
        c1, c2, c3 = st.columns(3)
        c1.metric("Round", info['current_round'])
        c2.metric("Deadline", info['deadline'])
        c3.metric("Subjects", info['subjects'])
        st.write("---")
        st.info(f"Points this round will be calculated based on: **{info['subjects']}**.")

    elif page == "My Squad":
        st.header("🏃 Team Selection")
        st.write(f"Active Subjects: **{info['subjects']}**")
        selected_display = st.multiselect("Pick 5 Players (£90m Budget)", player_options, max_selections=5)
        selected_names = [s.split(" (£")[0] for s in selected_display]
        
        if selected_names:
            cost = sum([price_dict[name] for name in selected_names])
            st.metric("Budget Remaining", f"£{90-cost:.1f}m")
            if len(selected_names) == 5 and cost <= 90:
                if st.button("Save Team"):
                    c = db_conn.cursor()
                    c.execute("UPDATE users SET team=? WHERE username=?", (", ".join(selected_names), st.session_state.username))
                    db_conn.commit()
                    st.success("✅ Team Saved!")
            elif cost > 90:
                st.error("🚨 Over budget!")

    elif page == "Leaderboard":
        st.header("🏆 Leaderboard")
        lb_df = pd.read_sql("SELECT username as Manager, total_points as Points, team as Squad FROM users ORDER BY total_points DESC", db_conn)
        st.dataframe(lb_df, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        st.header("🔑 Admin Control")
        admin_pass = st.text_input("Admin Key", type="password")
        if admin_pass == "gate2026":
            t1, t2 = st.tabs(["Game Control", "User Management"])
            with t1:
                new_round = st.text_input("Round Name", value=info['current_round'])
                new_date = st.text_input("Deadline", value=info['deadline'])
                new_subs = st.multiselect("Active Subjects", ["Maths", "English", "HASS", "Science", "Music"], 
                                         default=info['subjects'].split(", ") if info['subjects'] != "None" else None)
                if st.button("Update Round Info"):
                    subs_str = ", ".join(new_subs) if new_subs else "None"
                    c = db_conn.cursor()
                    c.execute("UPDATE game_state SET current_round=?, deadline=?, subjects=? WHERE id=1", (new_round, new_date, subs_str))
                    db_conn.commit()
                    st.success("Round Updated!")
                    st.rerun()
            with t2:
                all_u = pd.read_sql("SELECT username, password, team FROM users", db_conn)
                st.dataframe(all_u, use_container_width=True)
                user_del = st.selectbox("Select User to Remove", all_u['username'])
                if st.button("Delete Account"):
                    c = db_conn.cursor()
                    c.execute("DELETE FROM users WHERE username=?", (user_del,))
                    db_conn.commit()
                    st.warning(f"Deleted {user_del}")
                    st.rerun()
