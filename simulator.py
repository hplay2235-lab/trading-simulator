import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Aggressive Trading System Tracker")

FILE = "data.csv"

# --- Initialize file ---
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"
    ])
    df.to_csv(FILE, index=False)

df = pd.read_csv(FILE)

# --- Ensure correct columns exist ---
required_cols = ["Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"]
for col in required_cols:
    if col not in df.columns:
        df[col] = 0

# --- Convert types safely ---
df["Day"] = pd.to_numeric(df["Day"], errors="coerce").fillna(0).astype(int)
df["Trade"] = pd.to_numeric(df["Trade"], errors="coerce").fillna(0).astype(int)
df["Capital"] = pd.to_numeric(df["Capital"], errors="coerce").fillna(0.0)
df["ConsecLoss"] = pd.to_numeric(df["ConsecLoss"], errors="coerce").fillna(0).astype(int)

# --- Inputs ---
start_capital = st.number_input("Starting Capital (₹)", value=25000)

# --- Current state ---
if len(df) == 0 or df["Day"].max() == 0:
    capital = start_capital
    day = 1
    consec_loss = 0
    trades_today = 0
else:
    day = df["Day"].max()
    today_df = df[df["Day"] == day]

    if len(today_df) == 0:
        capital = start_capital
        consec_loss = 0
        trades_today = 0
    else:
        capital = today_df.iloc[-1]["Capital"]
        consec_loss = today_df.iloc[-1]["ConsecLoss"]
        trades_today = len(today_df[today_df["Trade"] > 0])

# --- Trade number ---
trade_no = trades_today + 1

# --- Previous outcome ---
prev_outcome = None
if trades_today > 0:
    prev_outcome = today_df.iloc[-1]["Outcome"]

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

# --- Display boxes ---
col1, col2 = st.columns(2)
col1.metric("💰 Total Capital", f"₹{round(capital,2)}")
col2.metric("📊 Invested Amount", f"₹{round(invested_amount,2)}")

st.markdown(f"📅 Day: {day} | Trades Today: {trades_today}/2")

# --- Trade limit ---
allow_trade = trades_today < 2
if not allow_trade:
    st.warning("🚫 Max 2 trades reached today")

# --- Input ---
outcome = st.selectbox("Outcome", ["W","L"])
st.write(f"📊 Trade #{trade_no} Size: {int(trade_size*100)}%")

# --- Add Trade ---
if st.button("Add Trade") and allow_trade:

    if outcome == "W":
        capital += capital * trade_size * 0.5
        consec_loss = 0
    else:
        capital -= capital * trade_size * 0.25
        consec_loss += 1

    new_row = pd.DataFrame([{
        "Day": day,
        "Trade": trade_no,
        "Capital": capital,
        "Outcome": outcome,
        "TradeSize": trade_size,
        "ConsecLoss": consec_loss
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE, index=False)

    st.success(f"Trade {trade_no} recorded!")
    st.rerun()

# --- Next Day ---
if st.button("➡️ Start Next Day"):
    if trades_today == 0:
        st.warning("No trades today yet")
    else:
        new_day = day + 1
        new_row = pd.DataFrame([{
            "Day": new_day,
            "Trade": 0,
            "Capital": capital,
            "Outcome": "-",
            "TradeSize": 0,
            "ConsecLoss": consec_loss
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FILE, index=False)

        st.success(f"Moved to Day {new_day}")
        st.rerun()

# --- Reset ---
if st.button("🔄 Reset to Day 1"):
    if os.path.exists(FILE):
        os.remove(FILE)
    st.success("Reset done. Refresh app.")

# --- Display ---
st.subheader("📋 Trade History")
st.dataframe(df, use_container_width=True)

if len(df) > 0:
    st.subheader("📈 Equity Curve")
    st.line_chart(df[df["Trade"] > 0].set_index("Day")["Capital"])
