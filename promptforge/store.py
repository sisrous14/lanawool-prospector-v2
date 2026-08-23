"""Datele care supraviețuiesc între rulări: profiluri, feedback, lexicon învățat.

Totul stă în fișiere JSON simple, sub `~/.promptforge` (sau sub calea din
`PROMPTFORGE_HOME`). Nicio bază de date, nimic de configurat, ușor de citit și
de șters cu mâna.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def home() -> Path:
    configured = os.environ.get("PROMPTFORGE_HOME")
    return Path(configured) if configured else Path.home() / ".promptforge"


def path_for(name: str) -> Path:
    return home() / name


def read_json(name: str, default: Any) -> Any:
    """Citește un fișier JSON; un fișier corupt nu oprește programul."""
    target = path_for(name)
    if not target.exists():
        return default
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return default


def write_json(name: str, payload: Any) -> Path:
    target = path_for(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Scriere în două trepte: un fișier întrerupt la jumătate nu îl strică pe cel bun.
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(target)
    return target
