from advisory_agent.models import AssetClass, Holding, Portfolio, RiskProfile, SimulationRequest
from agents.orchestrator import PortfolioAdvisorOrchestrator


def main() -> None:
    try:
        import streamlit as st
    except ImportError as error:
        raise SystemExit("Install the UI extras with: python -m pip install -r requirements.txt") from error

    st.set_page_config(page_title="Portfolio Advisor", layout="wide")
    st.title("Personalized Portfolio Advisor")
    st.caption("Scenario-tested guidance with grounded explanations. This is not financial advice.")
    profile = RiskProfile(st.selectbox("Risk profile", [item.value for item in RiskProfile]))
    col1, col2, col3 = st.columns(3)
    with col1:
        equities = st.number_input("Equities", min_value=0.0, value=7000.0)
    with col2:
        bonds = st.number_input("Bonds", min_value=0.0, value=3000.0)
    with col3:
        cash = st.number_input("Cash", min_value=0.0, value=0.0)
    contribution = st.number_input("Monthly contribution", min_value=0.0, value=250.0)
    years = st.number_input("Projection years", min_value=1, value=5)
    if st.button("Generate advisory report", type="primary"):
        portfolio = Portfolio((Holding("EQUITIES", AssetClass.EQUITIES, equities), Holding("BONDS", AssetClass.BONDS, bonds), Holding("CASH", AssetClass.CASH, cash)))
        workflow = PortfolioAdvisorOrchestrator().run(portfolio, profile, SimulationRequest(contribution, years, 0.06))
        st.metric("Portfolio value", f"${workflow.analytics.total_value:,.2f}")
        st.subheader("Recommendations")
        for item in workflow.report.recommendations:
            st.write(f"**{item.action.title()} {item.asset_class.value}**: ${item.amount:,.2f} - {item.reason}")
        st.subheader("Scenario stress test")
        st.bar_chart({item.name: item.portfolio_change for item in workflow.scenarios})
        st.subheader("Grounded narrative")
        st.write(workflow.narrative.text)
        st.caption(f"QA gate approved: {workflow.qa.approved}")


if __name__ == "__main__":
    main()