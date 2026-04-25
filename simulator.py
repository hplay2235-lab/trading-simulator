import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Trading Tracker (Stable Version)")

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

# --- Inputs ---
start_capital = st.number_input("Starting Capital (₹)", value=25000)

# --- Initialize state ---
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
        trades_today = len(today_df[today_df["Trade"] > 0])

# --- Trade number ---
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

# --- UI Boxes ---
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

# --- Next Day ---
if st.button("➡️ Start Next Day"):
    if trades_today == 0:
        st.warning("No trades today yet")
    else:
        new_day = day + 1

        new_row = {
            "Day": new_day,
            "Trade": 0,
            "Capital": capital,
            "Outcome": "-",
            "TradeSize": 0,
            "ConsecLoss": consec_loss
        }

        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        st.session_state.df.to_csv(FILE, index=False)
        st.rerun()

# --- Reset ---
if st.button("🔄 Reset to Day 1"):
    st.session_state.df = pd.DataFrame(columns=[
        "Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"
    ])
    if os.path.exists(FILE):
        os.remove(FILE)
    st.rerun()

# --- Display ---
st.subheader("📋 Trade History")
st.dataframe(st.session_state.df, use_container_width=True)

if len(st.session_state.df) > 0:
    st.subheader("📈 Equity Curve")
    chart_df = st.session_state.df[st.session_state.df["Trade"] > 0]
    if not chart_df.empty:
        st.line_chart(chart_df.set_index("Day")["Capital"])
