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

# --- Inputs ---
start_capital = st.number_input("Starting Capital (₹)", value=25000)

# --- Custom Risk/Reward ---
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100

st.markdown(f"⚖️ Risk:Reward = 1 : {round(reward_pct/risk_pct,2) if risk_pct != 0 else 0}")

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

# --- Auto next day ---
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

# --- Daily P&L ---
if len(df) == 0 or trades_today == 0:
    day_start_capital = capital
else:
    day_start_capital = today_df.iloc[0]["Capital"]

daily_pnl = capital - day_start_capital

# --- Display boxes ---
col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Capital", f"₹{round(capital,2)}")
col2.metric("📊 Invested Amount", f"₹{round(invested_amount,2)}")
col3.metric(
    "📈 Daily P&L",
    f"₹{round(daily_pnl,2)}",
    delta=f"{round((daily_pnl/day_start_capital)*100,2) if day_start_capital != 0 else 0}%"
)

st.markdown(f"📅 Day {day} | Trade {trade_no}/2")

# --- Input ---
outcome = st.selectbox("Outcome", ["W","L"])

# --- Add Trade ---
if st.button("Add Trade"):

    if outcome == "W":
        pnl = capital * trade_size * reward_pct
        capital += pnl
        consec_loss = 0
    else:
        pnl = capital * trade_size * risk_pct
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
    st.rerun()

# --- Trade-wise Summary ---
st.subheader("📊 Trade-wise Summary")

df_full = st.session_state.df.copy()
df_full = df_full[df_full["Trade"] > 0].reset_index(drop=True)

if not df_full.empty:

    invested_list = []
    pnl_list = []
    prev_capital = None

    for i, row in df_full.iterrows():
        capital_now = row["Capital"]
        trade_size = row["TradeSize"]

        if prev_capital is None:
            if row["Outcome"] == "W":
                prev_capital = capital_now / (1 + trade_size * reward_pct)
            else:
                prev_capital = capital_now / (1 - trade_size * risk_pct)

        invested = prev_capital * trade_size

        if row["Outcome"] == "W":
            pnl = invested * reward_pct
        else:
            pnl = -invested * risk_pct

        invested_list.append(invested)
        pnl_list.append(pnl)

        prev_capital = capital_now

    df_full["Invested ₹"] = invested_list
    df_full["PnL ₹"] = pnl_list

    df_display = df_full[[
        "Day","Trade","Outcome","TradeSize","Invested ₹","PnL ₹","Capital"
    ]].copy()

    df_display["TradeSize"] = (df_display["TradeSize"] * 100).astype(int).astype(str) + "%"
    df_display["Invested ₹"] = df_display["Invested ₹"].round(2)
    df_display["PnL ₹"] = df_display["PnL ₹"].round(2)
    df_display["Capital"] = df_display["Capital"].round(2)

    st.dataframe(df_display, use_container_width=True)
