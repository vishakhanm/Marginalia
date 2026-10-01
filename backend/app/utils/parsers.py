"""
File parsers — each function takes raw file bytes and returns extracted
plain text. Kept format-specific and dumb on purpose: no chunking or
cleanup logic here, just "get the text out."
"""

import io
import pandas as pd
from pypdf import PdfReader
from docx import Document


def parse_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def parse_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def parse_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()


def parse_csv(content: bytes) -> str:
    df = pd.read_csv(io.BytesIO(content))
    return _dataframe_to_text(df)


def parse_xlsx(content: bytes) -> str:
    excel_file = pd.ExcelFile(io.BytesIO(content))
    sections = []
    for sheet_name in excel_file.sheet_names:
        df = excel_file.parse(sheet_name)
        sections.append(f"Sheet: {sheet_name}\n{_dataframe_to_text(df)}")
    return "\n\n".join(sections).strip()


def _dataframe_to_text(df: pd.DataFrame) -> str:
    """
    Convert each row into a readable 'column: value' line rather than a raw
    table dump — this reads much better once it's embedded and retrieved
    as a chunk of context for the LLM.
    """
    lines = []
    for _, row in df.iterrows():
        line = ", ".join(f"{col}: {row[col]}" for col in df.columns)
        lines.append(line)
    return "\n".join(lines)


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}


def parse_file(filename: str, content: bytes) -> str:
    """Dispatch to the correct parser based on file extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == ".pdf":
        return parse_pdf(content)
    elif ext == ".docx":
        return parse_docx(content)
    elif ext == ".txt":
        return parse_txt(content)
    elif ext == ".csv":
        return parse_csv(content)
    elif ext == ".xlsx":
        return parse_xlsx(content)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )