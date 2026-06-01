"""
Document parser for the AI Interviewer Assistant project.

Supported formats: PDF, DOCX, TXT.
Main entry point: parse_document(file_path: str) -> str
"""

from __future__ import annotations

import os
import re
from pathlib import Path



SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2.

    Notes:
    - Works best on text-based PDFs.
    - Scanned/image-only PDFs usually need OCR, which is outside this task.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        import PyPDF2
    except ImportError as exc:
        raise ImportError("PyPDF2 is required for PDF parsing. Install it with: pip install PyPDF2") from exc

    pages_text: list[str] = []
    with path.open("rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text)
            else:
                pages_text.append(f"\n[Page {page_number}: no extractable text]\n")
    return "\n".join(pages_text)


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file, including paragraphs and tables."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError("python-docx is required for DOCX parsing. Install it with: pip install python-docx") from exc

    document = Document(str(path))
    parts: list[str] = []

    for paragraph in document.paragraphs:
        paragraph_text = paragraph.text.strip()
        if paragraph_text:
            parts.append(paragraph_text)

    # CVs sometimes use tables for layout, so we also parse table cells.
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return "\n".join(parts)


def parse_txt(file_path: str) -> str:
    """Read a TXT file with a few common encodings as fallback."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise UnicodeDecodeError(
        "unknown",
        b"",
        0,
        1,
        f"Could not decode {file_path}. Last error: {last_error}",
    )


def clean_text(text: str) -> str:
    """Clean extracted document text while preserving useful line breaks.

    Cleaning rules:
    - normalize Windows/Mac line endings
    - remove tabs and repeated spaces
    - remove excessive blank lines
    - remove common bullet/control characters while keeping readable punctuation
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")

    # Replace common bullet symbols with a simple dash.
    text = re.sub(r"[•●▪▫◦]", "-", text)

    # Remove non-printable control characters except newlines.
    text = re.sub(r"[^\S\n]+", " ", text)

    # Strip each line and remove lines that become empty later.
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse 3+ blank lines into max 2 blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse repeated spaces inside lines.
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def parse_document(file_path: str) -> str:
    """Detect file extension and return cleaned text from PDF, DOCX or TXT."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        raw_text = parse_pdf(file_path)
    elif ext == ".docx":
        raw_text = parse_docx(file_path)
    elif ext == ".txt":
        raw_text = parse_txt(file_path)
    else:
        raise ValueError(
            f"Unsupported format: {ext}. Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    return clean_text(raw_text)


def parse_folder(folder_path: str) -> dict[str, str]:
    """Parse all supported documents from a folder and return {filename: text}."""
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    parsed: dict[str, str] = {}
    for file_path in sorted(folder.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            parsed[file_path.name] = parse_document(str(file_path))
    return parsed


if __name__ == "__main__":
    # Small manual test from the repo root:
    # python src/parser.py data/job_descriptions/python_developer_01.txt
    import sys

    # if len(sys.argv) != 2:
    #     print("Usage: python src/parser.py <path_to_document>")
    #     raise SystemExit(1)

    # print(parse_document(sys.argv[1])[:2000])
    from datasets import load_dataset

    jobs = load_dataset("batuhanmtl/job-skill-set")
    print(jobs)
    print(jobs["train"][0])
