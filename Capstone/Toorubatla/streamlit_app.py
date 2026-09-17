from __future__ import annotations

import requests
import streamlit as st


st.set_page_config(
    page_title="Invoice Reconciliation",
    page_icon="📄",
    layout="wide",
)

st.title("Invoice Reconciliation")
st.caption("Upload accounting documents, review exceptions, and inspect vendor correspondence drafts.")

with st.sidebar:
    st.header("Configuration")
    api_url = st.text_input("Backend URL", "http://127.0.0.1:8000").rstrip("/")
    uploaded_files = st.file_uploader(
        "Upload invoice, purchase order, receipt, or bank statement files",
        type=["pdf", "csv", "png", "jpg", "jpeg", "tif", "tiff", "bmp"],
        accept_multiple_files=True,
    )
    run_reconciliation = st.button("Run reconciliation", type="primary", use_container_width=True)

if run_reconciliation:
    if not uploaded_files:
        st.warning("Upload at least one supported document first.")
    else:
        files = [
            (
                "files",
                (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream"),
            )
            for uploaded_file in uploaded_files
        ]
        try:
            with st.spinner("Processing documents..."):
                response = requests.post(f"{api_url}/reconcile", files=files, timeout=120)
            response.raise_for_status()
            st.session_state.result = response.json()
            st.success("Reconciliation completed.")
        except requests.RequestException as error:
            st.error(f"Could not connect to the backend at {api_url}. Start FastAPI first.\n\n{error}")

result = st.session_state.get("result")
if not result:
    st.info("Upload your documents and select 'Run reconciliation'.")
else:
    documents = result.get("documents", [])
    records = result.get("records", [])
    exceptions = result.get("exceptions", [])
    decisions = result.get("decisions", [])
    vendor_emails = result.get("vendor_emails", [])

    first, second, third, fourth = st.columns(4)
    first.metric("Documents", len(documents))
    second.metric("Records", len(records))
    third.metric("Exceptions", len(exceptions))
    fourth.metric("Vendor drafts", len(vendor_emails))

    st.subheader("Review decisions")
    if decisions:
        st.dataframe(
            [
                {
                    "Document": decision.get("document_id"),
                    "Route": decision.get("route"),
                    "Reason": decision.get("reason"),
                    "Amount at risk": decision.get("amount_at_risk"),
                }
                for decision in decisions
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No routing decisions were returned.")

    st.subheader("Exceptions")
    if exceptions:
        for index, exception in enumerate(exceptions, start=1):
            title = f"{exception.get('severity', 'unknown').upper()} | {exception.get('code', 'Unknown issue')}"
            with st.expander(title, expanded=True):
                st.write(exception.get("explanation") or "No explanation was provided.")
                st.json(
                    {
                        "document_id": exception.get("document_id"),
                        "expected": exception.get("expected"),
                        "found": exception.get("found"),
                        "amount_at_risk": exception.get("amount_at_risk"),
                    }
                )
                review_key = f"review-{exception.get('document_id')}"
                current_review = st.session_state.get(review_key)
                if current_review:
                    st.success(f"Human decision recorded: {current_review}")
                else:
                    reason = st.text_input(
                        "Reviewer note (optional)",
                        key=f"reason-{exception.get('document_id')}",
                    )
                    approve, reject, clarify = st.columns(3)
                    review_actions = [
                        (approve, "Approve case", "approve"),
                        (reject, "Reject case", "reject"),
                        (clarify, "Request clarification", "request_clarification"),
                    ]
                    for column, label, decision in review_actions:
                        if column.button(label, key=f"{decision}-{exception.get('document_id')}", use_container_width=True):
                            try:
                                review_response = requests.post(
                                    f"{api_url}/review",
                                    json={
                                        "document_id": exception.get("document_id"),
                                        "decision": decision,
                                        "reason": reason,
                                    },
                                    timeout=30,
                                )
                                review_response.raise_for_status()
                                st.session_state[review_key] = decision.replace("_", " ").title()
                                st.rerun()
                            except requests.RequestException as error:
                                st.error(f"Could not record the review decision: {error}")
    else:
        st.success("No exceptions were detected.")

    st.subheader("Vendor correspondence drafts")
    if vendor_emails:
        for index, email in enumerate(vendor_emails, start=1):
            st.text_area(
                f"Draft {index} (human approval required)",
                email,
                height=260,
                key=f"vendor-email-{index}",
            )
    else:
        st.write("No vendor correspondence drafts were generated.")

    with st.expander("Processed documents"):
        st.json(documents)

    with st.expander("Extracted transaction records"):
        st.json(records)
