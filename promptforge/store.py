"""Datele care supraviețuiesc între rulări: profiluri, feedback, lexicon învățat.

Totul stă în fișiere JSON simple, sub `~/.promptforge` (sau sub calea din
`PROMPTFORGE_HOME`). Nicio bază de date, nimic de configurat, ușor de citit și
de șters cu mâna.

Două rulări în paralel — două comenzi date odată, sau interfața web servind
mai multe cereri — scriu în aceleași fișiere. De aceea scrierea trece printr-un
fișier temporar cu nume unic, iar actualizarea de tip citește-schimbă-scrie se
face sub o încuietoare, ca a doua rulare să nu piardă ce a scris prima.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

try:                                   # POSIX
    import fcntl
except ImportError:                    # pragma: no cover - Windows
    fcntl = None                       # type: ignore[assignment]

# Încuietoare în proces, pentru firele aceleiași rulări; `fcntl` o acoperă pe
# cea dintre procese diferite.
_LOCAL = threading.Lock()


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
    """Scrie atomic: întâi într-un temporar propriu, apoi mutare peste țintă.

    Numele temporarului conține procesul și un identificator unic. Cu un nume
    fix, două scrieri simultane și-ar fura fișierul una alteia și una ar cădea
    cu „No such file or directory”.
    """
    target = path_for(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(target)
    finally:
        # Dacă mutarea a eșuat, temporarul nu are voie să rămână în urmă.
        if temporary.exists():
            temporary.unlink(missing_ok=True)
    return target


@contextmanager
def _locked(name: str) -> Iterator[None]:
    """Încuietoare pe fișier, cât ține o actualizare."""
    lock_path = path_for(name).with_name(path_for(name).name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCAL:
        if fcntl is None:                       # pragma: no cover - Windows
            yield
            return
        handle = open(lock_path, "w", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()


def update_json(name: str, mutate: Callable[[Any], Any], default: Any) -> Any:
    """Citește, schimbă și scrie la loc, fără ca o rulare paralelă să se piardă.

    `mutate` primește conținutul actual și întoarce ce trebuie scris. Totul se
    petrece sub încuietoare, deci două comenzi date în același timp se adună în
    loc să se suprascrie.
    """
    with _locked(name):
        current = read_json(name, default)
        updated = mutate(current)
        write_json(name, updated)
        return updated
