"""Config loader for xhs-viral-decoder.

Reads config.yaml from the skill root (or via env var XHS_VD_CONFIG).
Provides a single Config object accessible across all modules.
"""
import os
import sys
from pathlib import Path
from typing import Any


def _find_skill_root() -> Path:
    """Walk up from this file to find skill root (has manifest.json)."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "manifest.json").exists():
            return p
        p = p.parent
    raise FileNotFoundError("Could not find skill root (no manifest.json found)")


SKILL_ROOT = _find_skill_root()


class Config:
    """Lightweight config wrapper supporting attribute + dict access."""

    def __init__(self, data: dict):
        self._data = data
        for key, val in data.items():
            if isinstance(val, dict):
                setattr(self, key, Config(val))
            else:
                setattr(self, key, val)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict:
        return dict(self._data)


def _parse_simple_yaml(text: str) -> dict:
    """Parse the subset of YAML used in config.example.yaml.

    Avoids PyYAML dependency. Supports:
      - top-level keys
      - one level of nesting (key:\n  subkey: value)
      - inline lists [a, b, c]
      - quoted and unquoted scalars
      - # comments

    Not supported: multi-line strings, anchors, tags, deep nesting.
    """
    result: dict = {}
    stack: list = [(result, -1)]  # (dict, indent_level)

    for raw_line in text.splitlines():
        # Strip comments — but respect quotes
        stripped = raw_line
        in_quote = False
        quote_char = None
        for i, c in enumerate(raw_line):
            if c in ('"', "'") and not in_quote:
                in_quote, quote_char = True, c
            elif c == quote_char and in_quote:
                in_quote = False
            elif c == '#' and not in_quote:
                stripped = raw_line[:i]
                break
        line = stripped.rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        # pop stack to current indent level
        while stack and stack[-1][1] >= indent:
            stack.pop()
        parent = stack[-1][0]

        if not val:
            # nested dict
            new = {}
            parent[key] = new
            stack.append((new, indent))
        else:
            # parse value
            parent[key] = _parse_yaml_value(val)
    return result


def _parse_yaml_value(val: str) -> Any:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_value(p.strip()) for p in inner.split(",")]
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    if val.lower() in ("null", "~", ""):
        return None
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val[1:-1]
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def load_config(path: str = None) -> Config:
    """Load config.yaml. Falls back to config.example.yaml if user hasn't created one."""
    if path is None:
        path = os.environ.get("XHS_VD_CONFIG", str(SKILL_ROOT / "config.yaml"))
    p = Path(path)
    if not p.exists():
        example = SKILL_ROOT / "config.example.yaml"
        if example.exists():
            print(
                f"⚠️  {p} not found. Using {example} as fallback. "
                f"Copy it to config.yaml and edit your folder_token / open_id.",
                file=sys.stderr,
            )
            p = example
        else:
            raise FileNotFoundError(f"Config not found: {p}")
    text = p.read_text(encoding="utf-8")
    data = _parse_simple_yaml(text)
    return Config(data)
