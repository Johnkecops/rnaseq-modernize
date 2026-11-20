import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rnaseq_modernize.cli import main
from rnaseq_modernize.rules import load_tools
from rnaseq_modernize.translate import META, translate_text

TOOLS = load_tools()
ROOT = Path(__file__).parent.parent


def one(cmd: str):
    items = translate_text(cmd, TOOLS)
    assert len(items) == 1
    return items[0]


# Golden tests: expected output written by hand from the cited manuals' usage lines.
GOLDEN = {
    "bowtie-build NC_008253.fna e_coli_0157_h7": "bowtie2-build NC_008253.fna e_coli_0157_h7",
    "bowtie -t index1/e_coli_0157_h7 reads/e_coli_1000.fq e_coli1.map": (
        "bowtie2 -x index1/e_coli_0157_h7 -U reads/e_coli_1000.fq -S e_coli1.map -t"
    ),
    "bowtie -S index1/e_coli_0157_h7 reads/e_coli_1000.fq e_coli1.sam": (
        "bowtie2 -x index1/e_coli_0157_h7 -U reads/e_coli_1000.fq -S e_coli1.sam"
    ),
    "bowtie2-build chr20.fa chr20": "bowtie2-build chr20.fa chr20",
    "tophat -N 3 --read-edit-dist 5 --read-realign-edit-dist 2 -i 50 -I 5000 "
    "--max-coverage-intron 5000 -M -o out index/chr20 reads.fastq": (
        "hisat2 -x index/chr20 -U reads.fastq --min-intronlen 50 --max-intronlen 5000 "
        "-S out/hisat2_out.sam"
    ),
    "tophat idx r1.fq r2.fq": "hisat2 -x idx -1 r1.fq -2 r2.fq",
    "tophat --min-intron-length=60 idx r.fq": "hisat2 -x idx -U r.fq --min-intronlen 60",
    "cufflinks -o tophat.cufflinks tophat.out/accepted_hits.bam": (
        "stringtie tophat.out/accepted_hits.bam -o tophat.cufflinks/transcripts.gtf"
    ),
    "/opt/tophat-2.1.1/tophat idx r.fq": "hisat2 -x idx -U r.fq",
}


@pytest.mark.parametrize("cmd,expected", GOLDEN.items())
def test_golden(cmd: str, expected: str) -> None:
    it = one(cmd)
    assert it.status == "translated"
    assert it.output == expected


def test_dropped_flags_warn() -> None:
    it = one("tophat -N 3 -M idx r.fq")
    assert len([w for w in it.warnings if "dropped" in w]) == 2


def test_fixture_file_full_set() -> None:
    items = translate_text((ROOT / "fixtures/bi021_commands.sh").read_text(), TOOLS)
    statuses = [i.status for i in items]
    assert statuses.count("translated") == 6
    assert "not_translated" not in statuses and "error" not in statuses
    assert items[5].line_no == 6  # continuation joined, line number is where the command starts


def test_unknown_flag_not_translated() -> None:
    it = one("tophat --no-novel-juncs idx r.fq")
    assert it.status == "not_translated" and "unknown flag" in it.reason


def test_unknown_command_not_translated() -> None:
    assert one("samtools sort a.bam").status == "not_translated"


def test_bad_arity_and_missing_value() -> None:
    assert one("tophat idx").status == "not_translated"
    assert one("tophat idx r.fq -i").status == "not_translated"
    assert one("tophat -M=1 idx r.fq").status == "not_translated"


def test_comments_blank_empty() -> None:
    assert translate_text("", TOOLS) == []
    st = [i.status for i in translate_text("# hi\n\n   \ncufflinks a.bam\n", TOOLS)]
    assert st == ["comment", "blank", "blank", "translated"]


def test_trailing_backslash_at_eof() -> None:
    it = translate_text("cufflinks \\", TOOLS)[0]
    assert it.status == "not_translated"  # zero positionals, no crash


# Hostile input: never executed, never crash, never silently translated.
HOSTILE = [
    "tophat idx r.fq; rm -rf ~",
    "tophat idx r.fq && touch PWNED",
    "tophat idx `touch PWNED`",
    "tophat idx $(touch PWNED)",
    "tophat idx r.fq | tee x",
    "tophat idx r.fq > out.txt",
    "tophat idx r.fq &",
    "tophat idx $HOME/r.fq",
    "tophat idx *.fq",
    "tophat idx r.fq # trailing",
    "tophat idx '{value}' ",
]


