import streamlit as st
import pandas as pd
import sqlite3
import math

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('fantasy.db', check_same_thread=False)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
    # Gameweek config table
    c.execute('''CREATE TABLE IF NOT EXISTS config 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    return conn

conn = init_db()

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

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; }
    .fpl-header { background: linear-gradient(90deg, #38003c 0%, #7a00ff 100%); padding: 20px; border-radius: 10px; border-bottom: 4px solid #00ff87; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTH LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def login_user(u, p):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    return c.fetchone()

def signup_user(u, p):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
        return True
    except:
        return False

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚽ Gate Fantasy")

if not st.session_state.logged_in:
    page = st.sidebar.radio("Entry", ["Login", "Sign Up"])
else:
    page = st.sidebar.radio("Navigation", ["Home", "Build Team", "Leaderboard", "Admin Portal"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- PAGES ---
if not st.session_state.logged_in:
    if page == "Login":
        st.header("Login to Gate Fantasy")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = login_user(u, p)
            if res:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    elif page == "Sign Up":
        st.header("Create Account")
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if signup_user(new_u, new_p):
                st.success("Account created! Go to Login.")
            else:
                st.error("Username already exists.")

else:
    if page == "Home":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.write(f"### Welcome back, Manager **{st.session_state.user}**!")
        
    elif page == "Build Team":
        st.title("🏃 Build Your Squad")
        selected = st.multiselect("Pick 5 Players (£90m Budget)", df_market['name'], max_selections=5)
        
        if selected:
            cost = df_market[df_market['name'].isin(selected)]['price'].sum()
            st.metric("Remaining Budget", f"£{90-cost:.1f}m")
            if len(selected) == 5 and cost <= 90:
                if st.button("Save Team"):
                    c = conn.cursor()
                    c.execute("UPDATE users SET team=? WHERE username=?", (",".join(selected), st.session_state.user))
                    conn.commit()
                    st.success("Team Saved!")

    elif page == "Leaderboard":
        st.title("🏆 Leaderboard")
        lb_df = pd.read_sql("SELECT username, total_points FROM users ORDER BY total_points DESC", conn)
        st.table(lb_df)

    elif page == "Admin Portal":
        st.title("🔑 Admin Control")
        admin_pw = st.text_input("Admin Key", type="password")
        if admin_pw == "gate2026":
            tab1, tab2 = st.tabs(["User Management", "Gameweek Settings"])
            
            with tab1:
                st.write("### All Registered Participants")
                users_all = pd.read_sql("SELECT username, password FROM users", conn)
                st.dataframe(users_all)
                
                target_user = st.selectbox("Select user to reset password", users_all['username'])
                new_pass = st.text_input("New Password for user")
                if st.button("Update Password"):
                    c = conn.cursor()
                    c.execute("UPDATE users SET password=? WHERE username=?", (new_pass, target_user))
                    conn.commit()
                    st.success(f"Password for {target_user} updated!")

            with tab2:
                st.write("### Configure Round")
                subjects = st.multiselect("Which subjects count this week?", ["Maths", "English", "HASS", "Science"])
                if st.button("Set Round"):
                    st.success(f"Round updated with {subjects}")
