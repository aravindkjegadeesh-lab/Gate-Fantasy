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
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, team TEXT, total_points REAL DEFAULT 0)''')
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
# Create a dictionary for easy price lookup
price_dict = {row['name']: row['price'] for _, row in df_market.iterrows()}
# Create formatted labels: "Player Name (£Price)"
player_options = [f"{p['name']} (£{p['price']}m)" for p in MARKET_DATA]

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
        if st.button("Log In"): login(u_log, p_log)
    with tab2:
        u_sign = st.text_input("Choose Username", key="sign_u")
        p_sign = st.text_input("Choose Password", type="password", key="sign_p")
        if st.button("Sign Up"): signup(u_sign, p_sign)
else:
    st.sidebar.markdown(f"Manager: **{st.session_state.username}**")
    page = st.sidebar.radio("Go to:", ["Dashboard", "My Squad", "Leaderboard", "Admin Panel"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.markdown('<div class="fpl-header"><h1 style="color:#00ff87; margin:0;">GATE FANTASY</h1></div>', unsafe_allow_html=True)
        st.subheader(f"Welcome back, {st.session_state.username}!")
        st.info("Assemble your squad of 5 students to start earning points.")

    elif page == "My Squad":
        st.header("🏃 Manage Your Squad")
        st.write("Pick 5 players. Budget: **£90m**")
        
        # User picks from formatted labels
        selected_display = st.multiselect("Select Players", player_options, max_selections=5)
        
        # Extract just the names from the display strings
        selected_names = [s.split(" (£")[0] for s in selected_display]
        
        if selected_names:
            current_cost = sum([price_dict[name] for name in selected_names])
            st.metric("Budget Remaining", f"£{90-current_cost:.1f}m")
            
            if len(selected_names) == 5 and current_cost <= 90:
                if st.button("Save Team"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE users SET team=? WHERE username=?", (",".join(selected_names), st.session_state.username))
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
            conn = get_connection()
            all_users = pd.read_sql("SELECT username, password, team FROM users", conn)
            
            st.write("### 👥 Participant List")
            st.dataframe(all_users, use_container_width=True)
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 🛠️ Account Recovery")
                user_to_fix = st.selectbox("Select Manager to Reset", all_users['username'])
                new_pw = st.text_input("New Password")
                if st.button("Reset Password"):
                    c = conn.cursor()
                    c.execute("UPDATE users SET password=? WHERE username=?", (new_pw, user_to_fix))
                    conn.commit()
                    st.toast(f"Password reset for {user_to_fix}")

            with col2:
                st.write("### 🗑️ Remove Participant")
                user_to_del = st.selectbox("Select Manager to Delete", all_users['username'], key="del_user")
                if st.button("DELETE ACCOUNT", help="Warning: This is permanent!"):
                    c = conn.cursor()
                    c.execute("DELETE FROM users WHERE username=?", (user_to_del,))
                    conn.commit()
                    st.warning(f"Account for {user_to_del} has been deleted.")
                    st.rerun()
