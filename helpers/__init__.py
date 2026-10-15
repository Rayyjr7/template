"""Copy-paste-friendly helpers grouped by payload type."""

from .archive_operations import list_tar, list_zip, make_tar, make_zip
from .data_operations import (
    b64decode,
    b64encode,
    find_values,
    hexdecode,
    hexencode,
    random_string,
    to_bytes,
    upload_file,
    urlencode_form,
    urlquote,
    urlquote_plus,
    urlunquote,
)
from .file_operations import (
    append_bytes,
    chunk_bytes,
    pad_bytes,
    patch_bytes,
    prepend_bytes,
    read_bytes,
    replace_bytes,
    write_bytes,
)
from .pdf_operations import append_pdf_bytes, make_minimal_pdf, pdf_info, pdf_to_text
from .race_operations import poll, race, run_parallel

__all__ = [
    "append_bytes",
    "append_pdf_bytes",
    "b64decode",
    "b64encode",
    "chunk_bytes",
    "find_values",
    "hexdecode",
    "hexencode",
    "list_tar",
    "list_zip",
    "make_minimal_pdf",
    "make_tar",
    "make_zip",
    "pad_bytes",
    "patch_bytes",
    "pdf_info",
    "pdf_to_text",
    "poll",
    "prepend_bytes",
    "race",
    "random_string",
    "read_bytes",
    "replace_bytes",
    "run_parallel",
    "to_bytes",
    "upload_file",
    "urlencode_form",
    "urlquote",
    "urlquote_plus",
    "urlunquote",
    "write_bytes",
]
