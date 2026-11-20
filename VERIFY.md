# Rule verification sheet (for the human reviewer)

Prepared 2026-11-20. Evidence below is **verbatim text from the raw manual pages**, downloaded and grepped (not summarised by a model). Claude can gather evidence; **only you can set `checked = true`**, after reading the cited manual yourself. Tick a box only when you have confirmed it against the live page.

Evidence sources actually read:
- TopHat 2.1.1: https://ccb.jhu.edu/software/tophat/manual.shtml
- HISAT2 (no version shown on page): https://daehwankimlab.github.io/hisat2/manual/
- StringTie (no version on the page; README mentions 3.0.x): https://ccb.jhu.edu/software/stringtie/index.shtml?t=manual and https://github.com/gpertea/stringtie
- Cufflinks manual page https://cole-trapnell-lab.github.io/cufflinks/cufflinks/index.html, plus help text in https://github.com/cole-trapnell-lab/cufflinks/blob/master/src/cufflinks.cpp
- Bowtie1 and Bowtie2: the sourceforge manual pages returned HTTP 403 to automated download, so the evidence is from the `MANUAL` files in the authors' GitHub repos (BenLangmead/bowtie, BenLangmead/bowtie2). The rule files still cite the sourceforge URLs. **Confirm the sourceforge pages say the same.**

Status key: SUPPORTED = manual text matches the rule. PARTIAL = part of the rule is supported, part is this tool's own choice or inference. ISSUE = manual does not support the rule as written, needs your decision.

## Needs your decision first

1. **`bowtie:layout2` and `layout3` (ISSUE).** BI021 runs `bowtie -t index1/e_coli_0157_h7 reads.fq out.map`, with the index as a bare positional word. The current Bowtie1 manual usage is `bowtie [options]* -x <ebwt> {-1 <m1> -2 <m2> | --12 <r> | --interleaved <i> | <s>} [<hit>]`, which requires `-x`. The positional-index form is not documented in the manual I could download. It is probably the older (0.12.x) syntax. Decide: cite the old manual for that form, cite the BI021 protocol, or add support for `-x`. Until then the legacy side of this rule is unverified.
2. **`cufflinks:-o` (PARTIAL).** The Cufflinks manual page does not list `-o`. The program's own help text does: `-o/--output-dir   write all output files to this directory   [ default: ./ ]`. The rule now cites that source file. Confirm you accept the help text as the legacy source.
3. **The "no equivalent" claims** (TopHat `-N`, `--read-edit-dist`, `--read-realign-edit-dist`, `--max-coverage-intron`, `-M`) are claims of absence. Searching the HISAT2 page text found 0 hits for `read-mismatches`, `edit-dist`, `realign`, `max-coverage`, `coverage`, `prefilter`, `multihit`. Absence in one page is good evidence, not proof: please search the HISAT2 manual yourself.

## Per-rule evidence

### bowtie-build.toml
- [ ] **`bowtie-build:layout2` SUPPORTED.** Bowtie1: `bowtie-build [options]* <reference_in> <ebwt_base>`. Bowtie2: `bowtie2-build [options]* <reference_in> <bt2_base>`. Note: Bowtie1 index files end `.ebwt`/`.ebwtl`; Bowtie2 `.1.bt2`. Rebuild note is supported.

### bowtie2_build.toml
- [ ] **`bowtie2-build:layout2` SUPPORTED.** `bowtie2-build [options]* <reference_in> <bt2_base>`. The note that HISAT2 needs its own index is supported: HISAT2 `-x` says index files end ".1.ht2", `hisat2-build [options]* <reference_in> <ht2_base>`.

### bowtie.toml
- [ ] **`bowtie:layout2` / `layout3`** see decision 1. Modern side SUPPORTED: `bowtie2 [options]* -x <bt2-idx> {-1 <m1> -2 <m2> | -U <r> | ...} -S [<sam>]`; `-U <r>`: "Comma-separated list of files containing unpaired reads"; `-S <sam>`: "File to write SAM alignments to. By default, alignments are written to the "standard out" ...". Bowtie1 `<hit>`: "File to write alignments to. By default, alignments are written to the "standard out" filehandle". Bowtie1 native output: "8 fields separated by tabs" (supports the map-format note).
- [ ] **`bowtie:-t` SUPPORTED, wording differs.** Bowtie1: "Print the amount of wall-clock time taken by each phase." Bowtie2: "Print the wall-clock time required to load the index files and align the reads. This is printed to the "standard error" ("stderr") filehandle." Both `-t/--time`. The rule note matches.
- [ ] **`bowtie:-S` SUPPORTED.** Bowtie1: `-S/--sam` "Print alignments in SAM format." Bowtie2 `-S <sam>` takes a file name. The rule consumes the switch and maps the output positional to `-S <file>`.

