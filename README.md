# ECSC attack/defence toolkit

The repository keeps exploit scaffolding, reusable payload code, and audit
references separate so the exploit template remains small and copyable:

```text
template/   exploit template and HTTP, TCP, and BeautifulSoup cheatsheets
helpers/    reusable payload, file, archive, PDF, and race helpers
resources/  vulnerability research, audit searches, and patch patterns
```

## Start here

- [Exploit template](template/README.md)
- [Helper usage](helpers/README.md)
- [Audit resource index](resources/README.md)

Run an exploit from the repository root when it imports `helpers`, or add this
directory to `PYTHONPATH`:

```bash
PYTHONPATH=/path/to/repository python3 exploit.py 10.60.2.2
```

Install only what the part you use needs:

```bash
python3 -m pip install -r template/requirements.txt
python3 -m pip install -r helpers/requirements.txt  # optional PDF parsing
```
