# Intelligent Invoice & Expense Reconciliation Agent

A complete capstone starter for mixed-document ingestion, structured extraction, deterministic three-way matching, anomaly checks, plain-language explanations, human approval routing, and vendor email drafting.

## Roshan's ownership: Ingestion Agent
`app/agents/ingestion.py` accepts PDF/image/CSV files, selects text extraction or OCR, extracts tables, classifies the document, computes ingestion confidence, hashes the source for auditability, and emits a standard `IngestedDocument` object.

## Quick start
```bash
cp .env.example .env
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` and call `POST /reconcile` with multiple files.

Tesseract is required for images/scanned PDFs. Docker installs it automatically. Local Ubuntu: `sudo apt-get install tesseract-ocr`. Windows: install Tesseract and set `TESSERACT_CMD` in `.env`.

## Docker
```bash
docker compose up --build
```

## Tests
```bash
pytest -q
```

## Supported inputs
- PDF: native text first, then page-level OCR when text is insufficient
- Images: PNG, JPG, JPEG, TIFF, BMP via Tesseract OCR
- CSV: pandas with delimiter detection and normalized tables

## Pipeline
`Ingestion -> Extraction -> Matching + Anomaly -> Explanation -> HITL Router -> Correspondence`

The default extraction is regex-based so the repository runs without an LLM. Replace `ExtractionAgent` with an Azure OpenAI structured-output implementation later without changing downstream contracts.
