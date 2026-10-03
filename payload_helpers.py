#!/usr/bin/env python3

"""Small, copy-paste-friendly helpers for CTF exploit payloads."""

import base64
import io
import json
import secrets
import string
import tarfile
import time
import zipfile


def to_bytes(data):
    """Convert common values to bytes."""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode()
    return json.dumps(data).encode()


def random_string(length=12, alphabet=string.ascii_letters + string.digits):
    """Return a random value suitable for usernames, passwords, and filenames."""
    return "".join(secrets.choice(alphabet) for _ in range(length))


def b64encode(data):
    """Return standard base64 text."""
    return base64.b64encode(to_bytes(data)).decode()


def b64decode(data):
    """Decode standard base64 text or bytes."""
    return base64.b64decode(to_bytes(data), validate=True)


def make_tar(files=None, symlinks=None, gzip=False):
    """
    Build a TAR archive in memory.

    files and symlinks map archive paths to contents and link targets:
        make_tar(
            files={"main.typ": '#include "files/secret"'},
            symlinks={"files/secret": "/path/to/secret"},
        )
    """
    output = io.BytesIO()
    mode = "w:gz" if gzip else "w"

    with tarfile.open(fileobj=output, mode=mode) as archive:
        for path, content in (files or {}).items():
            content = to_bytes(content)
            entry = tarfile.TarInfo(str(path))
            entry.size = len(content)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(content))

        for path, target in (symlinks or {}).items():
            entry = tarfile.TarInfo(str(path))
            entry.type = tarfile.SYMTYPE
            entry.linkname = str(target)
            entry.mode = 0o777
            archive.addfile(entry)

    return output.getvalue()


def make_zip(files=None, symlinks=None):
    """Build a ZIP archive in memory, optionally with Unix symlink entries."""
    output = io.BytesIO()

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in (files or {}).items():
            archive.writestr(str(path), to_bytes(content))

        for path, target in (symlinks or {}).items():
            entry = zipfile.ZipInfo(str(path))
            entry.create_system = 3
            entry.external_attr = (0o120777 << 16)
            archive.writestr(entry, str(target).encode())

    return output.getvalue()


def upload_file(filename, data, content_type="application/octet-stream"):
    """Create a requests-compatible multipart file tuple."""
    return filename, to_bytes(data), content_type


def pdf_to_text(data):
    """Extract text from PDF bytes. Requires the optional pypdf package."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("pdf_to_text() requires: pip install pypdf") from error

    reader = PdfReader(io.BytesIO(to_bytes(data)))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def find_values(data, key):
    """Recursively return every value stored under key in JSON-like data."""
    found = []
    if isinstance(data, dict):
        for current_key, value in data.items():
            if current_key == key:
                found.append(value)
            found.extend(find_values(value, key))
    elif isinstance(data, list):
        for value in data:
            found.extend(find_values(value, key))
    return found


def poll(fetch, ready, timeout=15.0, interval=0.5):
    """Call fetch() until ready(result) is true or timeout expires."""
    deadline = time.monotonic() + timeout
    while True:
        result = fetch()
        if ready(result):
            return result
        if time.monotonic() >= deadline:
            raise TimeoutError("result was not ready before the timeout")
        time.sleep(interval)


if __name__ == "__main__":
    print("Import or copy the helpers you need; this file is not an exploit.")
