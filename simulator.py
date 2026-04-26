import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="centered")
st.title("📊 Trading Dashboard")

# =========================
# 🇮🇳 INR FORMAT FUNCTION
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
# 🗄️ DATABASE
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

st.caption(f"⚖️ RR = 1 : {int(reward_pct/risk_pct) if risk_pct else 0}")

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
outcome = st.radio("Outcome", ["W","L"], horizontal=True)

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
# 📊 STATS
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
    s1.metric("Win %", f"{int(win_rate*100)}%")
    s2.metric("Max DD", f"{int(max_dd)}%")

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

        # --- Calculate P&L ---
        pnl_list = []
        for i in range(len(df_show)):
            if i == 0:
                pnl = df_show.iloc[i]["Capital"] - start_capital
            else:
                pnl = df_show.iloc[i]["Capital"] - df_show.iloc[i-1]["Capital"]
            pnl_list.append(pnl)

        df_show["P&L"] = pnl_list

        # --- Format for display ---
        df_show["Capital"] = df_show["Capital"].apply(format_inr)
        df_show["TradeSize"] = (df_show["TradeSize"] * 100).astype(int).astype(str) + "%"

        # Keep numeric P&L for coloring
        df_numeric = df_show.copy()

        # Convert P&L to formatted string
        df_show["P&L"] = df_show["P&L"].apply(format_inr)

        # --- Styling function ---
        def color_pnl(val):
            try:
                v = float(val)
                if v > 0:
                    return "color: green; font-weight: bold;"
                elif v < 0:
                    return "color: red; font-weight: bold;"
                else:
                    return ""
            except:
                return ""

        # Apply styling using numeric P&L
        styled_df = df_show.style.apply(
            lambda x: [color_pnl(df_numeric.loc[x.name, "P&L"]) if col == "P&L" else "" for col in df_show.columns],
            axis=1
        )

        st.dataframe(styled_df, use_container_width=True)

    else:
        st.info("No trades yet")
