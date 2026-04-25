import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Aggressive Trading System Tracker")

FILE = "data.csv"

# --- Initialize ---
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "Day","Trade","Capital","Outcome",
        "TradeSize","ConsecLoss"
    ])
    df.to_csv(FILE, index=False)

df = pd.read_csv(FILE)

# --- Fix missing columns (safety) ---
required_cols = ["Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"]
for col in required_cols:
    if col not in df.columns:
        df[col] = 0

# --- Inputs ---
start_capital = st.number_input("Starting Capital", value=25000)

# --- Get Current State ---
if len(df) == 0:
    capital = start_capital
    day = 1
    consec_loss = 0
    trades_today = 0
else:
    capital = df.iloc[-1]["Capital"]
    day = int(df.iloc[-1]["Day"])
    consec_loss = int(df.iloc[-1]["ConsecLoss"])
    trades_today = len(df[df["Day"] == day])

# --- Trade number auto ---
trade_no = trades_today + 1

# --- Previous outcome ---
prev_outcome = None
if trades_today > 0:
    prev_outcome = df.iloc[-1]["Outcome"]

# --- Trade Size Logic ---
def get_trade_size(consec_loss, trade_no, prev_outcome):
    if trade_no == 1:
        if consec_loss >= 2:
            return 0.2
        elif consec_loss == 1:
            return 0.3
        else:
            return 0.4
    else:
        if prev_outcome == "L":
            return 0.25
        else:
            return 0.4

trade_size = get_trade_size(consec_loss, trade_no, prev_outcome)
invested_amount = capital * trade_size

# --- CAPITAL DISPLAY ---
col1, col2 = st.columns(2)
col1.metric("💰 Total Capital", f"₹{round(capital,2)}")
col2.metric("📊 Invested Amount", f"₹{round(invested_amount,2)}")

st.markdown(f"📅 Day: {day} | Trades Today: {trades_today}/2")

# --- ONLY RULE LEFT: max 2 trades/day ---
if trades_today >= 2:
    st.warning("🚫 Max 2 trades reached for today")
    allow_trade = False
else:
    allow_trade = True

# --- Trade Input ---
outcome = st.selectbox("Outcome", ["W","L"])

st.write(f"📊 Trade #{trade_no} Size: {int(trade_size*100)}%")

# --- Execute Trade ---
if st.button("Add Trade") and allow_trade:

    if outcome == "W":
        pnl = capital * trade_size * 0.5
        capital += pnl
        consec_loss = 0
    else:
        pnl = capital * trade_size * 0.25
