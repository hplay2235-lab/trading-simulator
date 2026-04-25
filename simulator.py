import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Aggressive Trading System Tracker")

FILE = "data.csv"

# Initialize
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "Day","Capital","Outcome","Trade","TradeSize",
        "DailyResult","ConsecLoss"
    ])
    df.to_csv(FILE, index=False)

df = pd.read_csv(FILE)

# Inputs
start_capital = st.number_input("Starting Capital", value=25000)

# Get current state
if len(df) == 0:
    capital = start_capital
    day = 1
    consec_loss = 0
else:
    capital = df.iloc[-1]["Capital"]
    day = int(df.iloc[-1]["Day"])
    consec_loss = int(df.iloc[-1]["ConsecLoss"])

st.markdown(f"### 💰 Current Capital: ₹{round(capital,2)}")

# Trade input
trade_no = st.selectbox("Trade Number", [1,2])
outcome = st.selectbox("Outcome", ["W","L"])

# --- Trade Size Logic ---
def get_trade_size():
    if consec_loss >= 2:
        return 0.2
    elif consec_loss == 1:
        return 0.3
    else:
        return 0.4

trade_size = get_trade_size()

if trade_no == 2:
    if outcome == "W":
        trade_size = 0.4
    else:
        trade_size = 0.25

st.write(f"📊 Trade Size: {int(trade_size*100)}%")

# --- Execute Trade ---
if st.button("Add Trade"):

    global capital, consec_loss

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
        "Capital": capital,
        "Outcome": outcome,
        "Trade": trade_no,
        "TradeSize": trade_size,
        "DailyResult": "",
        "ConsecLoss": consec_loss
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv(FILE, index=False)

    st.success("Trade Recorded!")

# Display
st.dataframe(df, use_container_width=True)

if len(df) > 0:
    st.line_chart(df["Capital"])
