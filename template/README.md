# ECSC attack/defence exploit template

Edit `SERVICE_NAME`, `SERVICE_PORT`, and `exploit_one()` in
`exploit_template.py`. The surrounding code fetches flag IDs, validates the
target IP, handles expected failures, and keeps stdout suitable for automatic
flag extraction.

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Minimal exploit

```python
SERVICE_NAME = "fireworx"
SERVICE_PORT = 8080


def exploit_one(target_ip, flag_id):
    with HTTPClient(target_ip, SERVICE_PORT) as http:
        response = http.get(f"/api/items/{flag_id}")
        ensure_status(response, 200)
        write_output(response)
```

`exploit()` calls `exploit_one(target_ip, flag_id)` once for every current flag
ID. Use `flag_ids_raw` inside `exploit()` only when the service needs the
original round/slot structure instead of the flattened IDs.

## Run

```bash
./exploit_template.py 10.60.2.2
```

Flag IDs come from `ecsc2026ad`, with the official `attack.json` endpoint as a
fallback. Set `FLAG_IDS` or `FLAG_IDS_RAW` for manual testing.

To print NOP's IP and current IDs for a service:

```bash
./nop_flag_ids.py fireworx
```

## Cheatsheets

- [HTTPClient and requests](HTTP_CHEATSHEET.md)
- [TCPClient and pwntools](TCP_CHEATSHEET.md)
- [BeautifulSoup HTML parsing](BS4_CHEATSHEET.md)

The wrappers are useful when you want the template's defaults: persistent HTTP
cookies, bounded response sizes, standard timeouts, IPv6 URL handling, concise
errors, and stdout reserved for flags. Use raw `requests` or pwntools directly
when you need behavior the wrapper does not expose; the wrapper is convenience,
not a security boundary or requirement.

Companion directories outside this template:

- [Payload construction and race helpers](../helpers/README.md)
- [Vulnerability research and patch resources](../resources/README.md)

## Template structure

- `exploit_template.py`: copy this and implement the exploit.
- `nop_flag_ids.py`: inspect NOP flag IDs.
- `requirements.txt`: Python dependencies.

Send possible flag-containing output through `write_output()`. Use `log()` for
debugging and raise `ExploitError` for an expected per-target failure.
