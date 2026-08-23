"""Profiluri salvate: opțiunile pe care le repeți de fiecare dată.

    promptforge preset salveaza produsele-mele --target flux --style "..." --aspect 1:1
    promptforge image "o cana de cafea" --preset produsele-mele

Un profil e doar un set de opțiuni pentru `Brief`. Ce dai în linia de comandă
bate întotdeauna ce e în profil.
"""

from __future__ import annotations

from . import store

FILE = "presets.json"

# Câmpurile pe care un profil are voie să le fixeze.
ALLOWED = {
    "mode", "domain", "target", "audience", "tone", "style", "aspect",
    "platform", "lang", "must", "avoid", "min_words", "max_words",
    "width", "height", "duration", "seed",
}


class PresetError(ValueError):
    """Profilul cerut nu există sau conține ceva nepermis."""


def all_presets() -> dict[str, dict]:
    data = store.read_json(FILE, {})
    return data if isinstance(data, dict) else {}


def get(name: str) -> dict:
    presets = all_presets()
    if name not in presets:
        known = ", ".join(sorted(presets)) or "niciunul"
        raise PresetError(f"Nu am profilul {name!r}. Salvate: {known}.")
    return dict(presets[name])


def save(name: str, options: dict) -> dict:
    """Salvează un profil, păstrând doar câmpurile cu valoare."""
    if not name.strip():
        raise PresetError("Profilul are nevoie de un nume.")

    unknown = set(options) - ALLOWED
    if unknown:
        raise PresetError(
            f"Câmpuri nepermise într-un profil: {', '.join(sorted(unknown))}. "
            f"Permise: {', '.join(sorted(ALLOWED))}."
        )

    cleaned = {
        key: value for key, value in options.items()
        if value not in (None, "", [], 0) or key == "seed"
    }
    def adauga(current: object) -> dict:
        saved = dict(current) if isinstance(current, dict) else {}
        saved[name.strip()] = cleaned
        return saved

    store.update_json(FILE, adauga, {})
    return cleaned


def delete(name: str) -> None:
    if name not in all_presets():
        raise PresetError(f"Nu am profilul {name!r}.")

    def sterge(current: object) -> dict:
        saved = dict(current) if isinstance(current, dict) else {}
        saved.pop(name, None)
        return saved

    store.update_json(FILE, sterge, {})


def apply(name: str, overrides: dict) -> dict:
    """Combină profilul cu opțiunile din linia de comandă.

    Ce a scris omul acum are prioritate; listele se adună, restul se înlocuiesc.
    """
    merged = get(name)
    for key, value in overrides.items():
        if value in (None, "", []):
            continue
        if key in ("must", "avoid") and isinstance(value, list):
            merged[key] = list(merged.get(key, [])) + value
        else:
            merged[key] = value
    return merged
