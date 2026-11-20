# Security audit (gate 2)

Date: 2026-11-20. Self-audit with automated tools and an AI reviewer. **Not an independent penetration test.**

Threat model: the tool reads untrusted text and prints commands a person may paste into a terminal. Risks: (a) the tool executes its input, (b) the tool emits a command whose meaning differs from the input.

| Item | Method | Result |
|---|---|---|
| No execution paths | `grep -rnE "subprocess\|os\.system\|os\.popen\|eval\|exec\|shell=True\|pickle\|__import__\|importlib" src` | 0 hits |
| No network, no telemetry | grep for `socket`, `urllib`, `http`, `requests` in `src` | 0 hits (only `https://` strings in rule data) |
| Safe parsing | `tomllib` (stdlib) only; no YAML, no pickle, no dynamic imports; rule files are package data, never user input | Pass |
| Injection pass-through | Lines with shell operators, expansion, globs, comments, escapes, control characters or leading `=` are not translated and are emitted commented out, never runnable. Translated words are re-quoted with `shlex.join`. Tests in `tests/test_translate.py` (hostile set, regression set) | Pass |
| Template injection | Single-pass placeholder substitution; `{` `}` refused in input; loader validates placeholders | Pass |
| File handling | Reads only the file given with `-f` (10 MB cap). Writes only stdout or `--output`, created with exclusive mode unless `--force` | Pass, tested |
| Resource limits | 200 000 character line and 20 000-item list tested | Pass |
| Static analysis | `bandit -r src` | 0 findings |
| Lint and types | `ruff check`, `ruff format`, `mypy --strict` | Clean |
| Dependencies | Zero runtime dependencies; `pip-audit` not applicable | n/a |
| Secrets | `gitleaks` over full git history | 0 leaks, 2 commits scanned (gitleaks, 2026-11-20) |
| Data privacy | `fixtures/` holds only public BI021 example commands; no patient data, unpublished names or server paths | Pass (manual read) |
| Claude Code hygiene | Fixtures treated as untrusted data in their own folder; never executed | Pass |
| CI hardening, PyPI trusted publishing, 2FA | Not in v0.1.0 (no CI, no PyPI release) | Deferred |

Known residual risk: rule content is unverified (`checked = false`), so a wrong flag mapping is a correctness risk, not a code-execution risk. The tool warns about this in its output.

Report vulnerabilities through a private GitHub security advisory on the repository once it is public. The repository does not exist publicly yet.
