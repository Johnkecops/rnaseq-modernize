# Code review log (gate 1)

Date: 2026-11-20. Automated pass: ruff, `mypy --strict`, bandit clean. Review by a fresh Claude subagent that did not write the code (no author context). Human review of rules and scientific notes: **PENDING** (see below).

| # | Finding | Disposition |
|---|---|---|
| 1 | Comment line ending in `\` swallowed the next command | Fixed (translate.py), regression test |
| 2 | Empty flag value produced `/transcripts.gtf`, `/hisat2_out.sam` | Fixed: empty value is not translated, tests |
| 3 | Untranslated lines exited 0; uncaught errors shared code 1 | Fixed: exit 3 for not translated; bad rule file exits 2 with message; documented in README |
| 4 | Missing warnings: stdout default, accepted_hits.bam absent after HISAT2, FASTA input | Fixed: added to rule notes (FASTA and stringtie-stdout points phrased "verify", not asserted) |
| 5 | Leading `=` expands in zsh | Fixed: word starting with `=` is not translated, test |
| 5b | `--flag==foo` inline value starting with `=` bypassed the zsh guard (automated commit review) | Fixed: every emitted word and flag value is checked; tests |
| 6 | Control characters (ESC) reached terminal via comment text | Fixed: lines with control characters not translated; emitter also replaces them with `?`; test |
| 7 | Repeated flags emitted twice | Fixed: repeated flag is not translated, tests. Bowtie `-S` note reworded |
| 8 | Loader accepted duplicate arities/flags and bad placeholders; bad TOML gave traceback; substitution relied on `{` in META | Fixed: validation at load, clean error, single-pass regex substitution, tests |
| 9 | Long aliases `--output-dir` absent | Closed, no change: unverified from the manuals, so lines using them stay "not translated" (safe, restrictive). Add after a human confirms in the manuals |
| 10 | `versions` never printed, manual URLs not shown to reader; bowtie2-build identity rule is YAGNI; broken pipe, non-UTF-8 locale | Closed, no change: JSON/rules carry the data; identity rule kept because BI021 uses `bowtie2-build`; others are low value for v0.1.0 |
| 11 | Tautological test; weak hostile and flag-rule tests; gaps | Fixed: tests replaced or strengthened, gaps covered. Golden outputs are hand-written by the author, so circular: they must be re-derived by the human reviewer |

Reviewer's flag-default checks (from memory, not a manual): TopHat `-i` 70 and `-I` 500000, HISAT2 min 20 and max 500000, Cufflinks `-o` as directory. Not a substitute for the human check.

## Still open before release

- **Human check of every rule** against the cited manuals (all `checked = false`). Rows the manual fetch could not confirm: Cufflinks `-o`; the HISAT2 "no equivalent" claims for `-N`, `--read-edit-dist`, `--read-realign-edit-dist`, `--max-coverage-intron`, `-M`; `-o` directory-to-file mapping; the file names `hisat2_out.sam` and `transcripts.gtf` (tool choices); StringTie `-A` and GTF as replacements for the `*.fpkm_tracking` files; HISAT2 and StringTie manual versions; the samtools step.
- Re-derive golden test expectations by hand.
- Confirm licence against i3L policy.
