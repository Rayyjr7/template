# Safe implementation and patch patterns

Patch the trust boundary rather than blocking one payload. A denylist such as
rejecting `../` or the word `flag` is usually bypassable through encoding,
alternate separators, links, parser differences, or a different primitive.

## Emergency patch order

1. Remove public reachability or disable the vulnerable feature if possible.
2. Enforce authentication and object-level authorization server-side.
3. Replace code/data concatenation with structured APIs and bound parameters.
4. Constrain paths, formats, sizes, counts, redirects, time, memory, and output.
5. Run risky parsers and converters without secrets, network, or write access.
6. Add a regression test for the exact exploit and one variant.

## Operating-system commands

Avoid a shell. Pass an executable and argument array directly:

```python
subprocess.run(
    ["typst", "compile", "--root", project_dir, input_path, output_path],
    shell=False,
    cwd=project_dir,
    timeout=5,
    check=True,
    env={"PATH": "/usr/bin:/bin"},
)
```

Do not try to make arbitrary shell text safe by deleting metacharacters. If the
operation has a small valid domain, map an allowlisted user choice to a fixed
argument list. Run the child unprivileged with resource limits and a minimal
environment.

- [OWASP OS command injection defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)
- [Python subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations)

## Filesystem paths

For an existing requested file, resolve the base and candidate before access:

```python
from pathlib import Path

base = Path("/srv/data").resolve(strict=True)
candidate = (base / user_path).resolve(strict=True)
if candidate != base and base not in candidate.parents:
    raise ValueError("path escapes storage root")
```

For a new file, resolve and verify its existing parent, generate the final name
server-side, open with exclusive creation, and reject links where the platform
supports no-follow semantics. Re-checking a string before later opening it is
still vulnerable to TOCTOU replacement; descriptor-relative APIs such as
`openat` with no-follow controls are preferable for hostile local filesystems.

Never rely only on `startswith`, `normpath`, `Clean`, `normalize`, or `Join`:
canonical containment and symlink policy are separate checks.

