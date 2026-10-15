# Audit search terms and research playbook

Start broad, then trace actual attacker-controlled values. Search results are
leads, not findings: inspect validation, authorization, data type, environment,
and the exact library version before deciding exploitability.

## Repository orientation

```bash
find . -maxdepth 3 -type f | sort
rg -n --hidden 'TODO|FIXME|HACK|XXX|debug|backdoor|admin|secret|flag'
rg -n --hidden 'listen|bind|port|route|endpoint|handler|controller|websocket'
rg -n --hidden 'Dockerfile|compose|volume|mount|privileged|cap_add|/var/run/docker.sock'
```

Identify manifests and lockfiles:

```bash
find . -type f \( \
  -name 'requirements*.txt' -o -name 'pyproject.toml' -o -name 'uv.lock' -o \
  -name 'package*.json' -o -name 'go.mod' -o -name 'go.sum' -o \
  -name 'Cargo.toml' -o -name 'Cargo.lock' -o -name 'build.zig*' -o \
  -name 'pom.xml' -o -name 'build.gradle*' -o -name 'composer.lock' -o \
  -name 'Gemfile.lock' -o -name 'mix.exs' -o -name 'mix.lock' -o \
  -name 'rebar.config' -o -name 'cpanfile' -o -name 'META.json' -o \
  -name 'Project.toml' -o -name 'Manifest.toml' -o -name 'DESCRIPTION' -o \
  -name '*.nimble' -o -name 'shard.yml' -o -name 'dune-project' -o \
  -name '*.opam' -o -name 'cabal.project' -o -name 'stack.yaml' -o \
  -name 'pubspec.yaml' -o -name 'Package.swift' -o -name '*.csproj' \
\) -print
```

If the language is unfamiliar, do not wait for a language-specific checklist:

```bash
file $(find . -maxdepth 3 -type f | head -200)
rg -n --hidden 'FROM |RUN |ENTRYPOINT|CMD |install|build|compile|serve|migrate'
rg -n --hidden 'ffi|foreign|native|plugin|extension|shared library|dlopen|LoadLibrary'
```

Read the build and startup path first. It reveals generated code, embedded DSLs,
native helpers, converters, and the real executable even when extensions do not.

## Universal source-to-sink search

```bash
rg -ni --hidden 'eval|exec|system|popen|spawn|processbuilder|shell=true|command\('
rg -ni --hidden 'upload|multipart|filename|extract|unpack|archive|tar|zip|symlink|hardlink'
rg -ni --hidden 'open\(|readfile|writefile|send_file|download|path\.join|resolve|canonical'
rg -ni --hidden 'select |insert |update |delete |query\(|execute\(|raw\(|nativequery'
rg -ni --hidden 'pickle|marshal|unserialize|objectinputstream|binaryformatter|yaml\.load'
rg -ni --hidden 'http\.get|requests\.|fetch\(|axios|urlopen|httpclient|reqwest|redirect'
rg -ni --hidden 'jwt|token|session|cookie|signature|hmac|md5|sha1|random|nonce|challenge'
rg -ni --hidden 'owner|userid|user_id|tenant|role|admin|permission|authorize|access'
rg -ni --hidden 'template|render|innerhtml|html_safe|markup|escape|sanitize'
```

Then answer for every match:

1. Can a remote user influence the value?
2. Is decoding or normalization performed before or after validation?
3. Does another parser interpret the value differently later?
4. Is the security decision tied to the current user and requested object?
5. Can links, redirects, races, duplicate keys, integer conversions, or repeated
   requests change the assumption?

## Feature-focused searches

### Authentication and IDOR

```text
login register reset password token session challenge signature
/profile/{id} /user/{id} /item/{id} owner_id user_id tenant_id
SELECT ... WHERE id = ?          without owner/tenant in the same query
client-supplied role/admin/owner/verified fields
GET endpoints that change state
```

