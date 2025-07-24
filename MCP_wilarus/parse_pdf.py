"""Utilities for extracting text from PDF documents."""
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract
from tempfile import TemporaryDirectory


def extract_text_with_ocr(pdf_path: str) -> str:
    """Fallback OCR extraction using Tesseract."""
    text = ""
    with TemporaryDirectory() as tmpdir:
        images = convert_from_path(pdf_path, output_folder=tmpdir)
        for img in images:
            text += pytesseract.image_to_string(img, lang="rus+eng")
    return text


def parse_pdf(pdf_path: str) -> str:
    """Return extracted text from a PDF. Uses text layer if available and
    falls back to OCR when the text layer is empty."""
    text = extract_text(pdf_path)
    if (not text or len(text.strip()) < 50 or
            "docs.yandex.ru" in text or "1/1" in text):
        text = extract_text_with_ocr(pdf_path)
    return text

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: parse_pdf.py <file.pdf>")
    else:
        result = parse_pdf(sys.argv[1])
        print(result)
