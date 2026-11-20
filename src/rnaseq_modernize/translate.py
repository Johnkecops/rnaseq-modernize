"""Pure text translation. No file, network or process access. shlex tokenises; no shell runs."""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field

from .rules import Tool

# Any of these in a line means the shell would do something we cannot model faithfully
# (operators, redirects, expansion, globbing, comments, escapes). Such lines are never translated.
# ponytail: whole-line refusal; split on operators and track quoting to translate more lines.
META = frozenset(";&|<>()`$*?[]{}~\\#!")


class NotTranslated(Exception):
    """Raised inside apply() when a command cannot be translated safely."""


@dataclass
class Item:
    line_no: int
    original: str
    status: str  # translated | not_translated | comment | blank | error
    output: str = ""
    reason: str = ""
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)


_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _fill(template: tuple[str, ...], values: dict[str, str]) -> list[str]:
    # single pass, so a substituted value is never re-scanned; never str.format (untrusted input)
    return [_PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), e) for e in template]


def apply(tool: Tool, args: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    positionals: list[str] = []
    used: list[tuple[str, str | None]] = []
    seen: set[int] = set()
    i = 0
    while i < len(args):
        tok = args[i]
        i += 1
        if not tok.startswith("-") or tok == "-":
            positionals.append(tok)
            continue
        name, eq, inline = tok.partition("=") if tok.startswith("--") else (tok, "", "")
        flag = tool.flags.get(name)
        if flag is None:
            raise NotTranslated(f"unknown flag {name}")
        if id(flag) in seen:
            raise NotTranslated(f"flag {name} given more than once")
        seen.add(id(flag))
        if not flag.takes_value:
            if eq:
                raise NotTranslated(f"flag {name} takes no value")
            used.append((name, None))
        elif eq:
            used.append((name, inline))
        elif i < len(args):
            used.append((name, args[i]))
            i += 1
        else:
            raise NotTranslated(f"flag {name} needs a value")
        if flag.takes_value and not used[-1][1]:
            raise NotTranslated(f"flag {name} has an empty value")
    layout = tool.layouts.get(len(positionals))
    if layout is None:
        raise NotTranslated(f"unexpected number of positional arguments ({len(positionals)})")
    out = _fill(layout.out, dict(zip(layout.names, positionals, strict=True)))
    notes = list(tool.notes)
    warnings: list[str] = []
    unverified: list[str] = []
    if layout.note:
        notes.append(layout.note)
    if not layout.checked:
        unverified.append(f"{tool.legacy}:layout{len(positionals)}")
    for name, value in used:
        flag = tool.flags[name]
        shown = name if value is None else f"{name} {value}"
        if flag.modern:
            out += _fill(flag.modern, {"value": value or ""})
            msg = f"{shown} -> {shlex.join(_fill(flag.modern, {'value': value or ''}))} ({flag.closeness}): {flag.note}"
            (notes if flag.closeness == "exact" else warnings).append(msg)
        elif flag.closeness == "none":
            warnings.append(f"{shown} dropped, no equivalent in {tool.modern}: {flag.note}")
        else:
            notes.append(f"{shown} consumed ({flag.closeness}): {flag.note}")
        if not flag.checked:
            unverified.append(f"{tool.legacy}:{flag.names[0]}")
    return out, notes, warnings, sorted(set(unverified))


def translate_line(line_no: int, original: str, tools: dict[str, Tool]) -> Item:
    s = original.strip()
    if not s:
        return Item(line_no, original, "blank")
    if s.startswith("#"):
        return Item(line_no, original, "comment")
    bad = sorted(set(s) & META)
    if bad:
        return Item(
            line_no,
            original,
            "not_translated",
            reason="shell operators or expansion characters present: " + " ".join(bad),
        )
    if any(not (c.isprintable() or c == "\t") for c in s):
        return Item(line_no, original, "not_translated", reason="control characters present")
    try:
        toks = shlex.split(s)
    except ValueError as exc:
        return Item(line_no, original, "error", reason=str(exc))
    if not toks:
        return Item(line_no, original, "blank")
    if any(t.startswith("=") for t in toks):  # zsh expands a leading = as a command lookup
        return Item(line_no, original, "not_translated", reason="word starts with =")
    tool = tools.get(os.path.basename(toks[0]))
    if tool is None:
        return Item(line_no, original, "not_translated", reason="unrecognised command")
    try:
        out, notes, warnings, unverified = apply(tool, toks[1:])
    except NotTranslated as exc:
        return Item(line_no, original, "not_translated", reason=str(exc))
    if toks[0] != tool.legacy:
        notes.append("path to the legacy binary was dropped; the modern tool is assumed on PATH")
    return Item(line_no, original, "translated", shlex.join(out), "", notes, warnings, unverified)


def translate_text(text: str, tools: dict[str, Tool]) -> list[Item]:
    items: list[Item] = []
    buf: list[str] = []
    start = 1
    for no, raw in enumerate(text.splitlines(), 1):
        if not buf:
            start = no
        if raw.endswith("\\") and (buf or not raw.lstrip().startswith("#")):
            buf.append(raw[:-1].strip())
            continue
        buf.append(raw.strip())
        items.append(translate_line(start, " ".join(b for b in buf if b), tools))
        buf = []
    if buf:  # file ended on a continuation backslash
        items.append(translate_line(start, " ".join(b for b in buf if b), tools))
    return items
