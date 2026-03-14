import streamlit as st
import pandas as pd
import sqlite3

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy", page_icon="⚽", layout="centered")

# --- DATABASE SETUP ---
# Using a function to ensure the connection stays alive
def get_connection():
    return sqlite3.connect('fantasy.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
    conn.commit()

init_db()

# --- LIGHT THEME STYLING ---
st.markdown("""
    <style>
    /* Background and text */
    .stApp { background-color: #FFFFFF; color: #1c1e21; }
    
    /* Global Text Color Fix */
    p, h1, h2, h3, h4, span, label { color: #38003c !important; }

    /* FPL Header */
    .fpl-header {
        background: #38003c;
        padding: 20px;
        border-radius: 10px;
        border-bottom: 5px solid #00ff87;
        text-align: center;
        margin-bottom: 25px;
    }

    /* Buttons */
    .stButton>button {
        background-color: #00ff87 !important;
        color: #38003c !important;
        font-weight: bold !important;
        border: 2px solid #38003c !important;
        border-radius: 8px !important;
        width: 100%;
    }

    /* Input Fields */
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

# --- SESSION STATE MANAGEMENT ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# --- AUTH FUNCTIONS ---
def login(u, p):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = c.fetchone()
    if user:
        st.session_state.authenticated = True
        st.session_state.username = u
        st.rerun()
    else:
        st.error("❌ Incorrect username or password.")

def signup(u, p):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, total_points) VALUES (?, ?, 0)", (u, p))
        conn.commit()
        st.success("✅ Account created! Please log in.")
    except sqlite3.IntegrityError:
        st.error("⚠️ That username is already taken.")

# --- APP FLOW ---
if not st.session_state.authenticated:
    st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u_log = st.text_input("Username", key="login_u")
        p_log = st.text_input("Password", type="password", key="login_p")
        if st.button("Log In"):
            login(u_log, p_log)
            
    with tab2:
        u_sign = st.text_input("Choose Username", key="sign_u")
        p_sign = st.text_input("Choose Password", type="password", key="sign_p")
        if st.button("Sign Up"):
            signup(u_sign, p_sign)

else:
    # Sidebar Nav
    st.sidebar.markdown(f"Manager: **{st.session_state.username}**")
    page = st.sidebar.radio("Go to:", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    # --- PAGES ---
    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.subheader(f"Welcome back, {st.session_state.username}!")
        st.info("The season is live. Head to 'My Squad' to build your 5-man team.")

    elif page == "My Squad":
        st.header("🏃 Manage Your Squad")
        st.write("Pick 5 players. Budget: **£90m**")
        
        selected = st.multiselect("Select Players", df_market['name'], max_selections=5)
        
        if selected:
            current_cost = df_market[df_market['name'].isin(selected)]['price'].sum()
            st.metric("Budget Remaining", f"£{90-current_cost:.1f}m")
            
            if len(selected) == 5 and current_cost <= 90:
                if st.button("Save Team"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE users SET team=? WHERE username=?", (",".join(selected), st.session_state.username))
                    conn.commit()
                    st.success("✅ Team Locked In!")
            elif current_cost > 90:
                st.error("🚨 Over Budget!")

    elif page == "Leaderboard":
        st.header("🏆 Global Standings")
        conn = get_connection()
        lb_df = pd.read_sql("SELECT username as Manager, total_points as Points FROM users ORDER BY total_points DESC", conn)
        st.dataframe(lb_df, use_container_width=True, hide_index=True)

    elif page == "Admin Panel":
        st.header("🔑 Admin Control Room")
        admin_pass = st.text_input("Enter Admin Secret Key", type="password")
        
        if admin_pass == "gate2026":
            st.success("Access Granted.")
            
            # User Management
            st.write("### 👥 Participant List")
            conn = get_connection()
            all_users = pd.read_sql("SELECT username, password, team FROM users", conn)
            st.dataframe(all_users, use_container_width=True)
            
            st.divider()
            st.write("### 🛠️ Account Recovery")
            user_to_fix = st.selectbox("Select Manager to Reset", all_users['username'])
            new_pw = st.text_input("New Password")
            if st.button("Reset Password"):
                c = conn.cursor()
                c.execute("UPDATE users SET password=? WHERE username=?", (new_pw, user_to_fix))
                conn.commit()
                st.toast(f"Password updated for {user_to_fix}")

            st.divider()
            st.write("### 📅 Gameweek Control")
            st.multiselect("Active Subjects", ["Maths", "English", "HASS", "Science"])
            if st.button("Launch New Gameweek"):
                st.success("Round started!")
