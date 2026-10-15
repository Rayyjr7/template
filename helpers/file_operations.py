"""Byte-level helpers for constructing and modifying payload files."""

from pathlib import Path

from .data_operations import to_bytes


def read_bytes(path):
    """Read an entire file as bytes."""
    return Path(path).read_bytes()


def write_bytes(path, data, *, create_parents=False):
    """Write bytes and return the resulting Path."""
    destination = Path(path)
    if create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(to_bytes(data))
    return destination


def patch_bytes(data, offset, patch, *, pad_byte=b"\x00"):
    """Overwrite bytes at offset, extending the input with pad_byte if needed."""
    if offset < 0:
        raise ValueError("offset must be non-negative")

    original = bytearray(to_bytes(data))
    replacement = to_bytes(patch)
    padding = to_bytes(pad_byte)
    if len(padding) != 1:
        raise ValueError("pad_byte must contain exactly one byte")

    if offset > len(original):
        original.extend(padding * (offset - len(original)))

    end = offset + len(replacement)
    if end > len(original):
        original.extend(padding * (end - len(original)))
    original[offset:end] = replacement
    return bytes(original)


def replace_bytes(data, old, new, *, count=-1, require_match=True):
    """Replace byte sequences and optionally fail when old is absent."""
    raw = to_bytes(data)
    needle = to_bytes(old)
    if require_match and needle not in raw:
        raise ValueError("byte sequence was not found")
    return raw.replace(needle, to_bytes(new), count)


def prepend_bytes(data, prefix):
    """Prepend arbitrary bytes."""
    return to_bytes(prefix) + to_bytes(data)


def append_bytes(data, suffix):
    """Append arbitrary bytes."""
    return to_bytes(data) + to_bytes(suffix)


def pad_bytes(data, size, *, pad_byte=b"\x00", left=False):
    """Pad to at least size bytes without truncating longer input."""
    raw = to_bytes(data)
    padding = to_bytes(pad_byte)
    if len(padding) != 1:
        raise ValueError("pad_byte must contain exactly one byte")
    missing = max(0, size - len(raw))
    return padding * missing + raw if left else raw + padding * missing


def chunk_bytes(data, size):
    """Split bytes into chunks of at most size bytes."""
    if size <= 0:
        raise ValueError("size must be positive")
    raw = to_bytes(data)
    return [raw[offset : offset + size] for offset in range(0, len(raw), size)]
