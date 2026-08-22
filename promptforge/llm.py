"""Accesul la modelul Claude, în singurul loc din program care îl atinge.

Motorul local nu are nevoie de nimic din acest fișier. Aici ajung doar
funcțiile opționale: rafinarea promptului și analiza imaginilor. Tot ce poate
merge prost — pachet lipsă, credențiale lipsă, rețea căzută, model
indisponibil — iese ca `ModelUnavailable`, cu un mesaj care spune ce să faci.
"""

from __future__ import annotations

from typing import Callable, Protocol

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_EFFORT = "high"
MAX_TOKENS = 16000


class ModelUnavailable(RuntimeError):
    """Modelul nu poate fi apelat; apelantul decide dacă e fatal."""


class Sender(Protocol):
    """Semnătura unui transport către model.

    Există ca să poată fi înlocuit în teste cu o funcție care întoarce un
    răspuns fix, fără rețea și fără chei.
    """

    def __call__(self, *, system: str, content: list[dict], model: str, effort: str) -> str:
        ...


def make_sender() -> Sender:
    """Transportul real, peste SDK-ul oficial Anthropic."""
    try:
        import anthropic
    except ImportError as exc:
        raise ModelUnavailable(
            "Pachetul `anthropic` nu este instalat. Rulează: pip install anthropic"
        ) from exc

    try:
        client = anthropic.Anthropic()
    except Exception as exc:
        raise ModelUnavailable(
            f"Nu am putut construi clientul Anthropic: {exc}. "
            "Setează ANTHROPIC_API_KEY sau autentifică-te cu `ant auth login`."
        ) from exc

    def send(*, system: str, content: list[dict], model: str, effort: str) -> str:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=system,
                thinking={"type": "adaptive"},
                output_config={"effort": effort},
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.AuthenticationError as exc:
            raise ModelUnavailable(
                "Credențiale Anthropic invalide sau lipsă (ANTHROPIC_API_KEY)."
            ) from exc
        except anthropic.NotFoundError as exc:
            raise ModelUnavailable(
                f"Modelul {model!r} nu este disponibil pentru acest cont. "
                "Alege altul cu --model."
            ) from exc
        except anthropic.RateLimitError as exc:
            raise ModelUnavailable(
                "Limită de rată atinsă; încearcă din nou peste puțin."
            ) from exc
        except anthropic.APIStatusError as exc:
            raise ModelUnavailable(f"Eroare API ({exc.status_code}): {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise ModelUnavailable(f"Eroare de rețea: {exc}") from exc

        if response.stop_reason == "refusal":
            raise ModelUnavailable("Modelul a refuzat cererea.")

        return "".join(block.text for block in response.content if block.type == "text")

    return send


def resolve_sender(sender: Sender | Callable | None) -> Sender:
    """Transportul dat de apelant, altfel cel real."""
    return sender if sender is not None else make_sender()
