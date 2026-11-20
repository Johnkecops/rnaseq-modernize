"""Format translation results as plain text or JSON."""

from __future__ import annotations

import json

from .translate import Item

DISCLAIMER = (
    "Modern tools use different algorithms. Translated commands will not reproduce the legacy "
    "results exactly. Check every command and its output before use."
)


def _safe(text: str) -> str:
    """Make text safe to print into a comment: no control characters reach the terminal."""
    return "".join(c if c.isprintable() else " " if c == "\t" else "?" for c in text)


def _unverified(items: list[Item]) -> list[str]:
    return sorted({u for it in items for u in it.unverified})


def render_text(items: list[Item]) -> str:
    out = [f"# rnaseq-modernize: {DISCLAIMER}"]
    unv = _unverified(items)
    if unv:
        out.append("# DRAFT RULES, not yet human-verified against the manuals: " + ", ".join(unv))
    for it in items:
        if it.status == "blank":
            out.append("")
        elif it.status == "comment":
            out.append(_safe(it.original))
        elif it.status == "translated":
            out.append(f"# line {it.line_no}: translated")
            out.append(f"# legacy: {_safe(it.original)}")
            out.append(it.output)
            out += [f"# note: {n}" for n in it.notes]
            out += [f"# WARNING: {w}" for w in it.warnings]
        else:
            label = "ERROR" if it.status == "error" else "NOT TRANSLATED, check manually"
            out.append(f"# line {it.line_no}: {label} ({_safe(it.reason)})")
            out.append(
                f"# {_safe(it.original)}"
            )  # kept literally but commented out: never runnable
    return "\n".join(out) + "\n"


def render_json(items: list[Item]) -> str:
    doc = {
        "disclaimer": DISCLAIMER,
        "unverified_rules": _unverified(items),
        "lines": [
            {
                "line": it.line_no,
                "status": it.status,
                "original": it.original,
                "output": it.output,
                "reason": it.reason,
                "notes": it.notes,
                "warnings": it.warnings,
            }
            for it in items
            if it.status != "blank"
        ],
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
