import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(layout="centered")
st.title("📊 Trading Dashboard")

# =========================
# 🗄️ DATABASE SETUP
# =========================

conn = sqlite3.connect("trades.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    Day INTEGER,
    Trade INTEGER,
    Capital REAL,
    Outcome TEXT,
    TradeSize REAL,
    ConsecLoss INTEGER
)
""")
conn.commit()

# Load data
df = pd.read_sql("SELECT * FROM trades", conn)

# =========================
# ⚙️ INPUTS
# =========================

start_capital = st.number_input("Starting Capital (₹)", value=25000)
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100

st.caption(f"⚖️ RR = 1 : {round(reward_pct/risk_pct,2) if risk_pct else 0}")

# =========================
# 🧠 STATE LOGIC
# =========================

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

# Auto next day
if trades_today >= 2:
    day += 1
    trades_today = 0

trade_no = trades_today + 1
prev_outcome = today_df.iloc[-1]["Outcome"] if trades_today > 0 else None

# =========================
# 📊 TRADE SIZE
# =========================

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
invested = capital * trade_size

# =========================
# 📈 DAILY P&L
# =========================

if len(df) == 0 or trades_today == 0:
    day_start = capital
else:
    day_start = today_df.iloc[0]["Capital"]

daily_pnl = capital - day_start

# =========================
# 📱 MOBILE METRICS
# =========================

st.markdown(f"### 💰 ₹{round(capital,2)}")
st.caption(f"Day {day} • Trade {trade_no}/2")

c1, c2, c3 = st.columns(3)
c1.metric("Invested", f"₹{round(invested,0)}")
c2.metric("Daily P&L", f"₹{round(daily_pnl,0)}")
c3.metric("Loss Streak", consec_loss)

# =========================
# 🧠 A+ CHECKLIST
# =========================

st.markdown("### 🧠 A+ Setup")

col1, col2 = st.columns(2)
trend = col1.checkbox("Trend")
level = col2.checkbox("Level")
confirmation = col1.checkbox("Confirmation")
rr = col2.checkbox("RR ≥ 1:2")
entry = st.checkbox("Clean Entry")

score = sum([trend, level, confirmation, rr, entry])

if score >= 4:
    st.success(f"A+ Setup ✅ ({score}/5)")
    allow_trade = True
else:
    st.warning(f"Not A+ ❌ ({score}/5)")
    allow_trade = False

# =========================
# 🎯 TRADE INPUT
# =========================

outcome = st.radio("Outcome", ["W","L"], horizontal=True)

if st.button("Add Trade"):
    if not allow_trade:
        st.warning("🚫 Trade blocked (Not A+)")
    else:
        if outcome == "W":
            capital += capital * trade_size * reward_pct
            consec_loss = 0
        else:
            capital -= capital * trade_size * risk_pct
            consec_loss += 1

        c.execute("""
        INSERT INTO trades VALUES (?,?,?,?,?,?)
        """, (day, trade_no, capital, outcome, trade_size, consec_loss))

        conn.commit()
        st.rerun()

# =========================
# 📊 PRO METRICS
# =========================

df_full = pd.read_sql("SELECT * FROM trades", conn)
df_full = df_full[df_full["Trade"] > 0]

if not df_full.empty:

    total = len(df_full)
    wins = len(df_full[df_full["Outcome"] == "W"])
    win_rate = wins / total

    equity = df_full["Capital"]
    peak = equity.cummax()
    drawdown = ((equity - peak) / peak) * 100
    max_dd = drawdown.min()

    st.markdown("### 📊 Stats")
    s1, s2 = st.columns(2)
    s1.metric("Win %", f"{round(win_rate*100,1)}")
    s2.metric("Max DD", f"{round(max_dd,1)}%")

# =========================
# 🔄 RESET
# =========================

if st.button("Reset"):
    c.execute("DELETE FROM trades")
    conn.commit()
    st.rerun()

# =========================
# 📋 HISTORY
# =========================

with st.expander("📋 Trade History"):
    df_show = pd.read_sql("SELECT * FROM trades", conn)
    st.dataframe(df_show, use_container_width=True)
