import pandas as pd
import streamlit as st

from agents.orchestrator import PortfolioOrchestrator

from models import AnalysisRequest, Goal, RiskResponses, Holding

st.set_page_config(
    page_title="Personalized Portfolio Advisor with What-If Simulation",
    layout="wide",
)

st.title("Personalized Portfolio Advisor with What-If Simulation")

# ======================================
# Investor Profile
# ======================================

st.header("Investor Profile")

goal_name = st.text_input(
    "Financial Goal",
    value="Retirement",
)

target_amount = st.number_input(
    "Target Amount",
    min_value=1000.0,
    value=30000000.0,
)

investment_horizon = st.number_input(
    "Investment Horizon (Years)",
    min_value=1,
    value=20,
)

monthly_contribution = st.number_input(
    "Monthly Contribution",
    min_value=0.0,
    value=25000.0,
)

risk_appetite = st.selectbox(
    "Risk Appetite",
    ["low", "medium", "high"],
)

loss_tolerance = st.slider(
    "Loss Tolerance (%)",
    min_value=0,
    max_value=100,
    value=20,
)

income_stability = st.selectbox(
    "Income Stability",
    [
        "stable",
        "variable",
        "medium",
        "high",
        "low",
    ],
)

investment_experience = st.selectbox(
    "Investment Experience",
    [
        "beginner",
        "intermediate",
        "advanced",
    ],
)

liquidity_need = st.selectbox(
    "Liquidity Need",
    [
        "low",
        "medium",
        "high",
    ],
)

scenario = st.selectbox(
    "Scenario",
    [
        "base",
        "market_downturn",
        "rate_hike",
        "inflation",
    ],
)

# ======================================
# Portfolio Input
# ======================================

st.header("Portfolio Input")

input_mode = st.radio(
    "Select Input Method",
    [
        "Upload CSV",
        "Manual Entry",
    ],
)

holdings = []

# ======================================
# CSV Upload
# ======================================

if input_mode == "Upload CSV":
    uploaded_file = st.file_uploader("Upload Portfolio CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Portfolio")
        st.dataframe(df)

        for _, row in df.iterrows():
            history = []
            if "history" in df.columns:
                history = [
                    float(x.strip())
                    for x in str(
                        row["history"]
                    ).split(",")
                    if x.strip()
                ]

            holdings.append(
                Holding(
                    symbol=str(row["symbol"]),
                    quantity=float(row["quantity"]),
                    current_price=float(row["current_price"]),
                    history=history,
                )
            )

# ======================================
# Manual Entry
# ======================================

else:

    num_holdings = st.number_input("Number of Holdings",
        min_value=1,
        max_value=20,
        value=1,
    )

    for index in range(num_holdings):
        st.subheader(f"Holding {index + 1}")

        symbol = st.text_input( "Ticker Symbol",
            key=f"symbol_{index}",
            placeholder="AAPL / MSFT / TSLA"
        )

        quantity = st.number_input("Quantity",
            min_value=1.0,
            value=10.0,
            key=f"qty_{index}",
        )

        current_price = st.number_input("Current Price",
            min_value=0.01,
            value=100.0,
            key=f"price_{index}",
        )

        history_text = st.text_input("Price History (comma separated)",
            value="100,98,103,97,105,101,108,104",
            key=f"history_{index}",
            help="Example: 90,95,100,110,120"
        )

        history = []

        if history_text:
            try:
                history = [
                    float(x.strip())
                    for x in history_text.split(",")
                    if x.strip()
                ]
            except ValueError:
                st.warning(f"Invalid history for Holding {index + 1}")


        if symbol.strip():
            holdings.append(
                Holding(
                    symbol=symbol.strip().upper(),
                    quantity=quantity,
                    current_price=current_price,
                    history=history,
                )
            )

# ======================================
# Execute Agents
# ======================================

