"""Bucla de feedback: programul învață ce fel de prompturi îți plac.

Marchezi un rezultat ca bun sau slab, iar descriptorii din el își schimbă
scorul. La generările următoare, alegerea înclină spre cei cu scor pozitiv și
îi ocolește pe cei negativi.

Nu e învățare automată, e o listă de preferințe. Se poate citi, edita și șterge
cu mâna, iar `promptforge preferinte` o arată așa cum e.
"""

from __future__ import annotations

from . import store

FILE = "feedback.json"

# Peste acest scor un descriptor e „preferat”; sub minusul lui, e ocolit.
THRESHOLD = 1


def _load() -> dict[str, int]:
    data = store.read_json(FILE, {})
    if not isinstance(data, dict):
        return {}
    return {key: int(value) for key, value in data.items() if isinstance(value, (int, float))}


def record(descriptors: list[str], good: bool) -> dict[str, int]:
    """Notează descriptorii unui rezultat ca buni sau slabi."""
    scores = _load()
    step = 1 if good else -1
    for descriptor in descriptors:
        if descriptor:
            scores[descriptor] = scores.get(descriptor, 0) + step
    store.write_json(FILE, scores)
    return scores


def preferences() -> tuple[set[str], set[str]]:
    """Descriptorii preferați și cei de ocolit."""
    scores = _load()
    liked = {key for key, value in scores.items() if value >= THRESHOLD}
    disliked = {key for key, value in scores.items() if value <= -THRESHOLD}
    return liked, disliked


def summary(limit: int = 20) -> list[tuple[str, int]]:
    """Preferințele, cele mai puternice întâi."""
    scores = _load()
    return sorted(scores.items(), key=lambda item: (-abs(item[1]), item[0]))[:limit]


def reset() -> None:
    store.write_json(FILE, {})
