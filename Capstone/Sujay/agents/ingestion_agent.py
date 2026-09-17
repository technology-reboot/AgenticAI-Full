"""
Ingestion Agent - Roshan Javvaji

Accepts a mixed folder of PDFs, images and CSVs; routes by type
(text layer PDF, OCR for scans, pandas for CSV) and emits tagged
raw text and tables.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Try to import pytesseract for OCR (alternative to paddle on Python 3.12+)
# Tesseract OCR engine must be installed separately: https://github.com/UB-Mannheim/tesseract/wiki
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# Try to import paddle for OCR/PDF processing
# paddle has limited Python 3.12 compatibility
try:
    import paddle
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class IngestionAgent:
    """
    Ingestion Agent - Roshan Javvaji

    Accepts a mixed folder of PDFs, images and CSVs; routes by type
    (text layer PDF, OCR for scans, pandas for CSV) and emits tagged
    raw text and tables.

    OCR Backends:
    - Primary: paddle (PaddlePaddle) - best compatibility with Python 3.8-3.11
    - Alternative: pytesseract + Tesseract OCR engine - works on Python 3.12+
      Requires: pip install pytesseract && install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
    - Fallback: No OCR - returns basic file metadata
    """

    def __init__(self):
        self.name = "ingestion_agent"
        self.version = "1.0.0"

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file based on its type.

        Args:
            file_path: Path to the file to process

        Returns:
            Dict with processed content and metadata
        """
        path = Path(file_path)
        result = {
            "file_name": path.name,
            "file_type": path.suffix.lower(),
            "content": None,
            "tables": [],
            "metadata": {}
        }

        if path.suffix.lower() == '.pdf':
            content = self._process_pdf(path)
        elif path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            content = self._process_image(path)
        elif path.suffix.lower() == '.csv':
            content = self._process_csv(path)
        else:
            content = {"error": f"Unsupported file type: {path.suffix}"}

        result["content"] = content
        return result

    def _process_pdf(self, path: Path) -> Dict[str, Any]:
        """Process PDF file - text layer or scanned."""
        # In a real implementation, this would use PyPDF2 or pdfplumber
        # For now, return structure
        return {
            "type": "pdf",
            "text": f"PDF content from {path.name}",
            "tables": [],
            "requires_ocr": path.name.lower().startswith('_') or '_scan' in path.name.lower()
        }

    def _process_image(self, path: Path) -> Dict[str, Any]:
        """Process image file using OCR."""
        text = ""
        tables = []

        if PYTESSERACT_AVAILABLE:
            try:
                # Load image with OpenCV and run Tesseract OCR
                import cv2
                img = cv2.imread(str(path))
                if img is not None:
                    # pytesseract can work with numpy arrays directly
                    text = pytesseract.image_to_string(img)
                    # Extract tables (basic) - pytesseract doesn't do table extraction natively
                    # We'll leave tables empty for now; enhance later if needed
                else:
                    text = f"Could not read image: {path.name}"
            except Exception as e:
                text = f"OCR error for {path.name}: {str(e)}"
        else:
            # pytesseract not available - Tesseract OCR engine not installed
            # Install: pip install pytesseract && install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
            text = f"OCR not available for {path.name}. Install Tesseract OCR engine."
            # Also note that paddle is not available (handled elsewhere)

        return {
            "type": "image_ocr",
            "text": text,
            "tables": tables,
            "requires_ocr": True
        }

    def _process_csv(self, path: Path) -> Dict[str, Any]:
        """Process CSV file using pandas."""
        import csv
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            return {
                "type": "csv",
                "headers": rows[0] if rows else [],
                "data": rows[1:] if len(rows) > 1 else [],
                "row_count": len(rows) - 1
            }
        except Exception as e:
            return {"error": str(e)}

    def scan_directory(self, directory: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan a directory for mixed file types and route each.

        Args:
            directory: Path to scan

        Returns:
            Dict mapping file types to processed results
        """
        results = {"pdfs": [], "images": [], "csvs": []}
        dir_path = Path(directory)

        if not dir_path.exists():
            return results

        for file in dir_path.rglob("*"):
            if file.is_file():
                result = self.process_file(str(file))
                file_type = path.splitext(file.name)[1].lower()

                if file_type == '.pdf':
                    results["pdfs"].append(result)
                elif file_type in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                    results["images"].append(result)
                elif file_type == '.csv':
                    results["csvs"].append(result)

        return results