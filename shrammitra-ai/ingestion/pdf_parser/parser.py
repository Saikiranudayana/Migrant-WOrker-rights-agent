"""
PDF parser for government labour documents.

Extracts text from PDF circulars, notifications, and scheme documents
from Karnataka Labour Department and Ministry of Labour portals.

Uses pdfplumber (more accurate for government PDFs with tables)
with PyPDF as fallback.
"""
from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pdfplumber
import structlog
from pypdf import PdfReader

logger = structlog.get_logger(__name__)


@dataclass
class ParsedDocument:
    """Extracted document content from a PDF."""
    title: str
    content: str
    page_count: int
    source_url: str
    source_type: str = "pdf"
    language: str = "en"
    act_name: Optional[str] = None
    doc_hash: str = ""

    def __post_init__(self) -> None:
        self.doc_hash = hashlib.sha256(self.content.encode()).hexdigest()


class PDFParser:
    """
    Parse government labour PDFs into clean text.

    Features:
    - Multi-page extraction
    - Table text extraction
    - Header/footer removal
    - Language detection per document
    - Deduplication via content hash
    """

    def parse_bytes(self, pdf_bytes: bytes, source_url: str, title: str = "") -> ParsedDocument:
        """Parse PDF from raw bytes."""
        content = self._extract_with_pdfplumber(pdf_bytes)
        if not content or len(content) < 100:
            # Fallback to PyPDF
            content = self._extract_with_pypdf(pdf_bytes)

        content = self._clean_text(content)

        # Detect act name from title or content
        act_name = self._extract_act_name(title + " " + content[:500])

        return ParsedDocument(
            title=title or self._extract_title_from_content(content),
            content=content,
            page_count=self._count_pages(pdf_bytes),
            source_url=source_url,
            act_name=act_name,
        )

    def parse_file(self, file_path: Path, source_url: str) -> ParsedDocument:
        """Parse PDF from file path."""
        pdf_bytes = file_path.read_bytes()
        return self.parse_bytes(pdf_bytes, source_url, title=file_path.stem)

    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> str:
        """Extract text using pdfplumber (best for tables and complex layouts)."""
        texts = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text(
                        x_tolerance=3,
                        y_tolerance=3,
                        layout=True,
                    )
                    if page_text:
                        texts.append(page_text)
        except Exception as exc:
            logger.debug("pdfplumber_failed", error=str(exc))
        return "\n\n".join(texts)

    def _extract_with_pypdf(self, pdf_bytes: bytes) -> str:
        """Fallback text extraction using PyPDF."""
        texts = []
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
        except Exception as exc:
            logger.debug("pypdf_failed", error=str(exc))
        return "\n\n".join(texts)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text: normalize whitespace, remove noise."""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        # Remove common PDF artifacts
        text = re.sub(r"\x00", "", text)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)  # Standalone page numbers
        # Remove very short lines that are likely headers/footers
        lines = text.split("\n")
        cleaned_lines = [
            line for line in lines
            if len(line.strip()) > 3 or line.strip() == ""
        ]
        return "\n".join(cleaned_lines).strip()

    def _extract_title_from_content(self, content: str) -> str:
        """Extract a likely title from the first few lines of content."""
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            # Take the first non-trivial line as title
            for line in lines[:5]:
                if len(line) > 10:
                    return line[:256]
        return "Untitled Document"

    def _extract_act_name(self, text: str) -> Optional[str]:
        """Extract act/regulation name from text."""
        act_patterns = [
            r"(Payment of Wages Act[,\s]*\d{4})",
            r"(Minimum Wages Act[,\s]*\d{4})",
            r"(Employees.*Provident Fund.*Act[,\s]*\d{4})",
            r"(ESI Act[,\s]*\d{4})",
            r"(Factories Act[,\s]*\d{4})",
            r"(Building.*Construction Workers.*Act[,\s]*\d{4})",
            r"(Inter-State Migrant Workmen.*Act[,\s]*\d{4})",
            r"(Karnataka Shops.*Establishments Act[,\s]*\d{4})",
            r"(Contract Labour.*Act[,\s]*\d{4})",
            r"(Maternity Benefit Act[,\s]*\d{4})",
            r"(Workmen.*Compensation Act[,\s]*\d{4})",
        ]
        for pattern in act_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _count_pages(self, pdf_bytes: bytes) -> int:
        """Count pages in the PDF."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            return len(reader.pages)
        except Exception:
            return 0