- [CWE-22 Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [CWE-59 Link Following](https://cwe.mitre.org/data/definitions/59.html)
- [CWE-367 TOCTOU Race Condition](https://cwe.mitre.org/data/definitions/367.html)

## Archive extraction

Before extracting an untrusted archive:

1. Extract into a new empty directory on a disposable filesystem.
2. Limit compressed size, expanded size, entry count, path length, and nesting.
3. Reject absolute paths, `..`, empty names, device nodes, FIFOs, sockets,
   symlinks, and hardlinks unless the feature explicitly requires them.
4. Resolve every destination beneath the extraction root before writing.
5. Refuse duplicates, case-folding collisions, and overwrites.
6. Stream with size accounting; do not trust archive metadata alone.
7. Process the result in an isolated worker, then delete the directory.

Python 3.12+ supports extraction filters, but its documentation still recommends
additional checks and resource limits:

```python
with tarfile.open(fileobj=upload, mode="r:*") as archive:
    archive.extractall(destination, filter="data")
```

- [Python tar extraction filters](https://docs.python.org/3/library/tarfile.html#extraction-filters)
- [CWE-409 Improper Handling of Compressed Data](https://cwe.mitre.org/data/definitions/409.html)

## File uploads

Minimum defensive pipeline:

1. Authenticate and authorize the operation.
2. Enforce request, file, pixel/page, and processing-time limits.
3. Ignore the supplied path; generate a random storage identifier.
4. Allow only formats required by the service.
5. Check extension, magic bytes, and a strict parser; none is sufficient alone.
6. Store outside the webroot with non-executable permissions.
7. Serve through an ID-to-file mapping with authorization and safe disposition.
8. Sandbox any parser, thumbnailer, compiler, or converter.

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)

## SQL and database queries

Bind data values. Never concatenate or interpolate them into SQL:

```python
cursor.execute("SELECT flag FROM items WHERE owner = ? AND id = ?", (user_id, item_id))
```

```go
row := db.QueryRow("SELECT flag FROM items WHERE owner = ? AND id = ?", userID, itemID)
```

```java
var statement = connection.prepareStatement(
    "SELECT flag FROM items WHERE owner = ? AND id = ?"
);
statement.setLong(1, userId);
statement.setString(2, itemId);
```

```php
$statement = $pdo->prepare(
    "SELECT flag FROM items WHERE owner = :owner AND id = :id"
);
$statement->execute(["owner" => $userId, "id" => $itemId]);
```

```c
sqlite3_prepare_v2(db,
    "SELECT flag FROM items WHERE owner = ? AND id = ?", -1, &stmt, NULL);
sqlite3_bind_int64(stmt, 1, user_id);
sqlite3_bind_text(stmt, 2, item_id, -1, SQLITE_TRANSIENT);
```

Placeholders usually cannot represent table names, column names, or sort
directions. Map those values through a fixed allowlist instead.

- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [SQLite binding API](https://sqlite.org/c3ref/bind_blob.html)

## Authentication, sessions, and authorization

- Prefer the framework's maintained session implementation.
- Generate opaque session IDs with at least 128 bits from a CSPRNG.
- Rotate the session after login and privilege changes; expire it server-side.
- Set cookies `Secure`, `HttpOnly`, an appropriate `SameSite`, and `Path=/`.
- Check authorization on every requested object: include the current owner or
  tenant in the query instead of fetching by attacker-controlled ID first.
- Use constant-time comparison for MACs, tokens, and signatures.
- Never accept a client-supplied role, owner ID, price, or verification result.

Do not implement password hashing, signature schemes, token formats, or crypto
primitives yourself. This is where a maintained library is mandatory. Store
passwords with Argon2id, scrypt, bcrypt, or PBKDF2 as appropriate—not a fast
general-purpose hash.

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## Deserialization and structured input

Prefer schemas composed of strings, numbers, booleans, lists, and maps. Apply
type, depth, length, and total-size limits after parsing. Never deserialize a
native object graph from untrusted bytes with `pickle`, `Marshal.load`, Java
serialization, `BinaryFormatter`, PHP `unserialize`, or equivalent mechanisms.

Signing unsafe serialized data only prevents modification; it does not make
data from an untrusted signer safe, remove gadget chains, or stop replay.

- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [Python pickle warning](https://docs.python.org/3/library/pickle.html)

## Server-side requests and redirects

If possible, accept an identifier and map it to a fixed destination. Otherwise:

- Require `https` or the exact schemes needed.
- Parse once and reject userinfo, fragments, ambiguous encodings, and ports.
- Resolve DNS and reject loopback, private, link-local, multicast, metadata,
  and other forbidden ranges for every resolved address.
- Connect to the validated address while preserving the intended Host/SNI.
- Disable redirects or validate every redirect target again.
- Apply time, body-size, and response-count limits.
- Enforce egress filtering outside the application as defense in depth.

- [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

## Untrusted compilers, renderers, parsers, and converters

Use this boundary for Typst, LaTeX, Pandoc, office documents, images, media,
PDF/PostScript, diagrams, templates, notebooks, DSLs, and custom parsers:

1. Pin the exact engine and dependencies; check their security advisories.
2. Create a fresh job directory containing only required input files.
3. Validate the container format before invoking the complex parser.
4. Reject archive links and verify canonical paths during extraction.
5. Disable imports, plugins, macros, scripts, external helpers, URL fetching,
   package downloads, and environment inheritance unless explicitly required.
6. Configure the narrowest file root or allowlist the engine supports.
7. Run as a dedicated unprivileged user in a disposable sandbox with no network.
8. Mount no flags, credentials, source tree, sockets, or shared host temp files.
9. Limit CPU, memory, processes, input/output bytes, pixels/pages/frames, archive
   expansion, recursion, and wall-clock time outside the child process too.
10. Copy out only named expected outputs after checking type, size, and count.
11. Destroy the worker and job directory; never reuse attacker-controlled state.

Do not treat a built-in "safe mode" as the only boundary. It may cover only one
capability, depend on flags, or have version-specific bypasses. OS-level
isolation and least-privilege mounts remain necessary.

### Typst example

For attacker-controlled Typst source specifically:

1. Create a fresh project directory containing only required input files.
2. Reject archive links and verify canonical paths during extraction.
3. Set the compiler root to that directory; do not expose a broader root.
4. Run as a dedicated unprivileged user in a read-only container/sandbox.
5. Mount no flags, credentials, source tree, Docker socket, or host temp files.
6. Disable network and package downloads or provide a fixed trusted package set.
7. Limit CPU, memory, processes, file size, page count, and wall-clock time.
8. Copy out only the expected result file after validating its type and size.
9. Destroy the entire worker and temporary directory after each job.

Checking only the textual path is insufficient when an uploaded archive can
create a symlink inside the allowed root. Resolve links or disallow them before
the compiler sees the tree.

- [Typst data loading](https://typst.app/docs/reference/data-loading/)
- [Typst symlink sandbox-escape report](https://github.com/typst/typst/issues/5454)
- [ImageMagick security policy](https://imagemagick.org/script/security-policy.php)
- [Ghostscript security policy](https://www.ghostscript.com/security/index.html)
- [FFmpeg security](https://ffmpeg.org/security.html)

## Race conditions and state changes

Do not implement `check balance → perform action → update balance` as separate
unlocked operations. Use a transaction, conditional atomic update, unique
constraint, idempotency key, or compare-and-swap and verify exactly one row was
changed. Locking only inside one web worker does not protect multiple processes.

Example atomic debit:

```sql
UPDATE accounts
SET balance = balance - ?
WHERE id = ? AND balance >= ?;
```

Accept success only when the affected-row count is exactly one.
