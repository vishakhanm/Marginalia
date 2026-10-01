import io
import pytest
import pandas as pd
from docx import Document

from app.utils.parsers import parse_txt, parse_csv, parse_docx, parse_file


def test_parse_txt():
    content = b"Hello world.\nSecond line."
    result = parse_txt(content)
    assert "Hello world." in result
    assert "Second line." in result


def test_parse_csv():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    result = parse_csv(buffer.getvalue())
    assert "name: Alice" in result
    assert "age: 30" in result


def test_parse_docx():
    doc = Document()
    doc.add_paragraph("This is a test paragraph.")
    buffer = io.BytesIO()
    doc.save(buffer)
    result = parse_docx(buffer.getvalue())
    assert "This is a test paragraph." in result


def test_parse_file_dispatches_by_extension():
    content = b"plain text content"
    result = parse_file("notes.txt", content)
    assert result == "plain text content"


def test_parse_file_unsupported_extension():
    with pytest.raises(ValueError):
        parse_file("archive.zip", b"binary data")