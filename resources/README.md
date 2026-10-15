# Attack/defence audit resources

Use this directory as a fast index while reading and patching an unfamiliar
service. No checklist can prove that code is safe; follow untrusted data from
its entry point to filesystem, process, database, template, parser, network,
authentication, and authorization sinks.

## Pick the document for the current job

- [Vulnerability references](VULNERABILITY_REFERENCES.md): dangerous APIs,
  capability-first workflow, language-specific review anchors, uncommon stacks,
  converters, and dependency advisory databases.
- [Safe implementation patterns](SAFE_IMPLEMENTATIONS.md): focused patch
  patterns for commands, paths, archives, uploads, databases, authentication,
  sessions, SSRF, deserialization, and document conversion.
- [Audit search terms](AUDIT_SEARCH_TERMS.md): copy-paste `rg` commands,
  language keywords, technology search queries, and a rapid review workflow.
- [Helper cheatsheet](../helpers/README.md): construct files, TAR/ZIP/PDF
  payloads, multipart uploads, encodings, polling, and race requests.

## Ten-minute service triage

1. Identify languages, frameworks, dependencies, entrypoints, ports, databases,
   workers, converters, and mounted secrets.
2. Map every unauthenticated and authenticated route or protocol command.
3. Search for process execution, file access, archive extraction, templates,
   deserialization, dynamic queries, outbound requests, and custom crypto.
4. Verify ownership checks on every object lookup, not only login checks.
5. Inspect client JavaScript: it often reveals hidden endpoints and request
   sequences such as challenge creation.
6. Trace uploaded data through extraction, parsing, conversion, storage, and
   download. Treat every parser as an attack surface.
7. Patch the root boundary, then test valid input, rejected input, and one
   exploit regression case.

If the stack is absent from the language list, use the unknown-technology
workflow and classify its capabilities. The lists are search accelerators, not
an allowlist of languages or the universe of possible vulnerable APIs.

## High-value external indexes

- [CWE weakness catalog](https://cwe.mitre.org/data/index.html)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OSV package vulnerability search](https://osv.dev/)
- [NIST National Vulnerability Database](https://nvd.nist.gov/vuln/search)
- [GitHub Advisory Database](https://github.com/advisories)
