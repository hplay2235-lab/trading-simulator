import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")
st.title("📊 Trading Dashboard")

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
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100

# --- State ---
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
prev_outcome = today_df.iloc[-1]["Outcome"] if trades_today > 0 else None

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

# --- Daily PnL ---
if len(df) == 0 or trades_today == 0:
    day_start = capital
else:
    day_start = today_df.iloc[0]["Capital"]

daily_pnl = capital - day_start

# =========================
# 📱 MOBILE METRICS (STACKED)
# =========================

st.markdown(f"### 💰 ₹{round(capital,2)}")
st.caption(f"Day {day} • Trade {trade_no}/2")

c1, c2, c3 = st.columns(3)
c1.metric("Invested", f"₹{round(invested_amount,0)}")
c2.metric("Daily P&L", f"₹{round(daily_pnl,0)}")
c3.metric("Streak", consec_loss)

# =========================
# 📊 PRO METRICS
# =========================

df_full = df[df["Trade"] > 0].copy()

if not df_full.empty:

    # Win rate
    total = len(df_full)
    wins = len(df_full[df_full["Outcome"] == "W"])
    win_rate = wins / total

    # Drawdown
    equity = df_full["Capital"]
    peak = equity.cummax()
    drawdown = ((equity - peak) / peak) * 100
    max_dd = drawdown.min()

    # Expectancy
    invested = df_full["Capital"] * df_full["TradeSize"]
    pnl = []

    for i, row in df_full.iterrows():
        if row["Outcome"] == "W":
            pnl.append(invested.iloc[i] * reward_pct)
        else:
            pnl.append(-invested.iloc[i] * risk_pct)

    avg_win = pd.Series(pnl)[pd.Series(pnl) > 0].mean() if wins > 0 else 0
    avg_loss = abs(pd.Series(pnl)[pd.Series(pnl) < 0].mean()) if wins < total else 0

    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    c4, c5, c6 = st.columns(3)
    c4.metric("Win %", f"{round(win_rate*100,1)}")
    c5.metric("Max DD", f"{round(max_dd,1)}%")
    c6.metric("Expectancy", f"₹{round(expectancy,0)}")

# =========================
# ⚠️ WARNINGS
# =========================

if consec_loss >= 2:
    st.warning("⚠️ Losing streak — reduce risk")

if day_start != 0:
    loss_pct = (daily_pnl / day_start) * 100
    if loss_pct < -10:
        st.error("🚫 Daily loss >10%")

# =========================
# 🎯 TRADE INPUT
# =========================

outcome = st.radio("Outcome", ["W","L"], horizontal=True)
setup_ok = st.checkbox("A+ Setup Only")

if st.button("Add Trade"):
    if not setup_ok:
        st.warning("Blocked: No A+ setup")
    else:
        if outcome == "W":
            capital += capital * trade_size * reward_pct
            consec_loss = 0
        else:
            capital -= capital * trade_size * risk_pct
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

# =========================
# 🔄 RESET
# =========================

if st.button("Reset"):
    st.session_state.df = pd.DataFrame(columns=[
        "Day","Trade","Capital","Outcome","TradeSize","ConsecLoss"
    ])
    if os.path.exists(FILE):
        os.remove(FILE)
    st.rerun()

# =========================
# 📋 HISTORY (COLLAPSIBLE)
# =========================

with st.expander("📋 Trade History"):
    st.dataframe(st.session_state.df, use_container_width=True)