if st.button("Run Portfolio Analysis"):
    if len(holdings) == 0:
        st.error("Please enter a ticker symbol for at least one holding.")

    else:
        try:
            request = AnalysisRequest(
                goal=Goal(
                    name=goal_name,
                    target_amount=target_amount,
                    time_horizon_years=investment_horizon,
                    monthly_contribution=monthly_contribution,
                ),

                risk_responses=RiskResponses(
                    risk_appetite=risk_appetite,
                    loss_tolerance_percent=loss_tolerance,
                    income_stability=income_stability,
                    investment_experience=investment_experience,
                    liquidity_need=liquidity_need,
                ),

                holdings=holdings,
                scenario=scenario,
            )
            orchestrator = (PortfolioOrchestrator())
            result = orchestrator.run(request)
            analysis = result["analysis_result"]
            risk = result["risk_result"]

            # =====================
            # Portfolio Overview
            # =====================

            st.header("Portfolio Overview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Portfolio Value",f"₹{analysis['total_market_value']:,.0f}",)
            col2.metric("Annual Return",f"{analysis['annualized_return']:.2%}",)
            col3.metric("Volatility",f"{analysis['annualized_volatility']:.2%}",)
            col4.metric("Sharpe Ratio",round(analysis["sharpe_ratio"],2,),)

            # =====================
            # Risk Section
            # =====================

            st.header("Risk Assessment")
            st.write(f"Risk Profile: **{risk['risk_profile']}**")
            st.write(f"Portfolio Risk: **{risk['portfolio_risk_level']}**")
            st.write(f"Alignment Status: **{risk['alignment_status']}**")
            st.info(risk["alignment_reason"])

            # =====================
            # Warnings
            # =====================

            if risk["warnings"]:
                st.header("Warnings")
                for warning in risk["warnings"]:
                    st.warning(warning)

            # =====================
            # Sector Allocation
            # =====================

            st.header("Sector Allocation")

            sector_df = pd.DataFrame(
                [
                    {
                        "Sector": sector,
                        "Weight %": weight * 100,
                    }
                    for sector, weight in
                    analysis["sector_allocation"].items()
                ]
            )

            if not sector_df.empty:
                st.bar_chart(sector_df.set_index("Sector"))
                st.dataframe(sector_df,use_container_width=True)
                

            # =====================
            # Monte Carlo
            # =====================

            # st.write("Annualized Return:", analysis["annualized_return"])
            # st.write("Annualized Volatility:",analysis["annualized_volatility"])
            def format_inr(value):
                if value >= 10000000:
                    return f"₹{value/10000000:.2f} Cr"
                if value >= 100000:
                    return f"₹{value/100000:.2f} Lakh"

                return f"₹{value:,.0f}"


            st.header("Monte Carlo Simulation")
            mc = analysis["monte_carlo_results"]
            st.metric("Goal Success Probability",f"{mc['goal_success_probability']:.2%}")
            st.write(f"Best Case (P90): "f"{format_inr(mc['best_case_p90'])}")
            st.write(f"Expected Case (P50): "f"{format_inr(mc['median_case_p50'])}")
            st.write(f"Worst Case (P10): "f"{format_inr(mc['worst_case_p10'])}")

            # =====================
            # Advisory Agent
            # =====================

            st.header("Recommendations")
            advisory = result["advisory_result"]

            if isinstance(advisory, dict):
                recommendations = advisory.get("recommendations","")
                st.markdown(recommendations)
            else:
                st.markdown(str(advisory))

            # =====================
            # QA Agent
            # =====================

            st.header("QA Review")
            qa = result["qa_result"]

            if qa["status"] == "Approved":
                st.success(qa["status"])
            else:
                st.warning(qa["status"])

            st.markdown(qa["review"])

            # =====================
            # Disclaimer
            # =====================

            st.header("Disclaimer")
            st.info(result["disclaimer"])

        except Exception as ex:
            st.exception(ex)