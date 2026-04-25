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

    # count today's trades
    trades_today = len(df[df["Day"] == day])

# --- UI Display ---
st.markdown(f"### 💰 Current Capital: ₹{round(capital,2)}")
st.markdown(f"📅 Day: {day} | Trades Today: {trades_today}/2")

# --- HARD RULE ENFORCEMENT ---
if trades_today >= 2:
    st.warning("🚫 Max 2 trades reached for today")
    allow_trade = False
elif consec_loss >= 2:
    st.warning("🚫 2 losses hit — STOP trading today")
    allow_trade = False
else:
    allow_trade = True

# --- Trade Input ---
trade_no = trades_today + 1
outcome = st.selectbox("Outcome", ["W","L"])

# --- Trade Size Logic ---
def get_trade_size(consec_loss, trade_no, prev_outcome=None):
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

# get previous outcome if exists
prev_outcome = None
if trades_today > 0:
    prev_outcome = df.iloc[-1]["Outcome"]

trade_size = get_trade_size(consec_loss, trade_no, prev_outcome)

st.write(f"📊 Trade #{trade_no} Size: {int(trade_size*100)}%")

# --- Execute Trade ---
if st.button("Add Trade") and allow_trade:

    if outcome == "W":
        pnl = capital * trade_size * 0.5
        capital += pnl
        consec_loss = 0
    else:
        pnl = capital * trade_size * 0.25
        capital -= pnl
        consec_loss += 1

    new_row = {
        "Day": day,
        "Trade": trade_no,
        "Capital": capital,
        "Outcome": outcome,
        "TradeSize": trade_size,
        "ConsecLoss": consec_loss
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv(FILE, index=False)

    st.success(f"Trade {trade_no} recorded!")

# --- NEXT DAY BUTTON ---
if st.button("➡️ Start Next Day"):
    if trades_today == 0:
        st.warning("No trades today yet")
    else:
        new_day = day + 1
        st.success(f"Moved to Day {new_day}")
        # dummy row to mark new day start
        df = pd.concat([df, pd.DataFrame([{
            "Day": new_day,
            "Trade": 0,
            "Capital": capital,
            "Outcome": "-",
            "TradeSize": 0,
            "ConsecLoss": consec_loss
        }])])
        df.to_csv(FILE, index=False)

# --- Display ---
st.subheader("📋 Trade History")
st.dataframe(df, use_container_width=True)

if len(df) > 0:
    st.subheader("📈 Equity Curve")
    st.line_chart(df["Capital"])
