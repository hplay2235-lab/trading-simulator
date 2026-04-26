import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="centered")
st.title("📊 Trading Dashboard")

# =========================
# 🇮🇳 INDIAN FORMAT
# =========================
def format_inr(x):
    x = int(x)
    s = str(abs(x))
    if len(s) <= 3:
        result = s
    else:
        result = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            result = s[-2:] + "," + result
            s = s[:-2]
        if s:
            result = s + "," + result
    return f"₹{'-' if x < 0 else ''}{result}"

# =========================
# 🗄️ SQLITE
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

df = pd.read_sql("SELECT * FROM trades", conn)

# =========================
# ⚙️ INPUTS
# =========================
start_capital = st.number_input("Starting Capital (₹)", value=25000)
reward_pct = st.number_input("Reward %", value=50.0) / 100
risk_pct = st.number_input("Risk %", value=25.0) / 100
invest_pct_input = st.number_input("Invest % (0 = Auto)", value=0.0) / 100

# =========================
# 🧠 STATE
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

# Auto next day after 2 trades
if trades_today >= 2:
    day += 1
    trades_today = 0

trade_no = trades_today + 1
prev_outcome = today_df.iloc[-1]["Outcome"] if trades_today > 0 else None

# =========================
# 📊 TRADE SIZE LOGIC
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

if invest_pct_input > 0:
    base_trade_size = invest_pct_input
else:
    base_trade_size = get_trade_size(consec_loss, trade_no, prev_outcome)

trade_size = base_trade_size * (0.7 ** consec_loss) if consec_loss > 0 else base_trade_size

# 🔒 MIN MAX LIMIT
trade_size = max(min(trade_size, 1.0), 0.15)

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
# 📱 DASHBOARD
# =========================
st.markdown(f"### 💰 {format_inr(capital)}")
st.caption(f"Day {day} • Trade {trade_no}/2")

c1, c2, c3 = st.columns(3)
c1.metric("Invested", format_inr(invested))
c2.metric("Daily P&L", format_inr(daily_pnl))
c3.metric("Loss Streak", consec_loss)

# =========================
# 🎯 TRADE INPUT
# =========================
outcome = st.radio("Outcome", ["W", "L"], horizontal=True)

if st.button("Add Trade"):

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
# 📌 SUGGESTIONS ENGINE
# =========================
def get_suggestion(prev_outcome, consec_loss, capital):

    tips = []

    if prev_outcome == "W":
        tips.append("🟢 Winning streak active")
        tips.append("📊 Maintain 30–40% risk or slightly reduce")
        tips.append("⚖️ Avoid over-aggression")

    elif prev_outcome == "L":
        if consec_loss == 1:
            tips.append("⚠️ First loss detected")
            tips.append("📉 Suggested size: 25–30%")
        elif consec_loss == 2:
            tips.append("⚠️ 2 consecutive losses")
            tips.append("📉 Switch to defensive mode (15–20%)")
        else:
            tips.append("🚨 High loss streak")
            tips.append("📉 Minimum 15% only")

    else:
        tips.append("🟡 Start of cycle")
        tips.append("📊 Use normal sizing (30–40%)")

    return tips

st.markdown("## 📌 Suggestions")

suggestions = get_suggestion(prev_outcome, consec_loss, capital)

for s in suggestions:
    st.write(s)

# =========================
# 📊 STATS
# =========================
df_full = pd.read_sql("SELECT * FROM trades", conn)
df_full = df_full[df_full["Trade"] > 0]

if not df_full.empty:

    wins = len(df_full[df_full["Outcome"] == "W"])
    win_rate = wins / len(df_full)

    peak = df_full["Capital"].cummax()
    drawdown = ((df_full["Capital"] - peak) / peak) * 100

    st.markdown("### 📊 Stats")
    c1, c2 = st.columns(2)
    c1.metric("Win %", f"{int(win_rate*100)}%")
    c2.metric("Max DD", f"{int(drawdown.min())}%")

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

    if not df_show.empty:

        pnl = []
        for i in range(len(df_show)):
            if i == 0:
                pnl.append(df_show.iloc[i]["Capital"] - start_capital)
            else:
                pnl.append(df_show.iloc[i]["Capital"] - df_show.iloc[i-1]["Capital"])

        df_show["P&L"] = pnl

        df_show["Capital"] = df_show["Capital"].apply(format_inr)
        df_show["TradeSize"] = (df_show["TradeSize"] * 100).astype(int).astype(str) + "%"

        def pnl_color(val):
            if val > 0:
                return f"🟢 {format_inr(val)}"
            elif val < 0:
                return f"🔴 {format_inr(val)}"
            return format_inr(val)

        df_show["P&L"] = df_show["P&L"].apply(pnl_color)

        st.dataframe(df_show, use_container_width=True)

    else:
        st.info("No trades yet")