Test horizontal access, vertical access, missing authentication, session
fixation, predictable tokens, replay, signature edge cases, and differences
between list/detail/update/delete authorization.

### Uploads, archives, and converters

```text
multipart filename extension MIME Content-Type magic bytes
extract extractall unpack_archive ZipFile TarFile ZipInputStream
../ absolute path duplicate entry symlink hardlink device FIFO
thumbnail convert compile render pandoc typst latex ffmpeg ghostscript libreoffice
temporary directory cleanup timeout resource limit output path
```

Trace the whole pipeline: HTTP body → temporary file → extraction → parser →
child process → generated output → download. A safe upload handler can still
feed an unsafe converter.

### Commands and interpreters

```text
shell=True sh -c bash -c cmd /c powershell
eval exec compile ScriptEngine template expression language
environment PATH LD_PRELOAD PYTHONPATH NODE_OPTIONS RUBYOPT
working directory executable path argument concatenation
```

### Databases

```text
query construction with +, %, format, f-string, interpolation, template literal
dynamic ORDER BY, table, column, LIMIT, JSON path, regex, or operator
NoSQL $where $regex operator injection mass assignment
database errors returned to clients
```

### Outbound requests

```text
URL webhook callback avatar import preview fetch proxy redirect
localhost 127.0.0.1 ::1 private IP link-local 169.254 metadata
file:// gopher:// ftp:// dict:// unix socket DNS rebinding redirect chain
```

### Cryptography and tokens

```text
hard-coded key nonce reuse constant IV deterministic encryption
random instead of CSPRNG ECB CBC without MAC signature verification exceptions
JWT alg none algorithm confusion missing issuer/audience/expiry checks
comparison with == instead of constant-time compare
```

## Language quick searches

### Python

```bash
rg -n 'eval\(|exec\(|pickle\.loads|yaml\.load|shell\s*=\s*True|os\.system|os\.popen'
rg -n 'extractall|unpack_archive|send_file|render_template_string|Markup\('
rg -n 'execute\(f|execute\([^,]*(%|\.format)|requests\.(get|post)\([^"'"']'
```

### Go

```bash
rg -n 'exec\.Command|"sh"\s*,\s*"-c"|template\.(HTML|JS)|fmt\.Sprintf.*(SELECT|INSERT|UPDATE|DELETE)'
rg -n 'filepath\.(Join|Clean|Rel)|os\.(Open|ReadFile|WriteFile)|archive/(tar|zip)'
rg -n 'http\.(Get|Post)|Client\.Do|math/rand|gob\.NewDecoder'
```

### Rust

```bash
rg -n '\bunsafe\b|Command::new|\.arg\("-c"\)|canonicalize|PathBuf|std::fs'
rg -n 'format!.*(SELECT|INSERT|UPDATE|DELETE)|reqwest|danger_accept_invalid_certs'
rg -n 'tar::|zip::|serde_yaml|from_raw_parts|get_unchecked|transmute'
```

### Zig

```bash
rg -n '@(ptrCast|alignCast|intCast|truncate|memcpy|memmove)|\[\*c\]|allowzero'
rg -n 'catch unreachable|\bundefined\b|allocator\.(alloc|create)|\.(free|destroy)\('
rg -n 'std\.process\.Child|std\.fs|openFile|createFile|realpath'
```

### Java/Kotlin

```bash
rg -n 'Runtime\.getRuntime|ProcessBuilder|ObjectInputStream|readObject|ScriptEngine'
rg -n 'Statement|createNativeQuery|executeQuery|Paths\.get|Path\.resolve|ZipInputStream'
rg -n 'DocumentBuilderFactory|SAXParserFactory|XMLDecoder|Class\.forName|setAccessible'
```

### JavaScript/TypeScript

