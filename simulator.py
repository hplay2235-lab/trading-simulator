import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="centered")
st.title("📊 Volatility Compounding Trading System")

# =========================
# 🇮🇳 FORMAT
# =========================
def format_inr(x):
    x = int(x)
    s = str(abs(x))
    if len(s) <= 3:
        res = s
    else:
        res = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            res = s[-2:] + "," + res
            s = s[:-2]
        if s:
            res = s + "," + res
    return f"₹{'-' if x < 0 else ''}{res}"

# =========================
# 🗄️ DB
# =========================
conn = sqlite3.connect("trades.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    day INTEGER,
    trade INTEGER,
    capital REAL,
    outcome TEXT,
    trade_size REAL,
    consec_loss INTEGER
)
""")
conn.commit()

df = pd.read_sql("SELECT * FROM trades", conn)

# =========================
# ⚙️ INPUTS
# =========================
start_capital = st.number_input("Starting Capital", value=25000)
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100
manual_pct = st.number_input("Manual Invest % (0 = auto)", value=0.0) / 100

# =========================
# 🧠 STATE
# =========================
if len(df) == 0:
    capital = start_capital
    day = 1
    consec_loss = 0
    trades_today = 0
else:
    day = int(df["day"].max())
    today = df[df["day"] == day]

    if len(today) == 0:
        capital = start_capital
        consec_loss = 0
        trades_today = 0
    else:
        capital = float(today.iloc[-1]["capital"])
        consec_loss = int(today.iloc[-1]["consec_loss"])
        trades_today = len(today)

# auto next day after 2 trades
if trades_today >= 2:
    day += 1
    trades_today = 0

trade_no = trades_today + 1
prev_outcome = df.iloc[-1]["outcome"] if len(df) > 0 else None

# =========================
# 📊 TRADE SIZE ENGINE
# =========================
def base_size(consec_loss, prev_outcome):
    if consec_loss >= 2:
        return 0.20
    elif consec_loss == 1:
        return 0.30
    else:
        return 0.40

if manual_pct > 0:
    trade_size = manual_pct
else:
    trade_size = base_size(consec_loss, prev_outcome)

# loss compression
trade_size = trade_size * (0.7 ** consec_loss)

# safety limits
trade_size = max(0.15, min(trade_size, 1.0))

invested = capital * trade_size

# =========================
# 📊 DISPLAY
# =========================
st.markdown(f"### 💰 Capital: {format_inr(capital)}")
st.caption(f"Day {day} • Trade {trade_no}/2")

c1, c2, c3 = st.columns(3)
c1.metric("Invested", format_inr(invested))
c2.metric("Loss Streak", consec_loss)
c3.metric("Trade %", f"{int(trade_size*100)}%")

# =========================
# 🎯 TRADE EXECUTION
# =========================
outcome = st.radio("Outcome", ["W", "L"], horizontal=True)

if st.button("Execute Trade"):

    if outcome == "W":
        profit = invested * reward_pct
        capital += profit
        consec_loss = 0
    else:
        loss = invested * risk_pct
        capital -= loss
        consec_loss += 1

    c.execute("""
    INSERT INTO trades VALUES (?,?,?,?,?,?)
    """, (day, trade_no, capital, outcome, trade_size, consec_loss))

    conn.commit()
    st.rerun()

# =========================
# 📌 SUGGESTIONS ENGINE
# =========================
st.markdown("## 📌 Suggestions")

def suggest(outcome, loss_streak):
    s = []

    if outcome == "W":
        s.append("🟢 Strong position state")
        s.append("📊 Maintain 30–40% exposure max")
        s.append("⚖️ Avoid increasing risk aggressively")

    elif outcome == "L":
        if loss_streak == 1:
            s.append("⚠️ First loss detected")
            s.append("📉 Reduce exposure to ~25–30%")
        elif loss_streak == 2:
            s.append("⚠️ 2 consecutive losses")
            s.append("📉 Defensive mode: 15–20% only")
        else:
            s.append("🚨 High loss streak")
            s.append("🧠 Stay at minimum 15% exposure")

    else:
        s.append("🟡 Start of cycle")
        s.append("📊 Normal exposure allowed")

    return s

for i in suggest(prev_outcome, consec_loss):
    st.write(i)

# =========================
# 📊 HISTORY
# =========================
with st.expander("📋 Trade History"):

    hist = pd.read_sql("SELECT * FROM trades", conn)

    if not hist.empty:

        pnl = []
        for i in range(len(hist)):
            if i == 0:
                pnl.append(hist.iloc[i]["capital"] - start_capital)
            else:
                pnl.append(hist.iloc[i]["capital"] - hist.iloc[i-1]["capital"])

        hist["P&L"] = pnl
        hist["capital"] = hist["capital"].apply(format_inr)
        hist["trade_size"] = (hist["trade_size"] * 100).astype(int).astype(str) + "%"

        def color(v):
            if v > 0:
                return f"🟢 {format_inr(v)}"
            return f"🔴 {format_inr(v)}"

        hist["P&L"] = hist["P&L"].apply(color)

        st.dataframe(hist, use_container_width=True)

    else:
        st.info("No trades yet")

# =========================
# 🔄 RESET
# =========================
if st.button("Reset System"):
    c.execute("DELETE FROM trades")
    conn.commit()
    st.rerun()
