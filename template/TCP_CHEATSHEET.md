# TCPClient cheatsheet

`TCPClient` wraps a pwntools remote tube and applies the template timeout to
normal receive operations.

## Connect and close

The context manager always closes the connection:

```python
def exploit_one(target_ip, flag_id):
    with TCPClient(target_ip, SERVICE_PORT) as io:
        io.sendline(flag_id)
        write_output(io.recvall())
```

Override the default connection/receive timeout when needed:

```python
with TCPClient(target_ip, SERVICE_PORT, timeout=8.0) as io:
    banner = io.recvline()
```

## Bytes and encoding

Network protocols are byte-oriented. The wrapper automatically encodes a
`str` passed to send methods, but receive methods always return `bytes`.

```python
io.sendline("hello")     # automatically encoded
io.sendline(b"hello")   # explicit bytes

line = io.recvline()     # bytes
text = line.decode(errors="replace")
number = int(line.strip())

payload = b"A" * 32 + flag_id.encode()
io.send(payload)
```

Use bytes for exact binary payloads; do not decode arbitrary binary data unless
you actually need text.

## Send and sendline

`send()` sends exactly the given data. `sendline()` appends a newline:

```python
io.send(b"raw bytes without newline")
io.sendline(b"menu choice with newline")
io.sendline()  # blank line
```

## Receive data

```python
chunk = io.recv(4096)                     # up to 4096 bytes
line = io.recvline()                      # includes trailing newline
line = io.recvline(keepends=False)        # strips line ending
prompt = io.recvuntil(b"> ")             # includes marker
body = io.recvuntil(b"END", drop=True)    # excludes marker
rest = io.recvall(timeout=1.0)             # until EOF/quiet timeout
```

Receive methods return `b""` on a pwntools timeout. Fail explicitly if the
protocol requires data:

```python
line = io.recvline(timeout=2.0)
if not line:
    raise ExploitError("timed out waiting for response")
```

Discard an initial banner or buffered noise with care:

```python
discarded = io.clean(timeout=0.2)
log("discarded:", discarded)
```

## Wait for a prompt, then send

`sendlineafter()` is the usual menu helper. It receives through the marker and
then sends the answer with a newline:

```python
io.sendlineafter(b"Username: ", b"admin")
io.sendlineafter(b"Item ID: ", flag_id)
```

Use `sendafter()` when the protocol must not receive a trailing newline:

```python
io.sendafter(b"Data: ", payload)
```

Both methods return everything received through the marker:

```python
banner = io.sendlineafter(b"> ", b"1")
log("banner:", banner)
```

## Menu interaction

```python
def exploit_one(target_ip, flag_id):
    with TCPClient(target_ip, SERVICE_PORT) as io:
        io.sendlineafter(b"> ", b"1")
        io.sendlineafter(b"Username: ", b"attacker")
        io.sendlineafter(b"> ", b"3")
        io.sendlineafter(b"Item ID: ", flag_id)

        result = io.recvuntil(b"\n1) ", drop=True)
        write_output(result)
```

For a prompt that changes dynamically, receive first and inspect the bytes:

```python
menu = io.recvuntil(b"> ")
log("menu:", menu)
io.sendline(b"2")
```

## Per-operation timeouts

```python
banner = io.recvuntil(b"> ", timeout=5.0)
line = io.recvline(timeout=1.0)
received = io.sendlineafter(b"Choice: ", b"1", timeout=3.0)
```

Keep timeouts bounded in attack/defence: one stalled target should not block the
whole exploit run.

## Output and debugging

Send data that may contain flags to stdout:

```python
write_output(io.recvall())
```

Send diagnostic output to stderr:

```python
response = io.recvline()
log("service response:", response)
write_output(response)
```

For a pwntools operation not exposed by the wrapper, use `io.raw`:

```python
io.raw.shutdown("send")
remaining = io.recvall()
```

Prefer the wrapper methods when available so the configured timeouts remain
consistent.