```bash
rg -n 'eval\(|new Function|child_process|execSync|shell\s*:\s*true|vm\.run'
rg -n 'innerHTML|outerHTML|dangerouslySetInnerHTML|__proto__|constructor\.prototype'
rg -n 'fs\.(read|write)|path\.(join|resolve)|fetch\(|axios|http\.request'
```

### PHP

```bash
rg -n 'eval\(|assert\(|system\(|exec\(|shell_exec|passthru|popen|proc_open|`[^`]+`'
rg -n 'include|require|unserialize|file_get_contents|move_uploaded_file|ZipArchive'
rg -n 'PDO|mysqli_query|\$_(GET|POST|REQUEST|FILES)|extract\(|parse_str'
```

### Ruby

```bash
rg -n 'eval|instance_eval|class_eval|constantize|Marshal\.load|YAML\.load'
rg -n 'system|IO\.popen|Open3|`[^`]+`|File\.(read|write)|File\.join'
rg -n 'find_by_sql|connection\.execute|html_safe|\braw\b|redirect_to'
```

### C/C++

```bash
rg -n '\b(gets|strcpy|strcat|sprintf|vsprintf|scanf|sscanf|memcpy|memmove)\s*\('
rg -n '\b(system|popen|execl|execvp|dlopen|mktemp|tmpnam|realpath|access)\s*\('
rg -n 'printf\s*\([^"'"']|malloc|calloc|realloc|free|sizeof|strlen|snprintf'
```

### Shell and PowerShell

```bash
rg -n '\beval\b|\bsource\b|(^|[;&|])\s*\.\s|sh -c|bash -c|`|\$\('
rg -n 'Invoke-Expression|\biex\b|ScriptBlock|Start-Process|powershell.*-Command'
rg -n '\$[A-Za-z_][A-Za-z0-9_]*' --glob '*.sh' --glob '*.bash' --glob '*.ps1'
```

### Perl, Erlang, and Elixir

```bash
rg -n '\beval\b|evalbytes|\bsystem\b|\bexec\b|qx|Storable|thaw|retrieve' --glob '*.pl' --glob '*.pm'
rg -n 'Code\.eval|System\.(shell|cmd)|:os\.cmd|Port\.open|binary_to_term|load_nif'
rg -n 'File\.(read|write)|Path\.join|Phoenix\.HTML\.raw|Ecto.*query|list_to_atom'
```

### Julia and R

```bash
rg -n '\beval\b|\binclude\b|include_string|\brun\b|deserialize|ccall|unsafe_' --glob '*.jl'
rg -n '\beval\b|\bparse\b|\bsource\b|system2?\b|shell\b|unserialize|readRDS|dyn\.load' --glob '*.R' --glob '*.r'
```

### Nim, Crystal, Haskell, and OCaml

```bash
rg -n 'execShellCmd|execCmd|startProcess|gorge|staticExec|\.\{emit\.\}|cast\[' --glob '*.nim'
rg -n 'Process\.(run|new)|`[^`]+`|Pointer|LibC|YAML|File\.' --glob '*.cr'
rg -n 'System\.Process|callCommand|shell|readProcess|unsafePerformIO|Foreign\.' --glob '*.hs'
rg -n 'Sys\.command|Unix\.(system|create_process)|Marshal\.from_|Obj\.magic|Dynlink' --glob '*.ml'
```

### Dart and Swift

```bash
rg -n 'Process\.(run|start)|runInShell|dart:ffi|DynamicLibrary|File\(' --glob '*.dart'
rg -n '\bProcess\b|FileManager|URLSession|Unsafe.*Pointer|dlopen|NSExpression' --glob '*.swift'
```

## Compiler, renderer, parser, and DSL playbook

Do not start with a product name. First model the entire pipeline:

```text
request/message → decode → temporary storage → archive/container extraction
→ parser/compiler/renderer → helper processes/network/plugins → generated output
→ storage/download
```

Search the service and deployment files:

```bash
rg -ni 'compile|render|convert|parse|preview|thumbnail|transcode|diagram|template'
rg -ni 'typst|latex|pandoc|imagemagick|convert|magick|ghostscript|ffmpeg|libreoffice|graphviz|plantuml'
rg -ni 'include|import|read|file|url|network|plugin|macro|extension|package|root|sandbox|policy'
rg -ni 'tar|zip|extract|unpack|symlink|hardlink|temp|upload|multipart'
```

Questions for every engine or input format:

1. Who controls source, filenames, metadata, and referenced resources?
2. Can the input execute expressions, load plugins, include files, or fetch URLs?
3. Can an archive/container create links, traversal paths, or special files?
4. Which canonical filesystem roots, mounts, environment, and secrets are visible?
5. Which helper binaries and native libraries does the engine invoke or load?
6. Are network, package downloads, redirects, and DNS resolution possible?
7. Are CPU, memory, output, recursion, process count, and time bounded externally?
8. Is only the expected output copied from a fresh disposable sandbox?
9. What exact versions, flags, policies, plugins, and codecs are enabled?

Useful searches for any unusual component:

```text
<product> <exact-version> security advisory
<product> <exact-version> CVE OR GHSA
<product> untrusted input arbitrary file read OR write
<product> path traversal symlink hardlink archive
<product> command injection SSRF sandbox escape
<product> denial of service recursion memory exhaustion
<input-format> parser vulnerability <library-name> <exact-version>
<product> security policy safe mode limitations
site:<upstream-domain> security advisory <product>
```

Also search dependencies and transitive tools individually. A wrapper's version
does not identify the ImageMagick, Ghostscript, FFmpeg, browser, office suite,
codec, native library, or plugin version it launches.

### Typst worked example

Search source and generated inputs:

```bash
rg -n '#(read|include|import|image|bibliography|csv|json|yaml|xml|plugin)\b' .
rg -n 'typst\s+(compile|watch)|--root|sys\.inputs|@preview' .
rg -n 'tar|zip|extract|unpack|symlink|hardlink|temp|upload|multipart' .
```

Questions to answer:

1. Who controls the `.typ` source and every referenced file?
2. Can an archive create links, traversal paths, duplicates, or special files?
3. What exact directory is passed as `--root`?
4. Is canonical containment checked after link resolution?
5. Can packages or remote assets be downloaded?
6. Which secrets and mounts are visible to the compiler process?
7. Are CPU, memory, file size, process count, and time bounded?
8. Is only the expected PDF copied out of a disposable sandbox?

Useful web searches:

```text
Typst <version> security advisory
Typst <version> arbitrary file read
Typst symlink sandbox escape
Typst #read path traversal
Typst archive upload symlink
site:github.com/typst/typst/issues security symlink path root
```

## Dependency checks

Run scanners only after recording lockfiles; automatic fixes can change behavior
or execute package scripts.

```bash
pip-audit                         # Python
govulncheck ./...                 # Go
cargo audit                       # Rust
npm audit                         # Node.js
composer audit                    # PHP
bundle audit check --update       # Ruby
osv-scanner scan -r .             # Multiple ecosystems
```

- [OSV-Scanner usage](https://google.github.io/osv-scanner/usage/)
- [Go vulnerability checking](https://go.dev/doc/tutorial/govulncheck)
- [RustSec](https://rustsec.org/)
- [`npm audit`](https://docs.npmjs.com/cli/commands/npm-audit/)
- [Composer `audit`](https://getcomposer.org/doc/03-cli.md#audit)

## Patch verification

After patching, test all three:

1. Normal checker-like behavior still succeeds.
2. The exact exploit no longer succeeds.
3. A variant reaches the same boundary through different encoding, path,
   redirect, archive entry order, duplicate key, concurrent request, or user.

Review the final diff for accidental flag leakage, broad exception handling,
debug endpoints, hard-coded credentials, changed permissions, and fail-open
behavior.
