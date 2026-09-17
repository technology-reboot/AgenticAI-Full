# Intelligent Invoice & Expense Reconciliation Agent - Capstone Project

## Project Overview
Build an agentic system that ingests invoices, receipts, and bank statements (PDF/image/CSV), performs a three-way match against purchase orders, and flags mismatches, duplicates, and anomalies. The agent should explain each exception in plain language and route uncertain cases to a human for approval.

## Project Structure
```
Capstone project/
├── agents/              # Individual agent implementations
│   ├── ingestion_agent.py    # Roshan Javvaji - PDF/image/CSV routing
│   ├── extraction_agent.py   # Jayashri Sheeli - Pydantic records with confidence
│   ├── matching_agent.py     # Sambhaji S Pandhare - Three-way match, deterministic
│   ├── anomaly_agent.py      # Shivam Thaman - Duplicates, outliers, policy breaches
│   ├── explanation_agent.py  # Sujay Kumar - Plain-language explanations
│   ├── hitl_router.py        # Riya Patil - Auto-clear vs human queue
│   └── correspondence_agent.py  # Toorubatla Upendra - Vendor dispute emails
├── models/              # Pydantic models and schemas
├── data/                # Input test data and samples
├── schemas/             # JSON schemas for data validation
└── main.py              # Entry point and orchestration
```

## Key Components

### 1. Ingestion Agent (Roshan Javvaji)
- Accepts mixed folder of PDFs, images, CSVs
- Routes by type: text layer PDF, OCR for scans, pandas for CSV
- Emits tagged raw text and tables

### 2. Extraction Agent (Jayashri Sheeli)
- Turns messy raw text into strict Pydantic records
- Handles missing fields, varied date formats, mangled OCR tables
- Attaches per-field confidence score

### 3. Matching Agent (Sambhaji S Pandhare)
- Performs three-way match: PO vs Invoice vs Receipt
- Configurable tolerances
- Fuzzy vendor matching
- **Deterministic Python, no LLM** - auditable

### 4. Anomaly Agent (Shivam Thaman)
- Detects duplicate invoices
- Statistical outliers against vendor history
- Policy breaches (above threshold amounts)

### 5. Explanation Agent (Sujay Kumar)
- Turns each exception into plain-language explanation
- Cites actual expected vs. found amounts
- Finance clerk can act on

### 6. HITL Router (Riya Patil)
- Decides auto-clear vs. human queue using confidence, severity, amount at risk
- Builds approval queue and records decisions back into state

### 7. Correspondence Agent (Toorubatla Upendra)
- Drafts professional vendor dispute email citing PO number and specific discrepancy
- **Always a draft for review, never auto-send**

## Learning Takeaways
- Document parsing and OCR
- Structured data extraction from messy inputs
- Entity/transaction matching logic
- Anomaly detection
- Designing human-in-the-loop approval flows