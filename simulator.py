import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt

st.title("📊 30-Day Trading Simulator")

capital_input = st.number_input("Starting Capital", value=10000)
risk_input = st.number_input("Base Risk %", value=5.0) / 100
reward_input = st.number_input("Reward %", value=10.0) / 100
win_rate = st.slider("Win Probability", 0.1, 0.9, 0.5)

if st.button("Run Simulation"):
    capital = capital_input
    peak = capital
    data = []

    for day in range(1, 31):
        outcome = "W" if random.random() < win_rate else "L"
        drawdown = (capital - peak) / peak

        if drawdown > -0.1:
            risk = risk_input
        elif drawdown > -0.2:
            risk = 0.03
        elif drawdown > -0.3:
            risk = 0.02
        else:
            risk = 0.01

        if outcome == "W":
            capital *= (1 + reward_input)
        else:
            capital *= (1 - risk)

        peak = max(peak, capital)

        data.append({
            "Day": day,
            "Capital": capital,
            "Outcome": outcome,
            "Drawdown": drawdown
        })

    df = pd.DataFrame(data)

    st.dataframe(df)

    fig, ax = plt.subplots()
    ax.plot(df["Day"], df["Capital"])
    st.pyplot(fig)

    total_return = (capital / capital_input - 1) * 100
    max_dd = df["Drawdown"].min() * 100

    st.write(f"Final Capital: ₹{round(capital,2)}")
    st.write(f"Return: {round(total_return,2)}%")
    st.write(f"Max Drawdown: {round(max_dd,2)}%")
