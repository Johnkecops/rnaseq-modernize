"""Command-line entry point. Reads one input, writes to stdout or an explicit new file."""

from __future__ import annotations

import argparse
import sys

from .emit import render_json, render_text
from .rules import load_tools
from .translate import translate_text

MAX_BYTES = 10_000_000


def _read(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read(MAX_BYTES + 1)
    with open(path, "rb") as fh:
        return fh.read(MAX_BYTES + 1)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="rnaseq-modernize",
        description="Print modern equivalents of legacy RNA-seq commands. Text only: nothing is run.",
    )
    p.add_argument("command", nargs="?", help="one legacy command as a single quoted string")
    p.add_argument("-f", "--file", help="script or text file of commands ('-' for stdin)")
    p.add_argument("--json", action="store_true", help="JSON output instead of text")
    p.add_argument("-o", "--output", help="write to this new file instead of stdout")
    p.add_argument("--force", action="store_true", help="allow --output to overwrite")
    args = p.parse_args(argv)
    if (args.command is None) == (args.file is None):
        p.error("give exactly one of: a command string, or --file")

    try:
        if args.file is not None:
            raw = _read(args.file)
            if len(raw) > MAX_BYTES:
                print(f"error: input larger than {MAX_BYTES} bytes", file=sys.stderr)
                return 2
            text = raw.decode("utf-8")
        else:
            text = args.command
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 2

    items = translate_text(text, load_tools())
    result = render_json(items) if args.json else render_text(items)

    if args.output:
        try:
            with open(args.output, "w" if args.force else "x", encoding="utf-8") as fh:
                fh.write(result)
        except FileExistsError:
            print(f"error: {args.output} exists; use --force to overwrite", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"error: cannot write output: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(result)
    return 1 if any(it.status == "error" for it in items) else 0


if __name__ == "__main__":
    sys.exit(main())
