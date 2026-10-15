"""Encoding, random-value, JSON-search, and multipart helpers."""

import base64
import json
import secrets
import string
from urllib.parse import quote, quote_plus, unquote, urlencode


def to_bytes(data):
    """Convert common Python values to bytes."""
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()
    if isinstance(data, str):
        return data.encode()
    return json.dumps(data, separators=(",", ":")).encode()


def random_string(length=12, alphabet=string.ascii_letters + string.digits):
    """Return a random value suitable for names, passwords, and filenames."""
    return "".join(secrets.choice(alphabet) for _ in range(length))


def b64encode(data, *, urlsafe=False, strip_padding=False):
    """Return standard or URL-safe base64 text."""
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    encoded = encoder(to_bytes(data)).decode()
    return encoded.rstrip("=") if strip_padding else encoded


def b64decode(data, *, urlsafe=False):
    """Decode standard or URL-safe base64 text, restoring omitted padding."""
    raw = to_bytes(data)
    raw += b"=" * (-len(raw) % 4)
    if urlsafe:
        return base64.urlsafe_b64decode(raw)
    return base64.b64decode(raw, validate=True)


def hexencode(data):
    """Return lowercase hexadecimal text."""
    return to_bytes(data).hex()


def hexdecode(data):
    """Decode hexadecimal text or ASCII bytes."""
    return bytes.fromhex(to_bytes(data).decode())


def urlencode_form(fields, *, doseq=True):
    """Encode fields as an application/x-www-form-urlencoded string."""
    return urlencode(fields, doseq=doseq)


def urlquote(value, *, path=False):
    """Quote one URL value; use path=True to keep slash separators."""
    return quote(str(value), safe="/" if path else "")


def urlquote_plus(value):
    """Quote one HTML-form value, replacing spaces with plus signs."""
    return quote_plus(str(value), safe="")


def urlunquote(value):
    """Decode percent escapes in one URL value."""
    return unquote(str(value))


def upload_file(filename, data, content_type="application/octet-stream"):
    """Create a requests-compatible multipart file tuple."""
    return filename, to_bytes(data), content_type


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
