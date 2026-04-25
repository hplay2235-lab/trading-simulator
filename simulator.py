import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="centered")

st.title("📊 Daily Trading Tracker")

FILE = "data.csv"

# --- Initialize ---
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["Day", "Capital", "Outcome", "Drawdown"])
    df.to_csv(FILE, index=False)

df = pd.read_csv(FILE)

# --- Inputs ---
capital_input = st.number_input("Starting Capital (₹)", value=10000)
risk_input = st.number_input("Base Risk %", value=5.0) / 100
reward_input = st.number_input("Reward %", value=10.0) / 100

st.markdown("### Enter Today's Trade")

outcome = st.selectbox("Outcome", ["W", "L"])

# --- Get current state ---
if len(df) == 0:
    capital = capital_input
    peak = capital
    day = 1
else:
    capital = df.iloc[-1]["Capital"]
    peak = max(df["Capital"])
    day = len(df) + 1

# --- Add Trade ---
if st.button("Add Trade"):

    drawdown = (capital - peak) / peak

    # Dynamic risk logic
    if drawdown > -0.1:
        risk = risk_input
    elif drawdown > -0.2:
        risk = 0.03
    elif drawdown > -0.3:
        risk = 0.02
    else:
        risk = 0.01

    # Apply trade
    if outcome == "W":
        capital = capital * (1 + reward_input)
    else:
        capital = capital * (1 - risk)

    peak = max(peak, capital)

    new_row = {
        "Day": day,
        "Capital": capital,
        "Outcome": outcome,
        "Drawdown": (capital - peak) / peak * 100
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv(FILE, index=False)

    st.success(f"Trade for Day {day} added!")

# --- Display ---
st.subheader("📋 Trade History")
st.dataframe(df, use_container_width=True)

if len(df) > 0:
    st.subheader("📈 Equity Curve")
    st.line_chart(df.set_index("Day")["Capital"])

    st.subheader("📊 Performance")

    final_capital = df.iloc[-1]["Capital"]
    total_return = (final_capital / capital_input - 1) * 100
    max_dd = df["Drawdown"].min()

    col1, col2, col3 = st.columns(3)
    col1.metric("Final Capital", f"₹{round(final_capital,2)}")
    col2.metric("Return %", f"{round(total_return,2)}%")
    col3.metric("Max Drawdown %", f"{round(max_dd,2)}%")

# --- Reset Button ---
if st.button("Reset All Data"):
    os.remove(FILE)
    st.warning("All data reset. Refresh app.")
