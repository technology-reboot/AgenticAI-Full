"""
Main orchestrator for the Intelligent Invoice & Expense Reconciliation Agent.

This project automates transaction reconciliation by:
1. Ingesting invoices, receipts, and bank statements (PDF/image/CSV)
2. Extracting structured data using Pydantic models
3. Performing three-way match (PO, Invoice, Receipt) deterministically
4. Detecting anomalies (duplicates, outliers, policy breaches)
5. Generating plain-language explanations for finance clerks
6. Routing to human-in-the-loop for approval when needed
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.ingestion_agent import IngestionAgent
from agents.extraction_agent import ExtractionAgent
from agents.matching_agent import MatchingAgent
from agents.anomaly_agent import AnomalyAgent
from agents.explanation_agent import ExplanationAgent
from agents.hitl_router import HITLRouter
from agents.correspondence_agent import CorrespondenceAgent


def load_sample_data() -> Dict[str, Any]:
    """Load sample test data from the data directory."""
    data_dir = PROJECT_ROOT / "data"
    samples = {}

    if data_dir.exists():
        # Load CSV files (for ingestion agent - raw text)
        for f in sorted(data_dir.glob("*.csv")):
            try:
                samples[f.name] = f.read_text(encoding='utf-8')
            except Exception:
                pass

        # Load JSON files (for extraction and anomaly agents)
        for f in sorted(data_dir.glob("*.json")):
            try:
                text = f.read_text(encoding='utf-8')
                # Try to parse and categorize
                import json as _json
                try:
                    parsed = _json.loads(text)
                    # Check what type of JSON this is
                    if 'invoices' in parsed and isinstance(parsed['invoices'], list):
                        samples['extracted_invoices_json'] = parsed
                    elif 'vendor_history' in parsed and isinstance(parsed['vendor_history'], dict):
                        samples['vendor_history_json'] = parsed
                    else:
                        samples[f.name] = text
                except _json.JSONDecodeError:
                    samples[f.name] = text
            except Exception:
                pass

    return samples


def main():
    """Main entry point for the capstone project."""
    print("=" * 70)
    print("Intelligent Invoice & Expense Reconciliation Agent")
    print("=" * 70)

    # Initialize all agents
    agents = {
        "ingestion": IngestionAgent(),
        "extraction": ExtractionAgent(),
        "matching": MatchingAgent(),
        "anomaly": AnomalyAgent(),
        "explanation": ExplanationAgent(),
        "hitl_router": HITLRouter(),
        "correspondence": CorrespondenceAgent(),
    }

    # Load sample data
    samples = load_sample_data()
    print(f"Loaded {len(samples)} sample data files")

    # Example workflow demonstration
    print("\n--- Demo: Processing a sample invoice ---")

    # In a real scenario, this would process actual files
    # For now, we'll show the architecture

    print("\n1. Ingestion Agent: Routes files by type")
    print("   - PDF (text layer) -> direct text extraction")
    print("   - Scanned PDF/image -> OCR processing")
    print("   - CSV -> pandas dataframe parsing")

    print("\n2. Extraction Agent: Structured data extraction")
    print("   - Converts messy raw text -> Pydantic records")
    print("   - Handles: missing fields, varied date formats, mangled OCR tables")
    print("   - Attaches per-field confidence score")

    print("\n3. Matching Agent: Three-way match (deterministic Python)")
    print("   - Match: Purchase Order × Invoice × Receipt")
    print("   - Configurable tolerances for amounts")
    print("   - Fuzzy vendor matching")
    print("   - No LLM -> fully auditable")

    print("\n4. Anomaly Agent: Detect issues")
    print("   - Duplicate invoices")
    print("   - Statistical outliers vs vendor history")
    print("   - Policy breaches (amount thresholds)")

    print("\n5. Explanation Agent: Plain-language explanations")
    print("   - Each exception -> actionable explanation")
    print("   - Cites: expected amount vs. found amount")
    print("   - Finance clerk can act immediately")

    print("\n6. HITL Router: Human decision queue")
    print("   - Factors: confidence, severity, amount at risk")
    print("   - Outcomes: auto-clear -> human queue -> reject")
    print("   - Records decisions back into state")

    print("\n7. Correspondence Agent: Vendor dispute emails")
    print("   - Drafts professional email citing PO number")
    print("   - Specific discrepancy details")
    print("   - **Always draft ->never auto-send**")

    print("\n" + "=" * 70)
    print("Project ready for processing actual invoice data")
    print("=" * 70)


if __name__ == "__main__":
    main()