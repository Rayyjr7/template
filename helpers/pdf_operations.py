"""Small PDF creation, mutation, and parsing helpers."""

import io

from .data_operations import to_bytes


def _escape_pdf_text(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_minimal_pdf(text="CTF payload"):
    """Create a one-page PDF with Helvetica text using only the standard library."""
    content = f"BT /F1 12 Tf 72 720 Td ({_escape_pdf_text(text)}) Tj ET".encode(
        "latin-1", errors="replace"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length "
        + str(len(content)).encode()
        + b" >>\nstream\n"
        + content
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(body)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(output)


def append_pdf_bytes(data, suffix):
    """Append bytes after the PDF EOF marker."""
    return to_bytes(data) + to_bytes(suffix)


def pdf_to_text(data):
    """Extract text from PDF bytes using the optional pypdf dependency."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("pdf_to_text() requires: pip install pypdf") from error

    reader = PdfReader(io.BytesIO(to_bytes(data)))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def pdf_info(data):
    """Return page count and metadata using the optional pypdf dependency."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("pdf_info() requires: pip install pypdf") from error

    reader = PdfReader(io.BytesIO(to_bytes(data)))
    return {
        "pages": len(reader.pages),
        "metadata": dict(reader.metadata or {}),
    }
