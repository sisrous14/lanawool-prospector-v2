"""Încărcarea surselor vizuale: fișiere locale, adrese de imagine, pagini web.

Un fișier local ajunge la model codificat base64. O adresă de imagine este
trimisă ca URL, fără descărcare — modelul o citește singur. O pagină web este
citită aici: îi extragem textul și, dacă are una, imaginea de previzualizare.
"""

from __future__ import annotations

import base64
import mimetypes
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Limitele API-ului pentru imagini trimise base64.
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_LONG_EDGE = 1568          # peste atât, imaginea e redimensionată de model oricum
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_PAGE_CHARS = 6000

SUPPORTED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
]

_USER_AGENT = "PromptForge/1.1 (+https://github.com/sisrous14/lanawool-prospector-v2)"


class MediaError(RuntimeError):
    """Sursa nu a putut fi încărcată."""


@dataclass
class ImageRef:
    """O imagine pregătită pentru trimitere către model."""

    label: str                  # „imaginea 1”, folosit în instrucțiuni
    origin: str                 # calea sau adresa, pentru mesaje și istoric
    media_type: str = ""
    data: str = ""              # base64, pentru fișiere locale
    url: str = ""               # adresă directă, pentru imagini de pe web

    def to_block(self) -> dict:
        """Blocul de conținut acceptat de API."""
        if self.url:
            return {"type": "image", "source": {"type": "url", "url": self.url}}
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": self.media_type,
                "data": self.data,
            },
        }


@dataclass
class PageRef:
    """Textul unei pagini web, pentru prompturi pornite de la un articol."""

    origin: str
    title: str
    text: str
    preview_image: str = ""


def _detect_media_type(raw: bytes, hint: str = "") -> str:
    for magic, media_type in _MAGIC:
        if raw.startswith(magic):
            return media_type
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    guessed, _ = mimetypes.guess_type(hint)
    if guessed in SUPPORTED_TYPES:
        return guessed
    raise MediaError(
        f"Nu recunosc formatul pentru {hint or 'sursa dată'}. "
        f"Acceptate: JPEG, PNG, GIF, WebP."
    )


def _shrink(raw: bytes, media_type: str) -> tuple[bytes, str]:
    """Micșorează imaginea dacă depășește limita, folosind Pillow dacă există."""
    if len(raw) <= MAX_IMAGE_BYTES:
        return raw, media_type
    try:
        import io

        from PIL import Image
    except ImportError as exc:
        raise MediaError(
            f"Imaginea are {len(raw) // 1024} KB, peste limita de "
            f"{MAX_IMAGE_BYTES // 1024} KB. Instalează Pillow "
            f"(pip install pillow) pentru redimensionare automată, sau "
            f"micșoreaz-o manual."
        ) from exc

    image = Image.open(io.BytesIO(raw))
    image.thumbnail((MAX_LONG_EDGE, MAX_LONG_EDGE))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    shrunk = buffer.getvalue()
    if len(shrunk) > MAX_IMAGE_BYTES:
        raise MediaError("Imaginea rămâne prea mare și după redimensionare.")
    return shrunk, "image/jpeg"


def _fetch(url: str, limit: int) -> tuple[bytes, str]:
    if not url.lower().startswith(("http://", "https://")):
        raise MediaError(f"Accept doar adrese http sau https, nu {url!r}.")
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip()
            raw = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise MediaError(f"Adresa {url} a răspuns cu eroarea {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MediaError(f"Nu am putut accesa {url}: {exc}") from exc
    if len(raw) > limit:
        raise MediaError(f"Conținutul de la {url} depășește {limit // 1024} KB.")
    return raw, content_type


def is_url(source: str) -> bool:
    return source.lower().startswith(("http://", "https://"))


def load_image(source: str, label: str = "") -> ImageRef:
    """Încarcă o imagine dintr-un fișier local sau de la o adresă web."""
    label = label or "imaginea"

    if is_url(source):
        _, content_type = _fetch(source, MAX_IMAGE_BYTES)
        if content_type in SUPPORTED_TYPES:
            # Adresa e trimisă ca atare: modelul citește imaginea direct.
            return ImageRef(label=label, origin=source, url=source, media_type=content_type)
        page = load_page(source)
        if not page.preview_image:
            raise MediaError(
                f"{source} nu este o imagine ({content_type or 'tip necunoscut'}) "
                f"și nu are imagine de previzualizare."
            )
        return ImageRef(
            label=label, origin=page.preview_image,
            url=page.preview_image, media_type="",
        )

    path = Path(source).expanduser()
    if not path.is_file():
        raise MediaError(f"Nu găsesc fișierul {source}.")
    raw = path.read_bytes()
    if not raw:
        raise MediaError(f"Fișierul {source} este gol.")
    media_type = _detect_media_type(raw, path.name)
    raw, media_type = _shrink(raw, media_type)
    return ImageRef(
        label=label,
        origin=str(path),
        media_type=media_type,
        data=base64.standard_b64encode(raw).decode("ascii"),
    )


_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_ALT_RE = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image["\']',
    re.IGNORECASE,
)


def load_page(source: str) -> PageRef:
    """Citește o pagină web și extrage titlul, textul și imaginea de previzualizare."""
    raw, _ = _fetch(source, MAX_PAGE_BYTES)
    html = raw.decode("utf-8", errors="replace")

    title_match = _TITLE_RE.search(html)
    title = _TAG_RE.sub(" ", title_match.group(1)).strip() if title_match else ""

    image_match = _OG_IMAGE_RE.search(html) or _OG_IMAGE_ALT_RE.search(html)
    preview = image_match.group(1).strip() if image_match else ""
    if preview.startswith("//"):
        preview = "https:" + preview

    body = _SCRIPT_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", body)
    text = re.sub(r"&[a-z]+;|&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text and not preview:
        raise MediaError(f"Nu am extras nimic util din {source}.")

    return PageRef(
        origin=source,
        title=title,
        text=text[:MAX_PAGE_CHARS],
        preview_image=preview,
    )


def load_source(source: str, label: str = "") -> ImageRef | PageRef:
    """Încarcă o sursă fără să știi dinainte ce e: imagine sau pagină web.

    Un fișier local este întotdeauna o imagine. O adresă web poate fi oricare
    dintre ele, așa că decidem după tipul de conținut pe care îl trimite.
    """
    if not is_url(source):
        return load_image(source, label=label)

    _, content_type = _fetch(source, MAX_IMAGE_BYTES)
    if content_type in SUPPORTED_TYPES:
        return ImageRef(
            label=label or "imaginea", origin=source, url=source, media_type=content_type
        )
    return load_page(source)


def load_sources(sources: list[str]) -> list[ImageRef]:
    """Încarcă mai multe imagini, etichetate «imaginea 1», «imaginea 2»…"""
    if not sources:
        raise MediaError("Nu ai dat nicio imagine.")
    return [
        load_image(source, label=f"imaginea {index}")
        for index, source in enumerate(sources, start=1)
    ]
