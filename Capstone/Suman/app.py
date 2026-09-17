import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from finance_analyzer.ingestion import parse_tabular, parse_narrative
from finance_analyzer.store import GroundingStore
from finance_analyzer.ratios import RatioEngine
from finance_analyzer.red_flags import TrendRedFlagAgent
from finance_analyzer.grounding import RetrievalGroundingAgent
from finance_analyzer.narrative import NarrativeQAAgent
from finance_analyzer.comparison import ComparisonAgent

load_dotenv()
st.set_page_config(page_title="Financial Statement Analyzer", layout="wide")
st.title("Conversational Financial Statement Analyzer")
st.caption("Deterministic calculations, grounded retrieval, mandatory citations. Not investment advice.")
store = GroundingStore(os.getenv("CHROMA_PATH", ".chroma"))

tab_upload, tab_analyze, tab_chat, tab_compare = st.tabs(["Upload", "Analyze", "Ask", "Compare"])
with tab_upload:
    st.subheader("Numeric statements")
    files = st.file_uploader("Upload normalized CSV/XLSX", type=["csv","xlsx","xlsm"], accept_multiple_files=True)
    if st.button("Index numeric statements", type="primary"):
        total = 0
        for f in files or []:
            recs = parse_tabular(f.getvalue(), f.name); store.index_metrics(recs); total += len(recs)
        st.success(f"Indexed {total} metric rows.")
    st.subheader("Narrative notes")
    note = st.file_uploader("Upload PDF/TXT notes", type=["pdf","txt"])
    c1, c2 = st.columns(2)
    note_company, note_period = c1.text_input("Company for notes"), c2.text_input("Period for notes")
    if st.button("Index narrative notes") and note:
        chunks = parse_narrative(note.getvalue(), note.name); store.index_notes(chunks, note_company, note_period)
        st.success(f"Indexed {len(chunks)} note chunks.")

records = store.all_metrics()
companies = sorted({r.company for r in records})
with tab_analyze:
    if not companies: st.info("Upload statements first.")
    else:
        company = st.selectbox("Company", companies, key="an_company")
        periods = sorted({r.period for r in records if r.company == company})
        period = st.selectbox("Current period", periods)
        previous = st.selectbox("Previous period", [p for p in periods if p != period], index=0 if len(periods)>1 else None)
        curr = [r for r in records if r.company == company and r.period == period]
        prev = [r for r in records if r.company == company and r.period == previous] if previous else []
        curr_ratios, prev_ratios = RatioEngine().compute(curr, prev), RatioEngine().compute(prev)
        deltas, flags = TrendRedFlagAgent().evaluate(curr_ratios, prev_ratios)
        st.dataframe(pd.DataFrame([{"ratio":k,"value":v,"period_change":deltas.get(k)} for k,v in curr_ratios.items()]), use_container_width=True)
        st.subheader("Red flags")
        if flags:
            for f in flags: st.warning(f"{f['severity'].upper()}: {f['message']}")
        else: st.success("No configured red-flag threshold was triggered.")

with tab_chat:
    if not companies: st.info("Upload statements first.")
    else:
        company = st.selectbox("Company", companies, key="qa_company")
        periods = sorted({r.period for r in records if r.company == company})
        period = st.selectbox("Period", periods, key="qa_period")
        question = st.chat_input("Ask about liquidity, leverage, profitability, trends or a source figure")
        if question:
            context = RetrievalGroundingAgent(store).build_context(question, company, period)
            with st.chat_message("user"): st.write(question)
            with st.chat_message("assistant"): st.write(NarrativeQAAgent().answer(question, context))

with tab_compare:
    if len(companies) < 2: st.info("Upload at least two companies.")
    else:
        a, b = st.columns(2)
        ca = a.selectbox("Company A", companies, key="ca")
        cb = b.selectbox("Company B", [c for c in companies if c != ca], key="cb")
        pa = a.selectbox("Period A", sorted({r.period for r in records if r.company == ca}))
        pb = b.selectbox("Period B", sorted({r.period for r in records if r.company == cb}))
        result = ComparisonAgent().compare([r for r in records if r.company == ca], [r for r in records if r.company == cb], pa, pb)
        for w in result["warnings"]: st.warning(w)
        st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True)
