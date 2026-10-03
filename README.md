# ECSC attack/defence exploit template

## Setup

Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Set the service at the top of `exploit_template.py`:

```python
SERVICE_NAME = "fireworx"
SERVICE_PORT = 8080
```

## Functions you will use

### `exploit_one(target_ip, flag_id)`

This is the main function you edit. It is called once for every flag ID that
belongs to the supplied target IP.

```python
def exploit_one(target_ip, flag_id):
    with HTTPClient(target_ip, SERVICE_PORT) as http:
        response = http.get(f"/api/item/{flag_id}")
        ensure_status(response, 200)
        write_output(response)
```

### `HTTPClient`

Use this for REST APIs and other HTTP services. It uses a persistent
`requests.Session`, so cookies and login state survive between requests.

```python
with HTTPClient(target_ip, SERVICE_PORT) as http:
    http.post("/login", json={"username": "admin"})
    response = http.get(f"/api/item/{flag_id}")
```

It supports `get`, `post`, `put`, `patch`, and `delete`. Normal `requests`
arguments such as `json=`, `data=`, `files=`, `headers=`, and `params=` work.

### `TCPClient`

Use this for menu-based or other raw TCP services:

```python
def exploit_one(target_ip, flag_id):
    with TCPClient(target_ip, SERVICE_PORT) as io:
        io.sendlineafter(b"ID: ", flag_id)
        write_output(io.recvall())
```

### `write_output(data)`

Writes a `requests.Response`, string, or bytes to stdout and flushes it. Use it
for responses that may contain flags. External tooling handles flag extraction.

### `ensure_status(response, ...)`

Optionally require an expected HTTP status:

```python
ensure_status(response, 200, 302)
```

### Flag IDs

`exploit()` prepares two variables before calling `exploit_one()`:

```python
flag_ids_raw = get_flag_ids_raw(IP)        # {"655": {"0": "some-id"}}
flag_ids = flatten_flag_ids(flag_ids_raw)  # ["some-id"]
```

Use `flag_ids` for normal iteration. Use `flag_ids_raw` when a challenge needs
the original round or slot keys, such as `flag_ids_raw["655"]["0"]`.

The remaining query, validation, `main`, and orchestration functions normally
do not need editing.

## Run

The script accepts exactly one IPv4 or IPv6 address:

```bash
./exploit_template.py 10.60.2.2
```

Flag IDs are obtained through `ecsc2026ad`, with the official `attack.json`
API as fallback. Set `FLAG_IDS` or `FLAG_IDS_RAW` to bypass automatic queries.

## NOP helper

```bash
./nop_flag_ids.py fireworx
```

This prints NOP's IP and current flag IDs for the selected service.
