# rnaseq-modernize

Prints modern equivalents of legacy RNA-seq commands (TopHat, Cufflinks, Bowtie) with a note per change. **It only translates text. It never runs the commands it reads or writes.** Version 0.1.0, built for the BI021 Transcriptomics Computational Protocol.

| Legacy | Modern |
|---|---|
| `bowtie-build`, `bowtie` | `bowtie2-build`, `bowtie2` |
| `bowtie2-build` | unchanged (noted) |
| `tophat` | `hisat2` |
| `cufflinks` | `stringtie` |

## Background

This tool was developed from the *Transcriptomics Computational Protocol*, the lab handbook for course BI021 at i3L University, Jakarta (Parikesit, Agustriawan and Pradipta, 2021) [1]. The handbook teaches RNA-seq analysis in six sessions. Its command-line steps use Bowtie and Bowtie2 for indexing and mapping, TopHat for spliced alignment, and Cufflinks for transcript assembly and FPKM. Students and teaching staff who reuse those commands need to know what to change when working with the HISAT2, StringTie and Bowtie2 tools instead. A published protocol for that tool pairing exists (Pertea et al., 2016) [2], but it describes a workflow rather than rewriting existing commands. This repository covers only the commands used in the BI021 handbook; see Limits below.

## Status: draft rules

Every rule in `src/rnaseq_modernize/rules/*.toml` was drafted from the official manuals and carries `checked = false`. **No rule has been checked by a human yet.** Output says so in its header. Release gate: `RELEASE_GATE=1 pytest` fails until every rule is checked. Do not treat the output as validated.

## Install and use

Python 3.11 or later. No runtime dependencies.

```bash
pip install -e .
rnaseq-modernize "tophat -i 50 -I 5000 -o out index/chr20 reads.fastq"
rnaseq-modernize -f legacy_script.sh            # a file of commands
cat legacy_script.sh | rnaseq-modernize -f -    # stdin
rnaseq-modernize -f legacy_script.sh --json -o result.json   # JSON, new file only (--force to overwrite)
```

Output is plain text: translated commands on their own lines, everything else as `#` comments. Exit codes: 0 all lines translated (or comments/blank), 1 a line was malformed (for example unbalanced quotes), 2 usage, I/O or rule-file error, 3 at least one line was not translated.

## Limits (read before use)

- **Results will differ.** HISAT2, StringTie and Bowtie2 are different algorithms from TopHat, Cufflinks and Bowtie. Translated commands do not reproduce legacy results. No benchmark has been run.
- **Only flags used in BI021 are covered.** Any other flag makes the whole command "not translated, check manually". The tool never guesses.
- **Flags without an equivalent are dropped with a warning** (for example TopHat `-N`, `--read-edit-dist`, `--read-realign-edit-dist`, `--max-coverage-intron`, `-M`).
- **Lines containing shell operators or expansion characters are not translated**: `; & | < > ( ) \` $ * ? [ ] { } ~ \ # !`. That includes pipes, redirects, `$VAR`, globs, inline comments and several commands on one line. Lines with control characters, a word starting with `=`, a repeated flag or an empty flag value are also refused. Split such lines by hand. Untranslated lines are kept literally but commented out so they cannot run when pasted.
- Line continuations with a trailing backslash are joined. Paired-end reads (two read files) are supported for TopHat only.
- Not covered: R/edgeR code, GSEA, `cuffmerge`/`cuffdiff`, Salmon workflows, Markdown output.
- Not tested on Linux. No CI yet.
- Index files are not interchangeable between the legacy and modern tools. Rebuild them.
- The `samtools` sorting step mentioned in notes was not checked against its manual.

## Privacy and security

No network access, no telemetry, no subprocess calls. See `SECURITY.md` for the audit. It is a self-audit with automated tools and an AI reviewer, not an independent penetration test.

## Novelty check

A short search (GitHub, PyPI, web) on 20 November 2026 found no tool that rewrites TopHat/Cufflinks/Bowtie commands into modern ones. The search was limited (GitHub search returned no results pages, PyPI did not load, Bioconda not checked), so absence is not established. Existing material is manual migration guidance (for example Pertea et al., 2016 [2]) and pipelines such as auto-hisat2.

## Tests

```bash
pip install pytest
pytest
```

## References

1. Parikesit AA, Agustriawan D, Pradipta A. *Transcriptomics Computational Protocol*. i3L University, Jakarta; 2021. Zenodo record (version 1.0, deposited 2026): doi:10.5281/zenodo.24393837. https://zenodo.org/records/24393837
2. Pertea M, Kim D, Pertea GM, Leek JT, Salzberg SL. Transcript-level expression analysis of RNA-seq experiments with HISAT, StringTie and Ballgown. *Nature Protocols*. 2016;11(9):1650-1667. doi:10.1038/nprot.2016.095

AI Assistance Disclaimer: This codebase was developed with the assistance of Claude Code. While the AI provided code generation, debugging, and structural support, the human developer maintains full responsibility for reviewing, testing, and maintaining all content and functionality
