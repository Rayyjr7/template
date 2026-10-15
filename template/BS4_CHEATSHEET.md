# BeautifulSoup cheatsheet

BeautifulSoup parses the HTML returned by the service. It does **not** execute
JavaScript.

```python
from bs4 import BeautifulSoup


response = http.get("/")
ensure_status(response, 200)
soup = BeautifulSoup(response.text, "html.parser")
```

## Inputs by name or ID

Given:

```html
<input id="challenge" name="chal" value="abc123">
```

Select it by `name`:

```python
challenge_input = soup.select_one('input[name="chal"]')
challenge = challenge_input.get("value")
```

Or by ID:

```python
challenge_input = soup.find("input", id="challenge")
# Equivalent CSS selector: soup.select_one("#challenge")
```

Select all inputs and inspect their names and values:

```python
fields = {
    element.get("name"): element.get("value", "")
    for element in soup.select("input[name]")
}
```

## Hidden fields and CSRF tokens

```python
csrf_input = soup.select_one('input[type="hidden"][name="csrf_token"]')
if csrf_input is None:
    raise ExploitError("CSRF input not found")

csrf_token = csrf_input.get("value")
if not csrf_token:
    raise ExploitError("CSRF token is empty")

response = http.post(
    "/submit",
    data={"csrf_token": csrf_token, "name": "alice"},
)
```

The same `HTTPClient` must perform the GET and POST when the hidden token is
bound to a session cookie.

## Forms and actions

Find a specific form and its submission details:

```python
form = soup.find("form", id="sign-form")
if form is None:
    raise ExploitError("sign form not found")

action = form.get("action") or "/"
method = (form.get("method") or "get").lower()

if not action.startswith("/"):
    raise ExploitError(f"unexpected form action: {action!r}")

fields = {
    element["name"]: element.get("value", "")
    for element in form.select("input[name]")
}
fields.update({"name": "alice", "sig": signature})

response = http.request(method, action, data=fields)
```

Check the form's `enctype`: ordinary forms use `data=`, while
`multipart/form-data` forms usually combine `data=` and `files=`. See the
[HTTP cheatsheet](HTTP_CHEATSHEET.md#multipart-form-data-and-one-file).

## Links

```python
for link in soup.select("a[href]"):
    label = link.get_text(" ", strip=True)
    href = link["href"]
    log(label, href)
```

Find a link by visible text:

```python
download_link = soup.find("a", string=lambda text: text and "download" in text.lower())
if download_link is None or not download_link.get("href"):
    raise ExploitError("download link not found")

download_path = download_link["href"]
```

## Tables

Read a table into rows of text:

```python
table = soup.select_one("table#users")
if table is None:
    raise ExploitError("users table not found")

rows = []
for row in table.select("tr"):
    cells = [cell.get_text(" ", strip=True) for cell in row.select("th, td")]
    if cells:
        rows.append(cells)
```

Find the link in a row containing a flag ID:

```python
item_path = None
for row in soup.select("table tr"):
    if flag_id in row.get_text(" ", strip=True):
        link = row.select_one("a[href]")
        if link is not None:
            item_path = link["href"]
            break

if item_path is None:
    raise ExploitError(f"no table row for {flag_id!r}")
```

## Lists and repeated elements

```python
items = [
    item.get_text(" ", strip=True)
    for item in soup.select("ul.results > li")
]
```

Extract attributes from repeated cards:

```python
item_ids = [
    card["data-item-id"]
    for card in soup.select(".item[data-item-id]")
]
```

## Safely handle missing elements

`find()` and `select_one()` return `None` when there is no match. Never access
`.get()`, `[...]`, or `.get_text()` before checking the result.

```python
element = soup.select_one('meta[name="api-token"]')
if element is None:
    raise ExploitError("API token element not found")

token = element.get("content")
if token is None:
    raise ExploitError("API token has no content attribute")
```

For optional text, provide a fallback:

```python
message_element = soup.select_one(".message")
message = message_element.get_text(" ", strip=True) if message_element else ""
```

## JavaScript-generated values

`requests` and BeautifulSoup only receive the server's HTTP response. They do
not run page JavaScript, so a field populated in the browser may still contain
a placeholder in `response.text`.

Use browser DevTools to reproduce the actual data flow:

1. Open **Network**, enable **Preserve log**, and reload the page.
2. Fill in the form and submit it manually.
3. Inspect the final request's **Payload/Form Data**.
4. Inspect preceding **Fetch/XHR** requests for the real challenge or token.
5. Reproduce those API calls with the same `HTTPClient`, so cookies persist.
6. If there is no extra request, search **Sources** for `chal`, `fetch`,
   `FormData`, `submit`, or the input's ID; port the relevant JavaScript logic
   to Python.

Typical API-backed flow when `/challenge` returns only the challenge text:

```python
with HTTPClient(target_ip, SERVICE_PORT) as http:
    http.get("/")  # establish session cookie

    challenge_response = http.get(
        "/challenge",
        params={"name": "alice"},
    )
    ensure_status(challenge_response, 200)
    challenge = challenge_response.text.strip()

    signature = sign(challenge)

    result = http.post(
        "/submit",
        data={"name": "alice", "chal": challenge, "sig": signature},
    )
    write_output(result)
```

Use `.json()` only if the response body is actually JSON, for example
`{"chal":"..."}`. A response containing only `abc123` is plain text, so use
`.text.strip()` (or `.content` when the signature operates on exact bytes).

Sleeping after the initial GET does not make JavaScript run. Prefer calling the
underlying API or reproducing its local calculation instead of using a browser
automation framework in a time-sensitive exploit.
