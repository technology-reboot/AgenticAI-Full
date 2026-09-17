from pathlib import Path
import json
import shutil
import tempfile
import uuid
from datetime import datetime

import streamlit as st

from app.pipeline import ReconciliationPipeline
from app.services.file_utils import SUPPORTED


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Intelligent Invoice Reconciliation",
    page_icon="🧾",
    layout="wide",
)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_value(value, default=None):
    """
    Supports Pydantic objects such as:
    {"value": "...", "confidence": 0.86}
    """
    if value is None:
        return default

    if isinstance(value, dict):
        return value.get("value", default)

    if hasattr(value, "value"):
        return value.value

    return value


def get_confidence(value, default=0):
    if value is None:
        return default

    if isinstance(value, dict):
        return value.get("confidence", default)

    if hasattr(value, "confidence"):
        return value.confidence

    return default


def model_to_dict(value):
    """
    Converts Pydantic models or normal dictionaries to dictionaries.
    """
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return value

    return value


def save_uploaded_files(uploaded_files):
    """
    Saves Streamlit UploadedFile objects into a temporary run directory.
    """
    run_dir = Path(tempfile.mkdtemp(prefix="reconciliation_"))
    paths = []

    for uploaded_file in uploaded_files:
        filename = Path(uploaded_file.name).name
        suffix = Path(filename).suffix.lower()

        if suffix not in SUPPORTED:
            raise ValueError(
                f"Unsupported file type: {filename}. "
                f"Supported types: {', '.join(sorted(SUPPORTED))}"
            )

        target = run_dir / filename
        target.write_bytes(uploaded_file.getbuffer())
        paths.append(target)

    return run_dir, paths


def serialize_result(result):
    """
    Converts the complete pipeline result into JSON-compatible data.
    """
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    if isinstance(result, dict):
        return result

    return {}


def severity_color(severity):
    severity = str(severity or "").lower()

    if severity == "high":
        return "🔴"
    if severity == "medium":
        return "🟠"
    if severity == "low":
        return "🟡"

    return "⚪"


def exception_document_id(exception):
    if isinstance(exception, dict):
        return exception.get("document_id")

    return getattr(exception, "document_id", None)


def exception_code(exception):
    if isinstance(exception, dict):
        return exception.get("code")

    return getattr(exception, "code", "UNKNOWN")


def get_exception_value(exception, field, default=None):
    if isinstance(exception, dict):
        return exception.get(field, default)

    return getattr(exception, field, default)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "reconciliation_result" not in st.session_state:
    st.session_state.reconciliation_result = None

if "human_decisions" not in st.session_state:
    st.session_state.human_decisions = {}

if "run_id" not in st.session_state:
    st.session_state.run_id = None


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🧾 Intelligent Invoice & Expense Reconciliation")
st.caption(
    "Upload business documents, run three-way matching, and resolve exceptions "
    "through human approval."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("Supported Files")

    st.write(
        "Upload one or more invoices, purchase orders, receipts, "
        "or bank statements."
    )

    st.code(", ".join(sorted(SUPPORTED)))

    st.divider()

    if st.session_state.reconciliation_result is not None:
        if st.button("Clear Current Run", use_container_width=True):
            st.session_state.reconciliation_result = None
            st.session_state.human_decisions = {}
            st.session_state.run_id = None
            st.rerun()


# ---------------------------------------------------------
# File upload
# ---------------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload documents",
    type=[
        suffix.replace(".", "")
        for suffix in sorted(SUPPORTED)
        if suffix.startswith(".")
    ],
    accept_multiple_files=True,
    help="You can upload invoices, purchase orders, receipts, and CSV bank statements.",
)


