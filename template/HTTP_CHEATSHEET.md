# HTTPClient cheatsheet

`HTTPClient` wraps a persistent `requests.Session`. Cookies received by one
request are therefore sent on later requests made by the same client.

```python
def exploit_one(target_ip, flag_id):
    with HTTPClient(target_ip, SERVICE_PORT) as http:
        response = http.get(f"/api/items/{flag_id}")
        ensure_status(response, 200)
        write_output(response)
```

Paths must start with `/`. Available shortcuts are `get`, `post`, `put`,
`patch`, and `delete`.

## Query parameters

This requests `/search?q=test&page=2` and lets `requests` safely URL-encode the
values:

```python
response = http.get(
    "/search",
    params={"q": "test", "page": 2},
)
```

Repeated parameters use a list of tuples:

```python
response = http.get(
    "/search",
    params=[("tag", "web"), ("tag", "crypto")],
)
```

## HTML form / URL-encoded body

For a normal HTML form (`application/x-www-form-urlencoded`), pass a dictionary
as `data`. Do not build `"name=x&chal=y"` yourself.

```python
response = http.post(
    "/submit",
    data={
        "name": "alice",
        "chal": challenge,
        "sig": signature,
    },
)
```

Repeated form keys also use tuples:

```python
response = http.post(
    "/submit",
    data=[("role", "user"), ("role", "admin")],
)
```

## JSON body and response

`json=` serializes the dictionary and sets `Content-Type: application/json`:

```python
response = http.post(
    "/api/login",
    json={"username": "admin", "password": "admin"},
)
ensure_status(response, 200)

payload = response.json()
token = payload["token"]
```

JSON is not a replacement for the request syntax shown in DevTools. Match the
server's `Content-Type` and parser:

- Browser **Form Data** or `application/x-www-form-urlencoded` → `data={...}`.
- Browser **Request Payload** containing JSON or `application/json` → `json={...}`.
- A response containing only the challenge string → `response.text.strip()`.
- A response such as `{"chal":"abc"}` → `response.json()["chal"]`.

For your challenge flow, that means:

```python
with HTTPClient(target_ip, SERVICE_PORT) as http:
    http.get("/")  # keep any session cookie
    challenge = http.get(
        "/challenge",
        params={"name": "alice"},
    ).text.strip()

    signature = sign(challenge)
    response = http.post(
        "/submit",
        data={"name": "alice", "chal": challenge, "sig": signature},
    )
```

If invalid JSON is possible, handle it explicitly:

```python
try:
    payload = response.json()
except ValueError as error:
    raise ExploitError("server returned invalid JSON") from error
```

## Headers and authentication

Headers for every request made by the client:

```python
with HTTPClient(
    target_ip,
    SERVICE_PORT,
    headers={"User-Agent": "exploit", "X-Team": "example"},
) as http:
    response = http.get("/api/items")
```

Headers for one request:

```python
response = http.get(
    "/api/private",
    headers={"Authorization": f"Bearer {token}"},
)
```

HTTP Basic authentication is passed through to `requests`:

```python
response = http.get("/admin", auth=("admin", "password"))
```

## Cookies and login sessions

Cookies from the login response persist automatically:

```python
with HTTPClient(target_ip, SERVICE_PORT) as http:
    login = http.post(
        "/login",
        data={"username": "admin", "password": "admin"},
    )
    ensure_status(login, 200, 302)

    private = http.get("/private")
    write_output(private)
```

Set or inspect cookies directly through the underlying session:

```python
http.raw.cookies.set("session", session_cookie)
log(http.raw.cookies.get_dict())
```

Or send a cookie for only one request:

```python
response = http.get("/private", cookies={"session": session_cookie})
```

## Multipart form data and one file

Adding `files=` makes `requests` build a `multipart/form-data` request. Other
form fields remain in `data=`:

```python
files = {
    "document": ("payload.txt", b"file contents", "text/plain"),
}
response = http.post(
    "/upload",
    data={"description": "test upload", "owner": "alice"},
    files=files,
)
```

For a file on disk, keep it open until the request finishes:

```python
with open("payload.zip", "rb") as payload_file:
    response = http.post(
        "/upload",
        files={
            "archive": (
                "payload.zip",
                payload_file,
                "application/zip",
            )
        },
    )
```

## Multiple files

Different field names can use a dictionary:

```python
response = http.post(
    "/upload",
    files={
        "avatar": ("avatar.png", avatar_bytes, "image/png"),
        "document": ("notes.txt", notes_bytes, "text/plain"),
    },
)
```

For multiple files under the same form field, use a list of tuples:

```python
response = http.post(
    "/upload-many",
    files=[
        ("files", ("first.txt", b"first", "text/plain")),
        ("files", ("second.txt", b"second", "text/plain")),
    ],
)
```

## Redirects and status codes

Redirects are followed by default. Disable this to inspect the original
response and its `Location` header:

```python
response = http.post(
    "/login",
    data={"username": "admin", "password": "admin"},
    allow_redirects=False,
)
ensure_status(response, 302, 303)
next_path = response.headers.get("Location")
```

Useful response properties:

```python
log("status:", response.status_code)
log("headers:", dict(response.headers))
log("final URL:", response.url)
log("redirects:", [item.status_code for item in response.history])

text = response.text       # decoded text
body = response.content    # raw bytes
```

Use `ensure_status()` when only specific statuses are valid:

```python
ensure_status(response, 200, 201)
```

## Timeouts, HTTPS, and output

The client applies the template timeout automatically. Override it per request
or for the whole client:

```python
response = http.get("/slow", timeout=10.0)

with HTTPClient(target_ip, 443, scheme="https", timeout=8.0) as http:
    response = http.get("/")
```

The template defaults to `verify=False`, which is convenient for self-signed AD
services but does not authenticate the server. Use `verify=True` when targets
have valid certificates; changing `http` to `https` does not change `data=`,
`json=`, cookies, or any other request semantics.

Send possible flags to stdout and debugging to stderr:

```python
write_output(response)          # response body
write_output(response.content)  # explicit raw bytes
log("status:", response.status_code)
```

Do not use `print()` for debug output: stdout is intended for results that the
external flag parser should inspect.
