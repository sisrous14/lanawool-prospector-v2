"""Istoricul prompturilor generate, salvat local ca JSONL."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .models import Brief, GeneratedPrompt


def default_path() -> Path:
    """Locația implicită a istoricului (`PROMPTFORGE_HOME` o poate schimba)."""
    home = os.environ.get("PROMPTFORGE_HOME")
    base = Path(home) if home else Path.home() / ".promptforge"
    return base / "history.jsonl"


def save(brief: Brief, result: GeneratedPrompt, path: Path | None = None) -> Path:
    """Adaugă o intrare în istoric și întoarce calea fișierului."""
    target = path or default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "idea": brief.idea,
        "mode": result.mode,
        "domain": result.domain,
        "target": result.target,
        "variant": result.variant,
        "word_count": result.word_count,
        "refined_by": result.refined_by,
        "prompt": result.full_text(),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return target


def load(limit: int = 20, path: Path | None = None) -> list[dict]:
    """Citește ultimele intrări din istoric, cele mai noi la început."""
    target = path or default_path()
    if not target.exists():
        return []
    entries: list[dict] = []
    with target.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # o linie coruptă nu strică tot istoricul
    return entries[-limit:][::-1]
