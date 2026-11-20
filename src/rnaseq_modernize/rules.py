"""Load and validate the TOML rule files. tomllib only; no code is loaded from rule data."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CLOSENESS = frozenset({"exact", "approximate", "none"})
RULES_DIR = Path(__file__).parent / "rules"


@dataclass(frozen=True)
class Flag:
    names: tuple[str, ...]
    takes_value: bool
    modern: tuple[str, ...]
    closeness: str
    note: str
    legacy_source: str
    modern_source: str
    checked: bool


@dataclass(frozen=True)
class Layout:
    names: tuple[str, ...]
    out: tuple[str, ...]
    note: str
    source: str
    checked: bool


@dataclass(frozen=True)
class Tool:
    legacy: str
    modern: str
    versions: str
    notes: tuple[str, ...]
    layouts: dict[int, Layout] = field(default_factory=dict)
    flags: dict[str, Flag] = field(default_factory=dict)

    def rule_ids(self) -> list[tuple[str, str, bool]]:
        """(rule id, source url, human-checked) for every rule. Used by tests and the gate."""
        rows = [
            (f"{self.legacy}:layout{n}", lay.source, lay.checked) for n, lay in self.layouts.items()
        ]
        seen: set[int] = set()
        for flag in self.flags.values():
            if id(flag) in seen:
                continue
            seen.add(id(flag))
            rows.append((f"{self.legacy}:{flag.names[0]}", flag.modern_source, flag.checked))
            rows.append((f"{self.legacy}:{flag.names[0]}:legacy", flag.legacy_source, flag.checked))
        return rows


def _str(d: dict[str, object], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str):
        raise TypeError(f"rule key {key!r} must be a string")
    return v


def _strs(d: dict[str, object], key: str) -> tuple[str, ...]:
    v = d.get(key)
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise ValueError(f"rule key {key!r} must be a list of strings")
    return tuple(v)


def _bool(d: dict[str, object], key: str) -> bool:
    v = d.get(key)
    if not isinstance(v, bool):
        raise TypeError(f"rule key {key!r} must be true or false")
    return v


def parse_tool(data: dict[str, object]) -> Tool:
    meta = data.get("tool")
    if not isinstance(meta, dict):
        raise TypeError("missing [tool] table")
    tool = Tool(
        legacy=_str(meta, "legacy"),
        modern=_str(meta, "modern"),
        versions=_str(meta, "versions"),
        notes=_strs(meta, "notes"),
    )
    for lay in data.get("layout", []):  # type: ignore[attr-defined]
        names = _strs(lay, "names")
        tool.layouts[len(names)] = Layout(
            names, _strs(lay, "out"), _str(lay, "note"), _str(lay, "source"), _bool(lay, "checked")
        )
    for fl in data.get("flag", []):  # type: ignore[attr-defined]
        closeness = _str(fl, "closeness")
        if closeness not in CLOSENESS:
            raise ValueError(f"closeness must be one of {sorted(CLOSENESS)}")
        flag = Flag(
            _strs(fl, "names"),
            _bool(fl, "takes_value"),
            _strs(fl, "modern"),
            closeness,
            _str(fl, "note"),
            _str(fl, "legacy_source"),
            _str(fl, "modern_source"),
            _bool(fl, "checked"),
        )
        for name in flag.names:
            tool.flags[name] = flag
    return tool


def load_tools(directory: Path = RULES_DIR) -> dict[str, Tool]:
    tools: dict[str, Tool] = {}
    for path in sorted(directory.glob("*.toml")):
        with path.open("rb") as fh:
            tool = parse_tool(tomllib.load(fh))
        tools[tool.legacy] = tool
    return tools
