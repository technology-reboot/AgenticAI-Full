import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/agent")

st.set_page_config(page_title="Portfolio Advisor", layout="wide")
st.title("Personalized Portfolio Advisor")
st.caption("Goal-based what-if simulation and analysis agent")

# Keep a simple default holdings list in session state
if "holdings" not in st.session_state:
    st.session_state.holdings = [
        {"symbol": "ASSET_A", "quantity": 100.0, "current_price": 120.0, "purchase_price": 120.0, "history": [100.0, 101.0, 102.0, 103.0]},
        {"symbol": "ASSET_B", "quantity": 50.0, "current_price": 80.0, "purchase_price": 80.0, "history": [80.0, 81.0, 82.0, 83.0]},
    ]

with st.sidebar:
    st.subheader("Goal")
    goal_name = st.text_input("Goal name", value="House down payment")
    target_amount = st.number_input("Target amount", min_value=0.0, value=3000000.0)
    time_horizon_years = st.number_input("Time horizon years", min_value=1, value=7)
    monthly_contribution = st.number_input("Monthly contribution", min_value=0.0, value=25000.0)

    st.subheader("Risk responses")
    loss_tolerance = st.number_input("Loss tolerance %", min_value=0.0, max_value=100.0, value=15.0)
    income_stability = st.selectbox("Income stability", ["stable", "variable"])
    investment_experience = st.selectbox("Investment experience", ["beginner", "intermediate", "advanced"])
    liquidity_need = st.selectbox("Liquidity need", ["low", "medium", "high"])

    st.subheader("Holdings")
    rows = []
    for idx, row in enumerate(st.session_state.holdings):
        cols = st.columns(5)
        with cols[0]:
            symbol = st.text_input(f"Symbol {idx+1}", value=row.get("symbol", ""), key=f"symbol_{idx}")
        with cols[1]:
            quantity = st.number_input(f"Quantity {idx+1}", min_value=0.0, value=float(row.get("quantity", 0.0)), key=f"quantity_{idx}")
        with cols[2]:
            current_price = st.number_input(f"Current price {idx+1}", min_value=0.0, value=float(row.get("current_price", row.get("purchase_price", 0.0))), key=f"current_price_{idx}")
        with cols[3]:
            purchase_price = st.number_input(f"Purchase price {idx+1}", min_value=0.0, value=float(row.get("purchase_price", row.get("current_price", 0.0))), key=f"price_{idx}")
        with cols[4]:
            history_text = st.text_input(f"History {idx+1}", value=", ".join(str(x) for x in row.get("history", [])) or "", key=f"history_{idx}")
        history = []
        if history_text.strip():
            try:
                history = [float(x.strip()) for x in history_text.split(",") if x.strip()]
            except ValueError:
                history = []
        rows.append({
            "symbol": symbol,
            "quantity": quantity,
            "current_price": current_price,
            "purchase_price": purchase_price,
            "history": history,
        })

    if st.button("Add Holding"):
        st.session_state.holdings.append({"symbol": "ASSET_X", "quantity": 10.0, "current_price": 100.0, "purchase_price": 100.0, "history": [100.0, 101.0, 102.0]})

    if st.button("Remove Last Holding") and len(st.session_state.holdings) > 1:
        st.session_state.holdings.pop()

    scenario = st.selectbox("Scenario", ["base", "rate_hike", "market_downturn", "inflation"])

    st.session_state.holdings = rows

if st.button("Analyze Portfolio"):
    payload = {
        "goal": {
            "name": goal_name,
            "target_amount": float(target_amount),
            "time_horizon_years": int(time_horizon_years),
            "monthly_contribution": float(monthly_contribution),
        },
        "risk_responses": {
            "loss_tolerance_percent": float(loss_tolerance),
            "income_stability": income_stability,
            "investment_experience": investment_experience,
            "liquidity_need": liquidity_need,
        },
        "holdings": [
            {
                "symbol": row["symbol"],
                "quantity": float(row["quantity"]),
                "current_price": float(row["current_price"]),
                "purchase_price": float(row["purchase_price"]),
                "history": row.get("history", []),
            }
            for row in st.session_state.holdings
        ],
        "scenario": scenario,
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        st.subheader("Analytics Result")
        st.metric("Total Market Value", f"{result.get('total_market_value', 0):,.2f}")
        st.metric("Annualized Return", f"{result.get('annualized_return', 0):.2%}")
        st.metric("Annualized Volatility", f"{result.get('annualized_volatility', 0):.2%}")
        st.metric("Sharpe Ratio", f"{result.get('sharpe_ratio', 0):.2f}")
        st.metric("Maximum Drawdown", f"{result.get('maximum_drawdown', 0):.2%}")

        st.subheader("Analysis")
        st.markdown(result.get("analysis", "No analysis returned."))

        st.subheader("Asset Weights")
        st.json(result.get("asset_weights", {}))

        st.subheader("Asset Class Allocation")
        st.json(result.get("asset_class_allocation", {}))

        st.subheader("Sector Allocation")
        st.json(result.get("sector_allocation", {}))

        st.subheader("Concentration")
        st.json(result.get("concentration", {}))

        st.subheader("Data Quality Warnings")
        st.json(result.get("data_quality_warnings", []))

        st.subheader("Recommendations")
        for item in result.get("recommendations", []):
            st.write("- " + item)

        st.subheader("Analytics Report")
        st.json(result.get("analytics_report", {}))

    except requests.RequestException as exc:
        st.error(f"Agent unavailable: {exc}")