### tophat.toml (legacy: TopHat 2.1.1, modern: HISAT2)
- [ ] **`tophat:layout2` / `layout3` SUPPORTED, with two caveats.** TopHat: `tophat [options]* <genome_index_base> <reads1_1[,...,readsN_1]> [reads1_2,...readsN_2]`. HISAT2: `hisat2 [options]* -x <hisat2-idx> {-1 <m1> -2 <m2> | -U <r> | --sra-acc <SRA accession number>} [-S <hit>]`. Caveat A: TopHat read arguments are comma-separated lists and may mix FASTA and FASTQ (since 2.0.10); HISAT2 `-f` declares FASTA reads, so a FASTA input needs `-f` (now in the note). Caveat B: TopHat `<genome_index_base>` is a Bowtie2 index, HISAT2 needs its own.
- [ ] **`tophat:-N` (dropped) SUPPORTED.** TopHat: "-N/--read-mismatches Final read alignments having more than these many mismatches are discarded. The default is 2." HISAT2 has only `--mp MX,MN` ("Sets the maximum (MX) and minimum (MN) mismatch penalties") and `--score-min` ("minimum alignment score needed for an alignment to be considered valid"). No hard mismatch cap found.
- [ ] **`tophat:--read-edit-dist` (dropped) SUPPORTED.** TopHat: "Final read alignments having more than these many edit distance are discarded. The default is 2." HISAT2 documents only the output tag `NM:i:<N> : The edit distance` (now cited in the note).
- [ ] **`tophat:--read-realign-edit-dist` (dropped) SUPPORTED.** TopHat: "...direct TopHat to re-align reads for which the edit distance of an alignment obtained in a previous mapping step is above or equal to this option value. If you set this option to 0, TopHat will map every read in all the mapping steps". No HISAT2 counterpart.
- [ ] **`tophat:-i` PARTIAL.** TopHat: "-i/--min-intron-length <int> The minimum intron length. TopHat will ignore donor/acceptor pairs closer than this many bases apart. The default is 70." HISAT2: "--min-intronlen <int> Sets minimum intron length. Default: 20". Same concept, defaults differ, HISAT2 text does not describe the donor/acceptor rule. Rule says approximate: correct.
- [ ] **`tophat:-I` PARTIAL.** TopHat: "-I/--max-intron-length <int> ... ignore donor/acceptor pairs farther than this many bases apart, except when such a pair is supported by a split segment alignment of a long read. The default is 500000." HISAT2: "--max-intronlen <int> Sets maximum intron length. Default: 500000". Defaults equal; the TopHat exception has no HISAT2 counterpart.
- [ ] **`tophat:--max-coverage-intron` (dropped) SUPPORTED.** TopHat: "The maximum intron length that may be found during coverage search. The default is 20000." No HISAT2 counterpart ("coverage" has 0 hits in the HISAT2 page).
- [ ] **`tophat:-M` (dropped) PARTIAL.** TopHat: "-M/--prefilter-multihits When mapping reads on the transcriptome, ... This option directs TopHat to first align the reads to the whole genome in order to determine and exclude such multi-mapped reads (according to the value of the -g/--max-multihits option)." The claim that it only matters in transcriptome-mapping mode follows from this text. HISAT2 has `-k <int>` ("searches for at most <int> distinct, primary alignments for each read"), which is related to `-g`, not `-M`. Your call whether dropping is acceptable for BI021 users.
- [ ] **`tophat:-o` PARTIAL.** TopHat: "-o/--output-dir <string> Sets the name of the directory in which TopHat will write all of its output. The default is "./tophat_out"." HISAT2: "-S <hit> File to write SAM alignments to. By default, alignments are written to the "standard out"". The mapping to `-S {dir}/hisat2_out.sam` is this tool's choice; the file name is not from any manual. Decide whether to keep it or warn only.
- Tool notes: TopHat/HISAT2 algorithm difference is a general statement, not a manual quote. `--dta`: "Report alignments tailored for transcript assemblers including StringTie." SUPPORTED. Samtools step: the StringTie manual says "the output of HISAT2 after sorting and converting it using samtools". SUPPORTED (samtools manual itself not read).

### cufflinks.toml (legacy: Cufflinks, modern: StringTie)
- [ ] **`cufflinks:layout1` SUPPORTED.** Cufflinks: `cufflinks [options] <aligned_reads.(sam/bam)>`. StringTie: `stringtie [-o <output.gtf>] [other_options] <read_alignments.bam>`; input "sorted by their genomic location (for example the accepted_hits.bam file produced by TopHat or the output of HISAT2 after sorting and converting it using samtools)". Cufflinks input must also be sorted: "must be sorted by reference position".
- [ ] **`cufflinks:-o` PARTIAL** see decision 2. StringTie: "-o [<path/>]<out.gtf> Sets the name of the output GTF file ... This can be specified as a full path, in which case directories will be created as needed. By default StringTie writes the GTF at standard output." The earlier note that the directory "must exist" was wrong and is corrected. File name `transcripts.gtf` is this tool's choice.
- [ ] **Tool note: `*.fpkm_tracking` replacements (inference).** Cufflinks formats page: "FPKM tracking files use a generic format to output estimated expression values." StringTie: "-A <gene_abund.tab> Gene abundances will be reported (tab delimited format) in the output file with the given name." Neither manual names the other as a replacement. The note now says this is the tool's inference. Keep, reword, or delete.
- [ ] **Tool note: TPM.** StringTie reports TPM and FPKM; Cufflinks reports FPKM. The StringTie page text was internally inconsistent on one column description earlier in this session, so read the output-column table yourself before relying on it.

## What I could not check

- Bowtie sourceforge pages (403). Evidence from GitHub MANUAL files.
- Whether any text exists in the full Cufflinks manual about `-o` beyond the help text.
- The samtools manual.
- Whether any rule is scientifically adequate for a given dataset: the tool maps flags, not biology. Mapping rates and results will differ.

## After you finish

For each rule you confirmed, change `checked = false` to `true` in `src/rnaseq_modernize/rules/*.toml` (layouts and flags each have their own `checked`). Then run `RELEASE_GATE=1 pytest`, update `REVIEW.md` ("Still open"), and tag.