if uploaded_files:
    st.write(f"**{len(uploaded_files)} file(s) selected**")

    file_data = []

    for uploaded_file in uploaded_files:
        file_data.append(
            {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type or "unknown",
            }
        )

    st.dataframe(
        file_data,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# Run reconciliation
# ---------------------------------------------------------

if st.button(
    "Run Reconciliation",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_files,
):
    run_dir = None

    try:
        with st.spinner("Ingesting documents and running reconciliation..."):
            run_dir, paths = save_uploaded_files(uploaded_files)

            pipeline = ReconciliationPipeline()
            result = pipeline.run(paths)

            st.session_state.reconciliation_result = result
            st.session_state.human_decisions = {}
            st.session_state.run_id = str(uuid.uuid4())

        st.success("Reconciliation completed successfully.")

    except Exception as exc:
        st.error(f"Reconciliation failed: {exc}")

    finally:
        if run_dir:
            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

result = st.session_state.reconciliation_result

if result is None:
    st.info("Upload your documents and click **Run Reconciliation**.")
    st.stop()


result_data = serialize_result(result)

documents = result_data.get("documents", [])
records = result_data.get("records", [])
exceptions = result_data.get("exceptions", [])
decisions = result_data.get("decisions", [])
vendor_emails = result_data.get("vendor_emails", [])


# ---------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------

total_documents = len(documents)
total_records = len(records)
total_exceptions = len(exceptions)

high_exceptions = sum(
    1
    for exception in exceptions
    if str(get_exception_value(exception, "severity", "")).lower() == "high"
)

human_review_count = sum(
    1
    for decision in decisions
    if str(get_exception_value(decision, "route", "")).lower()
    == "human_review"
)

approved_count = sum(
    1
    for decision in decisions
    if str(get_exception_value(decision, "route", "")).lower()
    in {"approved", "auto_approved"}
)


col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Documents", total_documents)

with col2:
    st.metric("Extracted Records", total_records)

with col3:
    st.metric("Exceptions", total_exceptions)

with col4:
    st.metric("High Severity", high_exceptions)

with col5:
    st.metric("Human Review", human_review_count)


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab_exceptions, tab_documents, tab_records, tab_emails, tab_json = st.tabs(
    [
        "⚠️ Exceptions & Review",
        "📄 Documents",
        "🔍 Extracted Records",
        "✉️ Vendor Emails",
        "📦 Raw JSON",
    ]
)


# ---------------------------------------------------------
# Human-in-the-loop exception review
# ---------------------------------------------------------

with tab_exceptions:
    st.subheader("Exceptions Requiring Review")

    if not exceptions:
        st.success("No exceptions detected. All documents passed reconciliation.")
    else:
        for index, exception in enumerate(exceptions):
            code = exception_code(exception)
            severity = get_exception_value(exception, "severity", "unknown")
            document_id = exception_document_id(exception)
            explanation = get_exception_value(
                exception,
                "explanation",
                "No explanation provided.",
            )
            expected = get_exception_value(exception, "expected")
            found = get_exception_value(exception, "found")
            amount_at_risk = get_exception_value(exception, "amount_at_risk")

            matching_record = next(
                (
                    record
                    for record in records
                    if record.get("document_id") == document_id
                ),
                {},
            )

            document_type = matching_record.get("document_type", "unknown")
            invoice_number = get_value(
                matching_record.get("invoice_number"),
                "Unknown invoice",
            )
            vendor_name = get_value(
                matching_record.get("vendor_name"),
                "Unknown vendor",
            )

            review_key = f"{document_id}-{index}"

            with st.container(border=True):
                st.markdown(
                    f"### {severity_color(severity)} {code} "
                    f"— {str(severity).upper()}"
                )

                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.write(f"**Document type:** {document_type}")

                with info_col2:
                    st.write(f"**Invoice:** {invoice_number}")

                with info_col3:
                    st.write(f"**Vendor:** {vendor_name}")

                if amount_at_risk is not None:
                    st.write(f"**Amount at risk:** `{amount_at_risk}`")

                st.info(explanation)

                if expected is not None or found is not None:
                    comparison_col1, comparison_col2 = st.columns(2)

                    with comparison_col1:
                        st.write("**Expected**")
                        st.code(str(expected))

                    with comparison_col2:
                        st.write("**Found**")
                        st.code(str(found))

                existing_decision = st.session_state.human_decisions.get(
                    review_key
                )

                decision_col1, decision_col2, decision_col3 = st.columns(3)

                with decision_col1:
                    approve_clicked = st.button(
                        "✅ Approve",
                        key=f"approve-{review_key}",
                        use_container_width=True,
                    )

                with decision_col2:
                    reject_clicked = st.button(
                        "❌ Reject",
                        key=f"reject-{review_key}",
                        use_container_width=True,
                    )

                with decision_col3:
                    clarification_clicked = st.button(
                        "✉️ Request Clarification",
                        key=f"clarification-{review_key}",
                        use_container_width=True,
                    )

                if approve_clicked:
                    st.session_state.human_decisions[review_key] = {
                        "document_id": document_id,
                        "exception_code": code,
                        "decision": "approved",
                        "decided_by": "human",
                        "decided_at": datetime.utcnow().isoformat() + "Z",
                    }
                    st.success("Exception approved by human reviewer.")

                elif reject_clicked:
                    st.session_state.human_decisions[review_key] = {
                        "document_id": document_id,
                        "exception_code": code,
                        "decision": "rejected",
                        "decided_by": "human",
                        "decided_at": datetime.utcnow().isoformat() + "Z",
                    }
                    st.warning("Exception rejected. Payment should remain blocked.")

                elif clarification_clicked:
                    st.session_state.human_decisions[review_key] = {
                        "document_id": document_id,
                        "exception_code": code,
                        "decision": "vendor_clarification_required",
                        "decided_by": "human",
                        "decided_at": datetime.utcnow().isoformat() + "Z",
                    }
                    st.info("Vendor clarification requested.")

                if existing_decision:
                    st.write(
                        f"**Current human decision:** "
                        f"`{existing_decision['decision']}`"
                    )


# ---------------------------------------------------------
# Documents tab
# ---------------------------------------------------------

with tab_documents:
    st.subheader("Ingested Documents")

    if documents:
        document_rows = []

        for document in documents:
            document_rows.append(
                {
                    "File": document.get("file_name"),
                    "Type": document.get("document_type"),
                    "Status": document.get("status"),
                    "Extraction Method": document.get("extraction_method"),
                    "Confidence": document.get("confidence"),
                    "Pages": document.get("page_count"),
                    "Error": document.get("error"),
                }
            )

        st.dataframe(
            document_rows,
            use_container_width=True,
            hide_index=True,
        )

        for document in documents:
            with st.expander(
                f"{document.get('file_name', 'Unknown file')} "
                f"— {document.get('status', 'unknown')}"
            ):
                st.write("**Document type:**", document.get("document_type"))
                st.write(
                    "**Extraction method:**",
                    document.get("extraction_method"),
                )
                st.write("**SHA-256:**", document.get("sha256"))
                st.write("**Page count:**", document.get("page_count"))
                st.write("**Confidence:**", document.get("confidence"))

                if document.get("error"):
                    st.error(document["error"])

                if document.get("raw_text"):
                    st.text_area(
                        "Extracted text",
                        document["raw_text"],
                        height=250,
                        key=f"raw-text-{document.get('document_id')}",
                    )


# ---------------------------------------------------------
# Extracted records tab
# ---------------------------------------------------------

with tab_records:
    st.subheader("Structured Extraction Results")

    if not records:
        st.warning("No structured records were extracted.")
    else:
        for record in records:
            document_id = record.get("document_id")
            document_type = record.get("document_type", "unknown")

            with st.expander(
                f"{document_type.title()} "
                f"— {document_id}"
            ):
                overview_col1, overview_col2, overview_col3 = st.columns(3)

                with overview_col1:
                    vendor = get_value(record.get("vendor_name"))
                    st.write("**Vendor**")
                    st.write(vendor or "Not found")

                with overview_col2:
                    invoice_number = get_value(record.get("invoice_number"))
                    st.write("**Invoice number**")
                    st.write(invoice_number or "Not found")

                with overview_col3:
                    po_number = get_value(record.get("po_number"))
                    st.write("**PO number**")
                    st.write(po_number or "Not found")

                amount_col1, amount_col2, amount_col3, amount_col4 = st.columns(4)

                with amount_col1:
                    st.write("**Subtotal**")
                    st.write(get_value(record.get("subtotal"), "Not found"))

                with amount_col2:
                    st.write("**Tax**")
                    st.write(get_value(record.get("tax"), "Not found"))

                with amount_col3:
                    st.write("**Total**")
                    st.write(get_value(record.get("total"), "Not found"))

                with amount_col4:
                    st.write("**Currency**")
                    st.write(get_value(record.get("currency"), "Not found"))

                st.write(
                    "**Overall confidence:**",
                    record.get("overall_confidence", "Not available"),
                )

                line_items = record.get("line_items") or []

                if line_items:
                    st.write("**Line items**")
                    st.json(line_items)

                with st.expander("Show field confidence"):
                    confidence_fields = {}

                    for field_name, field_value in record.items():
                        if isinstance(field_value, dict):
                            if "confidence" in field_value:
                                confidence_fields[field_name] = {
                                    "value": field_value.get("value"),
                                    "confidence": field_value.get(
                                        "confidence"
                                    ),
                                }

                    st.json(confidence_fields)


# ---------------------------------------------------------
# Vendor email tab
# ---------------------------------------------------------

with tab_emails:
    st.subheader("Drafted Vendor Follow-up Emails")

    if not vendor_emails:
        st.info("No vendor follow-up emails were generated.")
    else:
        for index, email in enumerate(vendor_emails, start=1):
            with st.expander(f"Vendor Email {index}", expanded=True):
                st.text_area(
                    "Email draft",
                    email,
                    height=300,
                    key=f"vendor-email-{index}",
                )

                st.download_button(
                    "Download Email",
                    data=email,
                    file_name=f"vendor_followup_{index}.txt",
                    mime="text/plain",
                    key=f"download-email-{index}",
                )


# ---------------------------------------------------------
# Raw JSON tab
# ---------------------------------------------------------

with tab_json:
    st.subheader("Reconciliation JSON")

    json_text = json.dumps(result_data, indent=2, default=str)

    st.download_button(
        "Download Complete Result",
        data=json_text,
        file_name=f"reconciliation_{st.session_state.run_id or 'result'}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.code(json_text, language="json")


# ---------------------------------------------------------
# Human decisions export
# ---------------------------------------------------------

if st.session_state.human_decisions:
    st.divider()
    st.subheader("Human Review Decisions")

    decisions_data = list(st.session_state.human_decisions.values())

    st.dataframe(
        decisions_data,
        use_container_width=True,
        hide_index=True,
    )

    decisions_json = json.dumps(decisions_data, indent=2)

    st.download_button(
        "Download Human Decisions",
        data=decisions_json,
        file_name="human_review_decisions.json",
        mime="application/json",
    )
