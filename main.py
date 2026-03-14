import streamlit as st
import pandas as pd
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gate Fantasy League", page_icon="⚽", layout="centered")

# --- CUSTOM CSS FOR FPL LOOK ---
st.markdown("""
    <style>
    .main { background-color: #121212; }
    .stButton>button { background-color: #00ff87; color: #38003c; font-weight: bold; width: 100%; border-radius: 10px; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- PLAYER DATABASE ---
MARKET_DATA = [
    {"name": "Ming", "price": 36.0}, {"name": "Cirrus", "price": 35.5},
    {"name": "Gautham", "price": 33.0}, {"name": "Dev", "price": 32.5},
    {"name": "Forrest", "price": 30.0}, {"name": "Talal", "price": 28.5},
    {"name": "Geonhee", "price": 27.0}, {"name": "Hardy", "price": 23.0},
    {"name": "Ethan Yuen", "price": 22.5}, {"name": "Abdul", "price": 22.0},
    {"name": "Lucas Yiu", "price": 22.0}, {"name": "Adhvik", "price": 21.0},
    {"name": "Sid", "price": 20.0}, {"name": "Barnabas", "price": 20.0},
    {"name": "Komron", "price": 20.0}, {"name": "Michael", "price": 20.0},
    {"name": "Nathan", "price": 20.0}, {"name": "Ethan Wang", "price": 19.5},
    {"name": "Josh", "price": 19.0}, {"name": "Daren", "price": 17.5},
    {"name": "Aravind", "price": 17.0}, {"name": "Alfie", "price": 16.0},
    {"name": "Musa", "price": 15.0}, {"name": "Maxwell", "price": 14.0},
    {"name": "Andre", "price": 14.0}, {"name": "Inesh", "price": 14.0},
    {"name": "Maximus", "price": 13.0}, {"name": "Jared", "price": 13.0},
    {"name": "Lucas Lau", "price": 12.0}, {"name": "Alden", "price": 11.0},
    {"name": "Sanjit", "price": 10.5}, {"name": "Yashwant", "price": 10.5},
    {"name": "Maxi", "price": 10.0}, {"name": "Raymond", "price": 9.5},
    {"name": "Hassan", "price": 9.0}, {"name": "Lucas Kong", "price": 8.0}
]
df_market = pd.DataFrame(MARKET_DATA)

# --- LOGIC FUNCTIONS ---
def calc_pts(score, multiplier=1):
    base = score - 70
    if base > 0:
        p = math.pow(base, 1.2) * 4
    elif base < 0:
        p = -math.pow(abs(base), 1.2) * 4
    else:
        p = 0
    return round(p * multiplier, 1)

# --- APP NAVIGATION ---
st.sidebar.title("Gate Fantasy 25/26")
menu = ["🏠 Dashboard", "🏃 Build Team", "🏆 Leaderboard", "🔑 Admin Update"]
choice = st.sidebar.radio("Navigate", menu)

if choice == "🏠 Dashboard":
    st.title("⚽ Gate Fantasy Guide")
    st.write("Welcome to the official fantasy league for your grades.")
    name = st.text_input("Enter Manager Name to Login")
    if name:
        st.success(f"Welcome back, {name}! Ready for the next Gameweek?")
    
    st.markdown("### 📜 Quick Rules")
    st.write("- **Budget:** £90m for 5 players.")
    st.write("- **Formula:** `(Score - 70)^1.2 * 4`")
    st.write("- **Exam Week:** Points are doubled!")

elif choice == "🏃 Build Team":
    st.title("🏃 Pick Your Starting 5")
    
    selected_names = st.multiselect("Select exactly 5 players:", df_market['name'])
    
    if selected_names:
        selected_df = df_market[df_market['name'].isin(selected_names)]
        total_cost = selected_df['price'].sum()
        remaining = 90 - total_cost
        
        col1, col2 = st.columns(2)
        col1.metric("Budget Remaining", f"£{remaining:.1f}m", delta=remaining, delta_color="normal")
        col2.metric("Players Selected", f"{len(selected_names)}/5")

        if len(selected_names) == 5 and remaining >= 0:
            st.success("Squad Valid!")
            if st.button("Confirm & Save Team"):
                st.balloons()
                st.write("Team saved to the cloud! (Connect Google Sheets for persistence)")
        elif remaining < 0:
            st.error("Over Budget! Remove expensive players.")

elif choice == "🏆 Leaderboard":
    st.title("🏆 Global Standings")
    # Example data (In a real app, this pulls from a database)
    leader_df = pd.DataFrame({
        "Rank": [1, 2, 3],
        "Manager": ["Lucas Lau", "Geonhee", "Aravind"],
        "Total Points": [184.5, 162.1, 145.0]
    })
    st.dataframe(leader_df, hide_index=True, use_container_width=True)

elif choice == "🔑 Admin Update":
    st.title("🔑 Admin Control")
    password = st.text_input("Admin Password", type="password")
    
    if password == "gate2026":
        st.write("### Update Scores for Gameweek")
        st.info("Input results for Maths, HASS, and English for each student.")
        
        updates = []
        for i, row in df_market.iterrows():
            with st.expander(f"Scores for {row['name']}"):
                m = st.number_input(f"Maths ({row['name']})", 0.0, 100.0, 70.0, key=f"m_{i}")
                h = st.number_input(f"HASS ({row['name']})", 0.0, 100.0, 70.0, key=f"h_{i}")
                e = st.number_input(f"English ({row['name']})", 0.0, 100.0, 70.0, key=f"e_{i}")
                avg = (m + h + e) / 3
                st.write(f"GW Points: **{calc_pts(avg)}**")
        
        if st.button("Finalize Gameweek & Push to Leaderboard"):
            st.warning("Ensure all scores are correct before pushing.")