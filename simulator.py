import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Trading Tracker")

FILE = "data.csv"

# --- Load once ---
if "df" not in st.session_state:
    if os.path.exists(FILE):
        st.session_state.df = pd.read_csv(FILE)
    else:
        st.session_state.df = pd.DataFrame(columns=[
            "Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"
        ])

df = st.session_state.df

# --- Input ---
start_capital = st.number_input("Starting Capital (₹)", value=25000)

# --- Get state ---
if len(df) == 0:
    capital = start_capital
    day = 1
    consec_loss = 0
    trades_today = 0
else:
    day = int(df["Day"].max())
    today_df = df[df["Day"] == day]

    if len(today_df) == 0:
        capital = start_capital
        consec_loss = 0
        trades_today = 0
    else:
        capital = float(today_df.iloc[-1]["Capital"])
        consec_loss = int(today_df.iloc[-1]["ConsecLoss"])
        trades_today = len(today_df)

# --- Auto next day after 2 trades ---
if trades_today >= 2:
    day += 1
    trades_today = 0

trade_no = trades_today + 1

# --- Previous outcome ---
prev_outcome = None
if trades_today > 0:
    prev_outcome = today_df.iloc[-1]["Outcome"]

# --- Trade size logic ---
def get_trade_size(consec_loss, trade_no, prev_outcome):
    if trade_no == 1:
        if consec_loss >= 2:
            return 0.2
        elif consec_loss == 1:
            return 0.3
        else:
            return 0.4
    else:
        return 0.25 if prev_outcome == "L" else 0.4

trade_size = get_trade_size(consec_loss, trade_no, prev_outcome)
invested_amount = capital * trade_size

# --- Display ---
# --- Daily P&L Calculation ---
if len(df) == 0 or trades_today == 0:
    day_start_capital = capital
else:
    day_start_capital = today_df.iloc[0]["Capital"]

daily_pnl = capital - day_start_capital

# --- Display Boxes ---
col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Capital", f"₹{round(capital,2)}")
col2.metric("📊 Invested Amount", f"₹{round(invested_amount,2)}")

col3.metric(
    "📈 Daily P&L",
    f"₹{round(daily_pnl,2)}",
    delta=f"{round((daily_pnl/day_start_capital)*100,2)}%"
)

st.markdown(f"📅 Day {day} | Trade {trade_no}/2")

# --- Input ---
outcome = st.selectbox("Outcome", ["W","L"])

# --- Add Trade ---
if st.button("Add Trade"):

    if outcome == "W":
        capital += capital * trade_size * 0.5
        consec_loss = 0
    else:
        capital -= capital * trade_size * 0.25
        consec_loss += 1

    new_row = {
        "Day": day,
        "Trade": trade_no,
        "Capital": capital,
        "Outcome": outcome,
        "TradeSize": trade_size,
        "ConsecLoss": consec_loss
    }

    st.session_state.df = pd.concat(
        [st.session_state.df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    st.session_state.df.to_csv(FILE, index=False)
    st.rerun()

# --- Reset ---
if st.button("Reset"):
    st.session_state.df = pd.DataFrame(columns=[
        "Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"
    ])
    
    if os.path.exists(FILE):
        os.remove(FILE)
    
    st.success("Reset successful")
    st.rerun()