@pytest.mark.parametrize("line", HOSTILE)
def test_hostile_not_translated(line: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    it = one(line)
    assert it.status == "not_translated"
    assert it.original == line.strip()
    assert not (tmp_path / "PWNED").exists()


def test_unbalanced_quote_is_error_exit_1(capsys: pytest.CaptureFixture[str]) -> None:
    assert one("tophat idx 'r.fq").status == "error"
    assert main(["tophat idx 'r.fq"]) == 1
    out = capsys.readouterr().out
    assert "# tophat idx 'r.fq" in out  # kept literally, commented out


def test_quoted_value_requoted_safely() -> None:
    it = one("tophat idx 'my reads.fq'")
    assert it.output == "hisat2 -x idx -U 'my reads.fq'"


def test_long_line_clean() -> None:
    it = one("foo " + "a" * 200_000)
    assert it.status == "not_translated"
    it = one("tophat idx " + ",".join(["r.fq"] * 20_000))
    assert it.status == "translated"


def test_non_utf8_file_clean_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "bad.sh"
    f.write_bytes(b"tophat idx r\xff.fq\n")
    assert main(["-f", str(f)]) == 2
    assert "cannot read input" in capsys.readouterr().err


def test_null_and_control_bytes_no_crash() -> None:
    for s in ("tophat idx r\x00.fq", "tophat\x0bidx r.fq\x1b[31m"):
        for it in translate_text(s, TOOLS):
            assert it.status in {"translated", "not_translated", "error", "blank"}


def test_template_injection_impossible() -> None:
    # braces are in META so a value cannot smuggle a placeholder into a later substitution
    assert "{" in META and one("tophat idx {value}.fq").status == "not_translated"


def test_output_file_no_overwrite(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "o.txt"
    assert main(["tophat idx r.fq", "-o", str(out)]) == 0
    first = out.read_text()
    assert main(["tophat idx other.fq", "-o", str(out)]) == 2
    assert out.read_text() == first
    assert main(["tophat idx other.fq", "-o", str(out), "--force"]) == 0
    assert "other.fq" in out.read_text()


def test_json_output() -> None:
    items = translate_text("tophat idx r.fq", TOOLS)
    from rnaseq_modernize.emit import render_json

    doc = json.loads(render_json(items))
    assert doc["lines"][0]["output"] == "hisat2 -x idx -U r.fq"
    assert "different algorithms" in doc["disclaimer"]
    assert doc["unverified_rules"]


def test_text_output_states_difference_and_comments_out_untranslated() -> None:
    from rnaseq_modernize.emit import render_text

    text = render_text(translate_text("tophat idx r.fq; rm x", TOOLS))
    assert "different algorithms" in text
    assert "\n# tophat idx r.fq; rm x\n" in text
    assert "\ntophat" not in text


def test_cli_via_subprocess_stdin(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "rnaseq_modernize.cli", "-f", "-"],
        input=b"cufflinks a.bam\n",
        capture_output=True,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        check=False,
    )
    assert r.returncode == 0 and b"stringtie a.bam" in r.stdout


# Rule tests
def test_every_rule_has_source_url() -> None:
    for tool in TOOLS.values():
        for rid, url, _ in tool.rule_ids():
            assert url.startswith("https://"), rid


def test_every_flag_rule_is_exercised() -> None:
    # each flag name in the rule files must translate (or drop) without raising
    for tool in TOOLS.values():
        layout = next(iter(tool.layouts.values()))
        base = [f"p{i}" for i in range(len(layout.names))]
        for name, flag in tool.flags.items():
            args = [name] + (["7"] if flag.takes_value else []) + base
            it = translate_text(f"{tool.legacy} " + " ".join(args), TOOLS)[0]
            assert it.status == "translated", (tool.legacy, name, it.reason)


@pytest.mark.skipif(os.environ.get("RELEASE_GATE") != "1", reason="release gate only")
def test_every_rule_human_checked() -> None:
    unchecked = [rid for t in TOOLS.values() for rid, _, ok in t.rule_ids() if not ok]
    assert not unchecked, unchecked
