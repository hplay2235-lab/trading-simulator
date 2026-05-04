import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="centered")
st.title("📊 Volatility Compounding System")

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
# DB
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
    consec_loss INTEGER,
    withdrawal REAL
)
""")
conn.commit()

df = pd.read_sql("SELECT * FROM trades", conn)

# =========================
# INPUTS
# =========================
start_capital = st.number_input("Starting Capital", value=25000)
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100
manual_pct = st.number_input("Manual Invest % (0 = auto)", value=0.0) / 100

# =========================
# STATE
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
        trades_today = len(today[today["trade"] > 0])

# auto next day
if trades_today >= 2:
    day += 1
    trades_today = 0

trade_no = trades_today + 1
prev_outcome = df.iloc[-1]["outcome"] if len(df) > 0 else None

# =========================
# TRADE SIZE
# =========================
def base_size(consec_loss):
    if consec_loss >= 2:
        return 0.20
    elif consec_loss == 1:
        return 0.30
    return 0.40

if manual_pct > 0:
    trade_size = manual_pct
else:
    trade_size = base_size(consec_loss)

trade_size = trade_size * (0.7 ** consec_loss)
trade_size = max(0.15, min(trade_size, 1.0))

invested = capital * trade_size

# =========================
# DISPLAY
# =========================
st.markdown(f"### 💰 {format_inr(capital)}")
st.caption(f"Day {day} • Trade {trade_no}/2")

c1, c2, c3 = st.columns(3)
c1.metric("Invested", format_inr(invested))
c2.metric("Loss Streak", consec_loss)
c3.metric("Trade %", f"{int(trade_size*100)}%")

# =========================
# TRADE
# =========================
outcome = st.radio("Outcome", ["W", "L"], horizontal=True)

if st.button("Execute Trade"):

    if outcome == "W":
        capital += invested * reward_pct
        consec_loss = 0
    else:
        capital -= invested * risk_pct
        consec_loss += 1

    c.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?)",
              (day, trade_no, capital, outcome, trade_size, consec_loss, 0))

    conn.commit()
    st.rerun()

# =========================
# 💰 WITHDRAWAL SECTION
# =========================
st.markdown("## 💰 Withdraw")

withdraw_amt = st.number_input("Enter Withdrawal Amount", value=0)

if st.button("Withdraw"):

    if withdraw_amt > 0 and withdraw_amt <= capital:
        capital -= withdraw_amt

        c.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?)",
                  (day, 0, capital, "WDR", 0, consec_loss, withdraw_amt))

        conn.commit()
        st.success(f"Withdrawn {format_inr(withdraw_amt)}")
        st.rerun()
    else:
        st.error("Invalid withdrawal amount")

# =========================
# SUGGESTIONS
# =========================
st.markdown("## 📌 Suggestions")

def suggest(outcome, loss):
    if outcome == "W":
        return ["🟢 Winning phase", "Maintain 30–40%"]
    elif outcome == "L":
        if loss == 1:
            return ["⚠️ Reduce size", "25–30%"]
        elif loss == 2:
            return ["⚠️ Defensive mode", "15–20%"]
        return ["🚨 Survival mode", "15% only"]
    return ["🟡 Start cycle"]

for s in suggest(prev_outcome, consec_loss):
    st.write(s)

# =========================
# HISTORY
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
        hist["trade_size"] = hist["trade_size"].apply(
            lambda x: f"{int(x*100)}%" if x > 0 else "-"
        )
        hist["withdrawal"] = hist["withdrawal"].apply(
            lambda x: format_inr(x) if x > 0 else "-"
        )

        def color(v):
            return f"🟢 {format_inr(v)}" if v > 0 else f"🔴 {format_inr(v)}"

        hist["P&L"] = hist["P&L"].apply(color)

        st.dataframe(hist, use_container_width=True)

# =========================
# RESET
# =========================
if st.button("Reset"):
    c.execute("DELETE FROM trades")
    conn.commit()
    st.rerun()
