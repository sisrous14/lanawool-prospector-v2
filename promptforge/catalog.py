"""Catalogul de modele, platforme și dimensiuni.

Trei tabele care răspund la trei întrebări:

* `MODELS`    — unde trimit promptul, și cât mă costă;
* `PLATFORMS` — pentru ce rețea sau produs e conținutul, cu regulile ei;
* `SIZES`     — ce dimensiune are imaginea sau clipul, în pixeli.

Despre prețuri: eticheta e o orientare, nu un contract. Se schimbă des, așa
că fiecare intrare are și o notă cu ce înseamnă concret, iar `promptforge
modele` afișează un avertisment. Verifică pe site înainte să te bazezi.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Etichete de preț
FREE = "gratis"        # se poate folosi fără plată, inclusiv rulat local
FREEMIUM = "freemium"  # există nivel gratuit, cu limite; varianta bună e plătită
PAID = "platit"        # nu există nivel gratuit util


@dataclass
class ModelInfo:
    """Un model-țintă: unde ajunge promptul generat."""

    key: str
    label: str
    kind: str                      # "text" | "image" | "video"
    pricing: str
    pricing_note: str
    note: str = ""


MODELS: dict[str, ModelInfo] = {
    # --- TEXT ---------------------------------------------------------------
    "claude": ModelInfo(
        "claude", "Claude", "text", FREEMIUM,
        "claude.ai are nivel gratuit cu limite de mesaje; API-ul și abonamentul sunt plătite.",
        "Urmărește cel mai fidel secțiunile marcate cu etichete.",
    ),
    "gpt": ModelInfo(
        "gpt", "ChatGPT / GPT", "text", FREEMIUM,
        "ChatGPT are nivel gratuit; modelele bune și API-ul sunt plătite.",
        "Preferă titluri Markdown.",
    ),
    "gemini": ModelInfo(
        "gemini", "Gemini", "text", FREEMIUM,
        "Nivel gratuit generos în Google AI Studio; peste cotă se plătește.",
        "Structură Markdown, cerințe numerotate.",
    ),
    "deepseek": ModelInfo(
        "deepseek", "DeepSeek", "text", FREEMIUM,
        "Chat gratuit; API-ul e plătit, dar printre cele mai ieftine.",
        "Merge bine pe sarcini de cod și raționament.",
    ),
    "mistral": ModelInfo(
        "mistral", "Mistral", "text", FREEMIUM,
        "Le Chat are nivel gratuit; modelele deschise pot fi rulate local, gratuit.",
        "Instrucțiuni scurte și explicite.",
    ),
    "local": ModelInfo(
        "local", "Model local (Llama, Qwen, Gemma)", "text", FREE,
        "Complet gratuit dacă îl rulezi la tine; plătești doar curentul și placa video.",
        "Modelele mici au nevoie de prompturi mai scurte și mai directe.",
    ),
    "generic": ModelInfo(
        "generic", "Generic", "text", FREE,
        "Format neutru, fără marcaje — merge oriunde.",
    ),
    # --- IMAGINE ------------------------------------------------------------
    "flux": ModelInfo(
        "flux", "Flux", "image", FREEMIUM,
        "Flux schnell are greutăți deschise și e gratuit local; Flux pro se plătește la imagine.",
        "Urmărește bine limbajul natural descriptiv.",
    ),
    "sdxl": ModelInfo(
        "sdxl", "Stable Diffusion / SDXL", "image", FREE,
        "Greutăți deschise: gratuit dacă îl rulezi local. Serviciile găzduite se plătesc.",
        "Promptul negativ contează mult aici.",
    ),
    "midjourney": ModelInfo(
        "midjourney", "Midjourney", "image", PAID,
        "Nu are nivel gratuit; abonament lunar.",
        "Citește un paragraf continuu, nu secțiuni.",
    ),
    "dalle": ModelInfo(
        "dalle", "DALL·E / GPT Image", "image", FREEMIUM,
        "Câteva imagini pe zi în ChatGPT gratuit; peste atât, abonament sau API.",
        "Nu are prompt negativ.",
    ),
    "imagen": ModelInfo(
        "imagen", "Imagen / Gemini Image", "image", FREEMIUM,
        "Nivel gratuit în aplicația Gemini; API-ul se plătește la imagine.",
        "Preferă descrierea continuă.",
    ),
    "ideogram": ModelInfo(
        "ideogram", "Ideogram", "image", FREEMIUM,
        "Câteva generări gratuite pe zi; restul, abonament.",
        "Cel mai bun la text scris corect în imagine.",
    ),
    "generic-image": ModelInfo(
        "generic-image", "Generic (imagine)", "image", FREE,
        "Format neutru, ușor de adaptat la orice model.",
    ),
    # --- VIDEO --------------------------------------------------------------
    "sora": ModelInfo(
        "sora", "Sora", "video", PAID,
        "Necesită abonament ChatGPT; nu are nivel gratuit util.",
        "Acceptă descrieri lungi, cu mișcare de cameră explicită.",
    ),
    "veo": ModelInfo(
        "veo", "Veo", "video", FREEMIUM,
        "Câteva clipuri în nivelul gratuit Gemini; producția reală cere abonament.",
        "Bun la mișcare naturală și la sunet.",
    ),
    "kling": ModelInfo(
        "kling", "Kling", "video", FREEMIUM,
        "Credite gratuite zilnice; peste ele, abonament.",
        "Bun la animarea unei imagini de start.",
    ),
    "runway": ModelInfo(
        "runway", "Runway", "video", FREEMIUM,
        "Credite gratuite la înscriere, apoi abonament.",
        "Control fin pe mișcarea camerei.",
    ),
    "generic-video": ModelInfo(
        "generic-video", "Generic (video)", "video", FREE,
        "Format neutru pentru orice generator video.",
    ),
}

PRICING_LABEL = {
    FREE: "gratis",
    FREEMIUM: "freemium",
    PAID: "platit",
}

PRICING_DISCLAIMER = (
    "Prețurile și nivelurile gratuite se schimbă des. Eticheta de mai sus e o "
    "orientare de la momentul scrierii, nu o garanție — verifică pe site-ul "
    "furnizorului înainte să te bazezi pe ea."
)


def models_of(kind: str) -> list[ModelInfo]:
    return [model for model in MODELS.values() if model.kind == kind]


# ---------------------------------------------------------------------------
# Platforme
# ---------------------------------------------------------------------------


@dataclass
class Platform:
    """O rețea sau un produs, cu regulile lui de format.

    `rules` e indexat pe mod și apoi pe limbă: regulile intră direct în prompt,
    deci trebuie să fie în limba promptului, nu în limba interfeței.
    """

    key: str
    label: str
    aspect: str
    size: tuple[int, int]
    alt_sizes: dict[str, tuple[int, int]] = field(default_factory=dict)
    rules: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    limits: dict[str, str] = field(default_factory=dict)


PLATFORMS: dict[str, Platform] = {
    "tiktok": Platform(
        "tiktok", "TikTok", "9:16", (1080, 1920),
        alt_sizes={"coperta": (1080, 1920)},
        limits={
            "ro": "Descriere: până la 2200 de caractere, dar primele 60 sunt singurele vizibile fără atingere.",
            "en": "Caption: up to 2200 characters, but only the first 60 are visible without a tap.",
        },
        rules={
            "text": {
                "ro": [
                    "Cârligul intră în primele 3 secunde și în primele 8 cuvinte; fără introduceri.",
                    "Scrie pentru ureche, nu pentru ochi: fraze scurte, rostite natural, fără subordonate.",
                    "Textul de pe ecran repetă cârligul, nu îl completează — mulți se uită fără sunet.",
                    "Descrierea are maximum 150 de caractere utile; restul se taie vizual.",
                    "Trei-cinci hashtaguri, dintre care unul de nișă; nu douăzeci.",
                ],
                "en": [
                    "The hook lands in the first 3 seconds and the first 8 words; no preamble.",
                    "Write for the ear, not the eye: short spoken sentences, no subordinate clauses.",
                    "On-screen text repeats the hook rather than completing it — many watch without sound.",
                    "The caption has at most 150 useful characters; the rest is visually cut off.",
                    "Three to five hashtags, one of them niche; not twenty.",
                ],
            },
            "image": {
                "ro": [
                    "vertical 9:16, cu subiectul în treimea de sus — partea de jos e acoperită de interfață",
                    "zonă sigură: lasă 15% liber sus și 20% jos, unde stau butoanele și descrierea",
                    "contrast mare, subiect clar de la prima privire, citibil pe ecran mic",
                ],
                "en": [
                    "vertical 9:16 with the subject in the upper third — the lower area is covered by the interface",
                    "safe area: leave 15% clear at the top and 20% at the bottom, where buttons and caption sit",
                    "high contrast, subject clear at first glance, legible on a small screen",
                ],
            },
            "video": {
                "ro": [
                    "durată 15-34 de secunde; sub 15 pare rupt, peste 60 pierde audiența",
                    "tăietură sau schimbare de cadru la fiecare 2-3 secunde",
                    "primul cadru trebuie să funcționeze ca miniatură statică",
                ],
                "en": [
                    "duration 15-34 seconds; under 15 feels truncated, over 60 loses the audience",
                    "a cut or a change of framing every 2-3 seconds",
                    "the first frame must work as a static thumbnail",
                ],
            },
        },
    ),
    "instagram": Platform(
        "instagram", "Instagram", "4:5", (1080, 1350),
        alt_sizes={"patrat": (1080, 1080), "reel": (1080, 1920), "story": (1080, 1920)},
        limits={
            "ro": "Legendă: până la 2200 de caractere; primele 125 apar înainte de „mai mult”.",
            "en": "Caption: up to 2200 characters; the first 125 show before the `more` link.",
        },
        rules={
            "text": {
                "ro": [
                    "Primul rând e tot ce se vede înainte de „mai mult”: pune miza acolo.",
                    "Legenda are un singur mesaj; dacă ai două, sunt două postări.",
                    "Rânduri scurte, cu pauze albe între ele — se citește pe telefon, în mers.",
                    "Cinci până la zece hashtaguri, puse la final sau în primul comentariu.",
                ],
                "en": [
                    "The first line is all that shows before `more`: put the stake there.",
                    "One caption, one message; if you have two, that is two posts.",
                    "Short lines with white space between them — it is read on a phone, while walking.",
                    "Five to ten hashtags, at the end or in the first comment.",
                ],
            },
            "image": {
                "ro": [
                    "format 4:5 pentru feed (ocupă cel mai mult ecran) sau 1:1 pentru carusel",
                    "compoziție care rezistă și decupată pătrat, pentru grila de profil",
                    "paletă consecventă cu restul profilului, ca grila să arate unitar",
                ],
                "en": [
                    "4:5 for the feed (it occupies the most screen) or 1:1 for a carousel",
                    "a composition that survives a square crop, for the profile grid",
                    "a palette consistent with the rest of the profile, so the grid reads as one set",
                ],
            },
            "video": {
                "ro": [
                    "Reel: 9:16, 15-30 de secunde, cu buclă naturală la final",
                    "primele 2 secunde decid tot; începe în mijlocul acțiunii",
                ],
                "en": [
                    "Reel: 9:16, 15-30 seconds, with a natural loop at the end",
                    "the first 2 seconds decide everything; start in the middle of the action",
                ],
            },
        },
    ),
    "facebook": Platform(
        "facebook", "Facebook", "1.91:1", (1200, 628),
        alt_sizes={"patrat": (1080, 1080), "postare": (1200, 630), "coperta": (820, 312)},
        limits={
            "ro": "Textul reclamei: 125 de caractere recomandate; titlu 40; descriere 30.",
            "en": "Ad copy: 125 characters recommended; headline 40; description 30.",
        },
        rules={
            "text": {
                "ro": [
                    "Primele 125 de caractere sunt singurele garantate vizibile — pune oferta acolo.",
                    "Titlul are 40 de caractere; scrie beneficiul, nu numele produsului.",
                    "Ton conversațional; publicul e mai matur decât pe TikTok și reacționează la claritate.",
                    "Un singur apel la acțiune, explicit, cu ce se întâmplă după clic.",
                ],
                "en": [
                    "The first 125 characters are the only ones guaranteed visible — put the offer there.",
                    "The headline has 40 characters; write the benefit, not the product name.",
                    "Conversational tone; this audience is older than TikTok's and responds to clarity.",
                    "One call to action, explicit, stating what happens after the click.",
                ],
            },
            "image": {
                "ro": [
                    "format 1.91:1 pentru link, 1:1 pentru postare în feed",
                    "text pe imagine sub 20% din suprafață, altfel scade distribuția",
                    "subiectul rămâne lizibil la lățime de 400px, cum apare în feed",
                ],
                "en": [
                    "1.91:1 for a link post, 1:1 for a feed post",
                    "text over the image under 20% of the area, or reach drops",
                    "the subject stays legible at 400px wide, as it appears in the feed",
                ],
            },
            "video": {
                "ro": [
                    "1:1 sau 4:5, 15-60 de secunde, subtitrare arsă în imagine",
                    "85% se uită fără sunet: mesajul trebuie să treacă vizual",
                ],
                "en": [
                    "1:1 or 4:5, 15-60 seconds, subtitles burned into the image",
                    "85% watch without sound: the message has to land visually",
                ],
            },
        },
    ),
    "google": Platform(
        "google", "Google (Ads și căutare)", "1.91:1", (1200, 628),
        alt_sizes={"patrat": (1200, 1200), "logo": (1200, 1200), "portret": (960, 1200)},
        limits={
            "ro": "Ads: titlu 30 de caractere, descriere 90. SEO: title 60, meta description 155.",
            "en": "Ads: headline 30 characters, description 90. SEO: title 60, meta description 155.",
        },
        rules={
            "text": {
                "ro": [
                    "Titlul de anunț are FIX maximum 30 de caractere; numără-le, nu estima.",
                    "Descrierea are maximum 90 de caractere; scrie trei variante distincte.",
                    "Include cuvântul-cheie exact în titlu, pentru scorul de relevanță.",
                    "Pentru SEO: title sub 60 de caractere, meta description sub 155, ambele cu intenția de căutare explicită.",
                    "Fără majuscule integrale, fără semne de exclamare multiple — sunt respinse.",
                ],
                "en": [
                    "An ad headline is capped at EXACTLY 30 characters; count them, do not estimate.",
                    "The description is capped at 90 characters; write three distinct variants.",
                    "Include the exact keyword in the headline, for the relevance score.",
                    "For SEO: title under 60 characters, meta description under 155, both with explicit search intent.",
                    "No all-caps, no multiple exclamation marks — they are rejected.",
                ],
            },
            "image": {
                "ro": [
                    "trei formate obligatorii: 1.91:1, 1:1 și 4:5, toate cu același subiect",
                    "fără text suprapus: Google îl adaugă singur peste imagine",
                    "subiectul centrat, cu margini libere, ca decuparea automată să nu-l taie",
                ],
                "en": [
                    "three required formats: 1.91:1, 1:1 and 4:5, all with the same subject",
                    "no overlaid text: Google adds its own over the image",
                    "subject centred with clear margins, so automatic cropping does not cut it",
                ],
            },
            "video": {
                "ro": [
                    "16:9 pentru YouTube, 6 secunde pentru bumper, 15-30 pentru skippable",
                    "marca apare în primele 5 secunde, înainte de butonul de sărire",
                ],
                "en": [
                    "16:9 for YouTube, 6 seconds for a bumper, 15-30 for skippable",
                    "the brand appears in the first 5 seconds, before the skip button",
                ],
            },
        },
    ),
    "youtube": Platform(
        "youtube", "YouTube", "16:9", (1920, 1080),
        alt_sizes={"miniatura": (1280, 720), "shorts": (1080, 1920)},
        limits={
            "ro": "Titlu: 60 de caractere vizibile; descriere: primele 150 apar în rezultate.",
            "en": "Title: 60 visible characters; description: the first 150 show in results.",
        },
        rules={
            "text": {
                "ro": [
                    "Titlul sub 60 de caractere, cu promisiunea și cuvântul-cheie în prima jumătate.",
                    "Primele 150 de caractere din descriere apar în căutare: scrie-le ca pe un rezumat.",
                    "Structura videoclipului: cârlig, promisiune, livrare, recapitulare.",
                ],
                "en": [
                    "Title under 60 characters, with the promise and the keyword in the first half.",
                    "The first 150 characters of the description show in search: write them as a summary.",
                    "Video structure: hook, promise, delivery, recap.",
                ],
            },
            "image": {
                "ro": [
                    "miniatură 1280x720, cu maximum trei elemente și o singură emoție clară",
                    "text pe miniatură: maximum patru cuvinte, citibile la 120px lățime",
                ],
                "en": [
                    "thumbnail 1280x720, at most three elements and one clear emotion",
                    "thumbnail text: at most four words, legible at 120px wide",
                ],
            },
            "video": {
                "ro": [
                    "16:9 orizontal pentru video lung, 9:16 pentru Shorts",
                    "primele 15 secunde decid retenția; nu pune generic la început",
                ],
                "en": [
                    "16:9 horizontal for long video, 9:16 for Shorts",
                    "the first 15 seconds decide retention; no intro sequence at the start",
                ],
            },
        },
    ),
    "linkedin": Platform(
        "linkedin", "LinkedIn", "1.91:1", (1200, 627),
        alt_sizes={"patrat": (1080, 1080)},
        limits={
            "ro": "Postare: 3000 de caractere; primele 210 apar înainte de „vezi mai mult”.",
            "en": "Post: 3000 characters; the first 210 show before `see more`.",
        },
        rules={
            "text": {
                "ro": [
                    "Primele două rânduri sunt tot ce se vede: pune concluzia sau tensiunea acolo.",
                    "Fără jargon corporatist; o observație concretă bate zece adjective.",
                    "Paragrafe de un rând, cu spațiu între ele.",
                    "Maximum trei hashtaguri, profesionale.",
                ],
                "en": [
                    "The first two lines are all that shows: put the conclusion or the tension there.",
                    "No corporate jargon; one concrete observation beats ten adjectives.",
                    "One-line paragraphs with space between them.",
                    "At most three hashtags, professional ones.",
                ],
            },
            "image": {
                "ro": [
                    "1.91:1 pentru link, 1:1 pentru postare nativă",
                    "estetică sobră, fără efecte; publicul reacționează la claritate",
                ],
                "en": [
                    "1.91:1 for a link, 1:1 for a native post",
                    "restrained aesthetic, no effects; this audience responds to clarity",
                ],
            },
            "video": {
                "ro": ["1:1 sau 16:9, sub 90 de secunde, cu subtitrare"],
                "en": ["1:1 or 16:9, under 90 seconds, subtitled"],
            },
        },
    ),
    "x": Platform(
        "x", "X / Twitter", "16:9", (1600, 900),
        limits={
            "ro": "Postare: 280 de caractere fără abonament.",
            "en": "Post: 280 characters without a subscription.",
        },
        rules={
            "text": {
                "ro": [
                    "280 de caractere: fiecare cuvânt trebuie să câștige spațiul.",
                    "Prima propoziție e completă și funcționează singură, dacă e citată.",
                    "Fără hashtaguri decorative; unul, cel mult.",
                ],
                "en": [
                    "280 characters: every word has to earn its space.",
                    "The first sentence is complete and works alone, if quoted.",
                    "No decorative hashtags; one at most.",
                ],
            },
            "image": {
                "ro": ["16:9, subiect mare și clar, citibil în feed la lățime mică"],
                "en": ["16:9, large clear subject, legible in the feed at small width"],
            },
            "video": {
                "ro": ["16:9 sau 1:1, sub 45 de secunde"],
                "en": ["16:9 or 1:1, under 45 seconds"],
            },
        },
    ),
}


def platform_aspect(platform: str | None) -> str | None:
    entry = PLATFORMS.get(platform or "")
    return entry.aspect if entry else None


# ---------------------------------------------------------------------------
# Dimensiuni
# ---------------------------------------------------------------------------

# Dimensiuni uzuale, dincolo de cele legate de o platformă.
SIZES: dict[str, tuple[int, int]] = {
    "hd": (1280, 720),
    "fullhd": (1920, 1080),
    "4k": (3840, 2160),
    "patrat": (1080, 1080),
    "vertical": (1080, 1920),
    "a4-print": (2480, 3508),
    "coperta-carte": (1600, 2560),
    "banner-web": (1920, 640),
}


def parse_size(value: str) -> tuple[int, int]:
    """Acceptă „1080x1920”, „1080X1920” sau un nume din `SIZES`."""
    key = value.strip().lower()
    if key in SIZES:
        return SIZES[key]
    for platform in PLATFORMS.values():
        if key == platform.key:
            return platform.size
        if key in platform.alt_sizes:
            return platform.alt_sizes[key]
    separator = "x" if "x" in key else ("×" if "×" in key else "")
    if separator:
        left, _, right = key.partition(separator)
        if left.strip().isdigit() and right.strip().isdigit():
            width, height = int(left), int(right)
            if width > 0 and height > 0:
                return width, height
    raise ValueError(
        f"Dimensiune neînțeleasă: {value!r}. Dă-o ca „1080x1920” sau folosește "
        f"un nume cunoscut: {', '.join(sorted(SIZES))}."
    )


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def aspect_of(width: int, height: int) -> str:
    """Raportul de aspect redus, cu apropiere de formatele uzuale."""
    if width <= 0 or height <= 0:
        raise ValueError("Dimensiunile trebuie să fie pozitive.")

    ratio = width / height
    known = {
        "1:1": 1.0, "4:5": 0.8, "2:3": 2 / 3, "3:4": 0.75, "9:16": 9 / 16,
        "3:2": 1.5, "4:3": 4 / 3, "16:9": 16 / 9, "1.91:1": 1.91, "21:9": 21 / 9,
    }
    for name, value in known.items():
        if abs(ratio - value) < 0.015:
            return name

    divisor = _gcd(width, height)
    reduced_w, reduced_h = width // divisor, height // divisor
    if reduced_w <= 32 and reduced_h <= 32:
        return f"{reduced_w}:{reduced_h}"

    # Raportul exact e ilizibil (620:877). Căutăm cel mai apropiat raport simplu;
    # A4 devine astfel „5:7”, cum e numit de obicei, nu „0.71:1”.
    best, best_error = None, 1.0
    for denominator in range(1, 17):
        numerator = max(1, round(ratio * denominator))
        if numerator > 32:
            continue
        error = abs(numerator / denominator - ratio) / ratio
        if error < best_error:
            best, best_error = (numerator, denominator), error
    if best and best_error < 0.02:
        return f"{best[0]}:{best[1]}"
    return f"{ratio:.2f}:1"


def describe_size(width: int, height: int) -> str:
    megapixels = width * height / 1_000_000
    return f"{width}×{height} px ({aspect_of(width, height)}, {megapixels:.1f} MP)"
