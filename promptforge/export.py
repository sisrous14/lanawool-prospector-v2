"""Exportul rezultatelor în formatele uneltelor cu care lucrezi.

Formatul se ia din extensia fișierului: `.csv`, `.json`, `.md` sau `.txt`.
Nimic de configurat.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .models import GeneratedPrompt

FORMATS = ("csv", "json", "md", "txt")

_COLUMNS = [
    "index", "mod", "domeniu", "tinta", "cuvinte",
    "prompt", "prompt_negativ", "parametri", "observatii",
]


def infer_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in FORMATS:
        raise ValueError(
            f"Nu știu formatul {suffix!r}. Folosește o extensie dintre: "
            f"{', '.join('.' + f for f in FORMATS)}."
        )
    return suffix


def render(results: list[GeneratedPrompt], fmt: str) -> str:
    """Transformă rezultatele în formatul cerut."""
    if fmt == "json":
        return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)

    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_COLUMNS)
        for index, result in enumerate(results, start=1):
            writer.writerow([
                index, result.mode, result.domain, result.target, result.word_count,
                result.prompt, result.negative_prompt, result.parameters,
                " | ".join(result.notes),
            ])
        return buffer.getvalue()

    if fmt == "md":
        parts: list[str] = []
        for index, result in enumerate(results, start=1):
            header = f"## Varianta {index}" if len(results) > 1 else "## Prompt"
            parts.append(
                f"{header}\n\n"
                f"*{result.mode} · {result.domain} · {result.target} · "
                f"{result.word_count} cuvinte*\n\n"
                f"```\n{result.prompt}\n```"
            )
            if result.negative_prompt:
                parts.append(f"**Prompt negativ**\n\n```\n{result.negative_prompt}\n```")
            if result.parameters:
                parts.append(f"**Parametri**\n\n`{result.parameters}`")
            if result.notes:
                parts.append("\n".join(f"- {note}" for note in result.notes))
        return "\n\n".join(parts) + "\n"

    # txt: doar prompturile, separate, gata de copiat
    blocks = [result.full_text() for result in results]
    return ("\n\n" + "─" * 60 + "\n\n").join(blocks) + "\n"


def write(results: list[GeneratedPrompt], path: Path) -> str:
    """Scrie rezultatele în fișier și întoarce formatul folosit."""
    fmt = infer_format(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(results, fmt), encoding="utf-8")
    return fmt
