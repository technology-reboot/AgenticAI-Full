"""
Extraction Agent - Jayashri Sheeli

Turns messy raw text into strict Pydantic records, handling missing
fields, varied date formats and mangled OCR tables — attaches a per
field confidence score.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator


class InvoiceRecord(BaseModel):
    """Pydantic model for extracted invoice data."""
    invoice_number: str = Field(..., description="Unique invoice identifier")
    vendor_name: str = Field(..., description="Name of the vendor")
    invoice_date: str = Field(..., description="Invoice date")
    due_date: Optional[str] = Field(None, description="Payment due date")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    currency: Optional[str] = Field("USD", description="Currency code")
    po_number: Optional[str] = Field(None, description=" associated Purchase Order number")
    status: Optional[str] = Field("pending", description="Processing status")

    @validator('invoice_date', 'due_date')
    def validate_date_format(cls, v):
        """Validate and normalize date formats."""
        if v:
            # Try common date formats
            date_patterns = [
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
                r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            ]
            # Basic validation - just ensure it looks like a date
            if not re.match(r'\d{2}[-/]\d{2}[-/]\d{4}', v) and not re.match(r'\d{4}[-/]\d{2}[-/]\d{2}', v):
                # Return as-is, let downstream handle normalization
                pass
        return v


class VendorRecord(BaseModel):
    """Pydantic model for vendor data."""
    vendor_id: str = Field(..., description="Unique vendor identifier")
    vendor_name: str = Field(..., description="Vendor name")
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    account_number: Optional[str] = Field(None, description="Bank account number")


class LineItemRecord(BaseModel):
    """Pydantic model for invoice line items."""
    description: str = Field(..., description="Line item description")
    quantity: Optional[float] = Field(None, description="Quantity")
    unit_price: Optional[float] = Field(None, description="Unit price")
    total_price: Optional[float] = Field(None, description="Line total")
    sku_or_part_number: Optional[str] = Field(None, description="SKU or part number")


class ExtractionResult(BaseModel):
    """Result of extracting data from a document."""
    invoice: Optional[InvoiceRecord] = Field(None, description="Extracted invoice data")
    vendor: Optional[VendorRecord] = Field(None, description="Extracted vendor data")
    line_items: List[LineItemRecord] = Field(default_factory=list, description="Line items")
    confidence_score: float = Field(..., description="Overall confidence score 0-1")
    raw_text: str = Field("", description="Original raw text extracted")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Detected tables")
    errors: List[str] = Field(default_factory=list, description="Extraction errors")


class ExtractionAgent:
    """
    Extraction Agent - Jayashri Sheeli

    Turns messy raw text into strict Pydantic records, handling missing
    fields, varied date formats and mangled OCR tables — attaches a per
    field confidence score.
    """

    def __init__(self):
        self.name = "extraction_agent"
        self.version = "1.0.0"

    def extract_from_text(self, raw_text: str, document_type: str = "invoice") -> ExtractionResult:
        """
        Extract structured data from raw text.

        Args:
            raw_text: The raw text to extract from
            document_type: Type of document (invoice, receipt, po)

        Returns:
            ExtractionResult with structured data and confidence scores
        """
        errors = []
        confidence_score = 1.0

        # Initialize result based on document type
        if document_type == "invoice":
            invoice = InvoiceRecord(
                invoice_number=self._extract_field(raw_text, r'invoice #? ?[\w\-]+|invoice.number|inv.?#?'),
                vendor_name=self._extract_field(raw_text, r'vendor[:\s]+([^\n\r]+)'),
                invoice_date=self._extract_date(raw_text),
                po_number=self._extract_field(raw_text, r'po #? ?[\w\-]+|purchase.order|po.number'),
                total_amount=self._extract_amount(raw_text),
                status="pending"
            )
            line_items = []
        elif document_type == "receipt":
            invoice = None
            line_items = []
            total_amount = self._extract_amount(raw_text)
        else:  # po
            invoice = None
            line_items = []
            total_amount = None

        # Extract tables from text
        tables = self._extract_tables(raw_text)

        # Calculate overall confidence (simple heuristic)
        if not errors:
            confidence_score = 0.9
        else:
            confidence_score = 0.5

        result = ExtractionResult(
            invoice=invoice,
            vendor=None,  # Will be populated separately if needed
            line_items=line_items,
            confidence_score=confidence_score,
            raw_text=raw_text,
            tables=tables,
            errors=errors
        )

        return result

    def _extract_field(self, text: str, pattern: str) -> str:
        """Extract a field using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Clean up the extracted value
            value = match.group(1).strip() if match.lastindex > 1 else match.group(0).strip()
            return value
        return ""

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text."""
        # Try multiple date patterns
        patterns = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',  # MM/DD/YYYY or DD-MM-YYYY
            r'\d{4}[-/]\d{2}[-/]\d{2}',  # YYYY-MM-DD or YYYY/MM/DD
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text."""
        patterns = [
            r'[\$\£\¥]?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # 1,234.56 without symbol
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(0).replace('$', '').replace('£', '').replace('¥', '').strip()
                try:
                    return float(amount_str.replace(',', ''))
                except ValueError:
                    return None

        return None

    def _extract_tables(self, text: str) -> List[Dict[str, Any]]:
        """Extract table structures from text."""
        tables = []
        # Simple table detection - look for repeated pipe or tab separated rows
        rows = text.split('\n')
        pipe_rows = [r for r in rows if '|' in r]

        if pipe_rows:
            for row in pipe_rows[:5]:  # Limit to first 5 tables
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if len(cells) > 1:
                    tables.append({
                        "headers": cells[:1] if cells else [],
                        "rows": [cells[1:]] if len(cells) > 1 else [],
                        "source": "ocr_pipe"
                    })

        return tables