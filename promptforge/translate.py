"""Stratul de limbă română.

Două lucruri diferite:

1. `to_english` — traduce aproximativ subiectul unei imagini din română în
   engleză, offline. Modelele de imagine sunt antrenate pe engleză, iar un
   subiect românesc dă rezultate vizibil mai slabe. Traducerea e făcută cu un
   lexicon de termeni vizuali frecvenți, nu cu un model, deci este limitată:
   dacă prea puține cuvinte sunt recunoscute, funcția refuză să traducă și
   spune asta, în loc să livreze o engleză stricată.

2. `IMAGE_LABELS` și `IMAGE_PHRASES` — variantele românești ale blocurilor de
   prompt vizual, pentru `--lang ro`.

Termenii tehnici (85mm, f/1.8, softbox, golden hour, bokeh) rămân netraduși
și în varianta românească: așa sunt folosiți și în română de fotografi.
"""

from __future__ import annotations

import re

from . import store
from .vocab import normalize

LEXICON_FILE = "lexicon.json"

# Etichete: substantiv (n), adjectiv (adj), prepoziție (prep), determinant (det),
# verb la gerunziu/participiu (v), altele (x).
N, ADJ, PREP, DET, V, X = "n", "adj", "prep", "det", "v", "x"

# ---------------------------------------------------------------------------
# Lexicon româno-englez de termeni vizuali
# ---------------------------------------------------------------------------

LEXICON: dict[str, tuple[str, str]] = {}


def _add(pos: str, pairs: dict[str, str]) -> None:
    for ro, en in pairs.items():
        LEXICON[normalize(ro)] = (en, pos)


_add(DET, {
    "un": "a", "o": "a", "unui": "a", "unei": "a", "niste": "some",
    "acest": "this", "aceasta": "this", "acel": "that", "acea": "that",
    "doi": "two", "doua": "two", "trei": "three", "patru": "four",
    "cinci": "five", "multi": "many", "multe": "many", "cateva": "a few",
    "fiecare": "each", "toti": "all", "toate": "all",
})

_add(PREP, {
    "in": "in", "pe": "on", "la": "at", "sub": "under", "peste": "over",
    "langa": "next to", "intre": "between", "deasupra": "above",
    "dedesubt": "below", "cu": "with", "fara": "without", "din": "from",
    "catre": "towards", "spre": "towards", "prin": "through",
    "printre": "among", "de": "of", "dinspre": "from", "pana": "up to",
    "inspre": "toward", "impotriva": "against", "aproape": "near",
})

_add(X, {
    "si": "and", "sau": "or", "care": "", "ce": "", "al": "of", "ale": "of",
    "lui": "of", "ei": "of", "lor": "of", "iar": "and", "dar": "but",
})

# Oameni
_add(N, {
    "persoana": "person", "om": "man", "oameni": "people", "barbat": "man",
    "barbati": "men", "femeie": "woman", "femei": "women", "fata": "girl",
    "fete": "girls", "baiat": "boy", "baieti": "boys", "copil": "child",
    "copii": "children", "batran": "old man", "batrana": "old woman",
    "tanar": "young man", "tanara": "young woman", "bunic": "grandfather",
    "bunica": "grandmother", "mama": "mother", "tata": "father",
    "familie": "family", "prieten": "friend", "cuplu": "couple",
    "muncitor": "worker", "pescar": "fisherman", "bucatar": "chef",
    "medic": "doctor", "profesor": "teacher", "student": "student",
    "soldat": "soldier", "calugar": "monk", "dansator": "dancer",
    "dansatoare": "dancer", "muzician": "musician", "pictor": "painter",
    "scriitor": "writer", "cioban": "shepherd", "fermier": "farmer",
    "mireasa": "bride", "mire": "groom", "chip": "face", "ochi": "eyes",
    "mana": "hand", "maini": "hands", "par": "hair", "zambet": "smile",
    "privire": "gaze", "silueta": "silhouette", "portret": "portrait",
    "razboinic": "warrior", "cavaler": "knight", "vrajitor": "wizard",
    "vrajitoare": "witch", "erou": "hero", "regina": "queen", "rege": "king",
    "calator": "traveller", "turist": "tourist", "gradinar": "gardener",
})

# Animale
_add(N, {
    "pisica": "cat", "pisici": "cats", "caine": "dog", "caini": "dogs",
    "cal": "horse", "cai": "horses", "vaca": "cow", "oaie": "sheep",
    "pasare": "bird", "pasari": "birds", "vultur": "eagle", "bufnita": "owl",
    "vulpe": "fox", "lup": "wolf", "urs": "bear", "cerb": "deer",
    "iepure": "rabbit", "fluture": "butterfly",
    "albina": "bee", "sarpe": "snake", "elefant": "elephant", "leu": "lion",
    "tigru": "tiger", "maimuta": "monkey", "broasca": "frog",
    "veverita": "squirrel", "arici": "hedgehog", "dragon": "dragon",
    "pesti": "fish",
    "balena": "whale", "delfin": "dolphin", "papagal": "parrot",
})

# Natură
_add(N, {
    "munte": "mountain", "munti": "mountains", "deal": "hill", "vale": "valley",
    "camp": "field", "padure": "forest", "copac": "tree", "copaci": "trees",
    "frunza": "leaf", "frunze": "leaves", "floare": "flower", "flori": "flowers",
    "iarba": "grass", "rau": "river", "lac": "lake", "mare": "sea",
    "ocean": "ocean", "plaja": "beach", "val": "wave", "valuri": "waves",
    "piatra": "stone", "stanca": "rock", "nisip": "sand", "zapada": "snow",
    "gheata": "ice", "ploaie": "rain", "ceata": "fog", "nor": "cloud",
    "nori": "clouds", "cer": "sky", "soare": "sun", "luna": "moon",
    "stea": "star", "stele": "stars", "foc": "fire", "fum": "smoke",
    "apa": "water", "vant": "wind", "furtuna": "storm", "curcubeu": "rainbow",
    "apus": "sunset", "rasarit": "sunrise", "amurg": "dusk", "zori": "dawn",
    "noapte": "night", "dimineata": "morning", "seara": "evening",
    "iarna": "winter", "vara": "summer", "toamna": "autumn",
    "primavara": "spring", "desert": "desert", "insula": "island",
    "pestera": "cave", "cascada": "waterfall", "gradina": "garden",
    "parc": "park", "lumina": "light", "umbra": "shadow",
    "peisaj": "landscape", "natura": "nature", "scena": "scene",
    "fundal": "background", "orizont": "horizon", "poiana": "clearing",
    "camp de grau": "wheat field", "livada": "orchard", "vie": "vineyard",
})

# Oraș, clădiri, locuri
_add(N, {
    "oras": "city", "orase": "cities", "sat": "village", "strada": "street",
    "drum": "road", "poteca": "path", "pod": "bridge", "cladire": "building",
    "cladiri": "buildings", "casa": "house", "case": "houses",
    "apartament": "apartment", "camera": "room", "bucatarie": "kitchen",
    "dormitor": "bedroom", "birou": "office", "fereastra": "window",
    "ferestre": "windows", "usa": "door", "scara": "staircase",
    "perete": "wall", "acoperis": "roof", "turn": "tower",
    "biserica": "church", "castel": "castle", "far": "lighthouse",
    "moara": "mill", "hambar": "barn", "piata": "square", "cafenea": "cafe",
    "restaurant": "restaurant", "magazin": "shop", "piscina": "pool",
    "chei": "pier", "port": "harbour", "fatada": "facade", "balcon": "balcony",
    "curte": "courtyard", "atelier": "workshop", "biblioteca": "library",
    "muzeu": "museum", "gara": "train station", "hotel": "hotel",
})

# Vehicule și obiecte
_add(N, {
    "barca": "boat", "corabie": "ship", "masina": "car", "bicicleta": "bicycle",
    "tren": "train", "avion": "plane", "motocicleta": "motorcycle",
    "camion": "truck", "autobuz": "bus", "astronava": "spaceship",
    "robot": "robot", "masa": "table", "scaun": "chair", "pat": "bed",
    "canapea": "sofa", "lampa": "lamp", "carte": "book", "carti": "books",
    "ceas": "watch", "telefon": "phone", "calculator": "computer",
    "laptop": "laptop", "chitara": "guitar", "pian": "piano",
    "vioara": "violin", "palarie": "hat", "haina": "coat", "rochie": "dress",
    "camasa": "shirt", "pantofi": "shoes", "geanta": "bag",
    "umbrela": "umbrella", "cana": "mug", "pahar": "glass", "sticla": "bottle",
    "farfurie": "plate", "cutit": "knife", "paine": "bread", "cafea": "coffee",
    "ceai": "tea", "vin": "wine", "fruct": "fruit", "mar": "apple",
    "legume": "vegetables", "tort": "cake", "prajitura": "pastry",
    "supa": "soup", "paste": "pasta", "oglinda": "mirror", "tablou": "painting",
    "perna": "pillow", "covor": "rug", "plasa": "net", "plase": "nets",
    "unealta": "tool", "cheie": "key", "scrisoare": "letter", "harta": "map",
    "parfum": "perfume", "cutie": "box", "borcan": "jar", "lumanare": "candle",
    "fotografie": "photograph", "imagine": "image", "ilustratie": "illustration",
    "desen": "drawing", "pictura": "painting", "afis": "poster",
    "mancare": "food", "produs": "product", "bautura": "drink",
    "instrument": "instrument", "jucarie": "toy", "ochelari": "glasses",
})

# Materiale
_add(N, {
    "lemn": "wood", "metal": "metal", "beton": "concrete",
    "caramida": "brick", "hartie": "paper", "panza": "canvas",
    "matase": "silk", "lana": "wool", "bumbac": "cotton", "piele": "leather",
    "aur": "gold", "argint": "silver", "fier": "iron", "otel": "steel",
    "marmura": "marble", "ceramica": "ceramic", "catifea": "velvet",
})

# Adjective
_add(ADJ, {
    "batran": "old", "batrana": "old", "vechi": "old", "nou": "new",
    "noua": "new", "tanar": "young", "tanara": "young", "mare": "large",
    "mic": "small", "mica": "small", "inalt": "tall", "scund": "short",
    "lung": "long", "lunga": "long", "scurt": "short", "lat": "wide",
    "ingust": "narrow", "gros": "thick", "subtire": "thin",
    "frumos": "beautiful", "frumoasa": "beautiful", "trist": "sad",
    "trista": "sad", "vesel": "cheerful", "obosit": "tired",
    "obosita": "tired", "linistit": "calm", "linistita": "calm",
    "salbatic": "wild", "singur": "lone", "singura": "lone", "gol": "empty",
    "goala": "empty", "plin": "full", "plina": "full", "curat": "clean",
    "murdar": "dirty", "luminos": "bright", "luminoasa": "bright",
    "intunecat": "dark", "intunecata": "dark", "cald": "warm",
    "calda": "warm", "rece": "cold", "umed": "damp", "uscat": "dry",
    "ruginit": "rusty", "lucios": "glossy", "mat": "matte", "moale": "soft",
    "colorat": "colourful", "alb": "white", "alba": "white", "negru": "black",
    "neagra": "black", "rosu": "red", "rosie": "red", "albastru": "blue",
    "albastra": "blue", "verde": "green", "galben": "yellow",
    "portocaliu": "orange", "roz": "pink", "mov": "purple", "maro": "brown",
    "gri": "grey", "auriu": "golden", "argintiu": "silver",
    "transparent": "transparent", "elegant": "elegant", "moderna": "modern",
    "modern": "modern", "rustic": "rustic", "rustica": "rustic",
    "futurist": "futuristic", "misterios": "mysterious",
    "dramatic": "dramatic", "dramatica": "dramatic",
    "minimalist": "minimalist", "abandonat": "abandoned",
    "abandonata": "abandoned", "parasit": "abandoned", "parasita": "abandoned",
    "vopsit": "painted", "sculptat": "carved", "inflorit": "blooming",
    "ninsa": "snowy", "insorit": "sunlit", "insorita": "sunlit",
    "cetos": "foggy", "cetoasa": "foggy", "ploios": "rainy",
    "artizanal": "artisanal", "traditional": "traditional",
    "montan": "mountain", "urban": "urban", "rural": "rural",
    "veche": "old", "sprijinit": "leaning", "sprijinita": "leaning",
    "asezata": "seated", "intins": "stretched", "ascuns": "hidden",
    "ascunsa": "hidden", "deschis": "open", "deschisa": "open",
    "inchis": "closed", "inchisa": "closed", "ruginita": "rusty",
    "prafuit": "dusty", "prafuita": "dusty", "stralucitor": "glowing",
    "invechit": "weathered", "invechita": "weathered", "aspru": "rough",
    "neted": "smooth", "bogat": "rich", "simplu": "simple", "clara": "clear",
    "salbatica": "wild", "vibrant": "vibrant", "pastelat": "pastel",
})

# Verbe la gerunziu / stări
_add(V, {
    "asezat": "seated", "asezata": "seated", "zambind": "smiling",
    "privind": "looking", "tinand": "holding", "citind": "reading",
    "alergand": "running", "dormind": "sleeping", "lucrand": "working",
    "gatind": "cooking", "cantand": "singing", "dansand": "dancing",
    "plutind": "floating", "zburand": "flying", "mergand": "walking",
    "stand": "standing", "asteptand": "waiting", "gandind": "thinking",
    "reparand": "mending", "pescuind": "fishing", "pictand": "painting",
    "scriind": "writing", "ravasit": "dishevelled",
})

# Expresii de mai multe cuvinte, verificate înaintea cuvintelor izolate.
PHRASES: dict[str, tuple[str, str]] = {
    "in picioare": ("standing", V),
    "in fata": ("in front of", PREP),
    "in spate": ("behind", PREP),
    "in mijloc": ("in the middle of", PREP),
    "in departare": ("in the distance", X),
    "la apus": ("at sunset", X),
    "la rasarit": ("at sunrise", X),
    "la fereastra": ("by the window", X),
    "la masa": ("at the table", X),
    "in varsta": ("elderly", ADJ),
    "de aproape": ("close up", X),
    "cu susul in jos": ("upside down", X),
    "alb negru": ("black and white", ADJ),
    "alb si negru": ("black and white", ADJ),
    "intr-un": ("in a", PREP),
    "intr-o": ("in a", PREP),
    "dintr-un": ("from a", PREP),
    "dintr-o": ("from a", PREP),
    "printr-un": ("through a", PREP),
    # „X de <material>” devine adjectiv în engleză: „masă de lemn” -> „wooden table”.
    "de piatra": ("stone", ADJ),
    "de lemn": ("wooden", ADJ),
    "de sticla": ("glass", ADJ),
    "de metal": ("metal", ADJ),
    "de fier": ("iron", ADJ),
    "de otel": ("steel", ADJ),
    "de beton": ("concrete", ADJ),
    "de marmura": ("marble", ADJ),
    "de caramida": ("brick", ADJ),
    "de aur": ("golden", ADJ),
    "de argint": ("silver", ADJ),
    "de piele": ("leather", ADJ),
    "de hartie": ("paper", ADJ),
    "de ceramica": ("ceramic", ADJ),
}

# Sufixe de articol hotărât și de plural, încercate în ordine.
_SUFFIXES = ["ului", "elor", "ilor", "lui", "ele", "ile", "ul", "le", "ii", "a", "l", "i", "e"]

_TOKEN_RE = re.compile(r"[a-zăâîșşțţ]+|\d+|[^\sa-zăâîșşțţ\d]", re.IGNORECASE)


def learned() -> dict[str, str]:
    """Perechile române-engleze pe care le-ai corectat tu, salvate local."""
    data = store.read_json(LEXICON_FILE, {})
    if not isinstance(data, dict):
        return {}
    return {normalize(k): str(v) for k, v in data.items() if isinstance(v, str) and v.strip()}


def learn(romanian: str, english: str) -> None:
    """Reține o traducere dată de utilizator, ca data viitoare să o știe.

    Când corectezi subiectul unei imagini cu `--subject`, perechea ajunge aici.
    Lexiconul offline crește astfel cu fiecare corecție, fără niciun apel de rețea.
    """
    key = normalize(romanian).strip()
    value = english.strip()
    if not key or not value or key == normalize(value):
        return
    data = store.read_json(LEXICON_FILE, {})
    if not isinstance(data, dict):
        data = {}
    data[key] = value
    store.write_json(LEXICON_FILE, data)


def forget(romanian: str) -> bool:
    data = store.read_json(LEXICON_FILE, {})
    key = normalize(romanian).strip()
    if not isinstance(data, dict) or key not in data:
        return False
    del data[key]
    store.write_json(LEXICON_FILE, data)
    return True


def lookup_romanian(word: str) -> tuple[str, str] | None:
    """Caută un cuvânt românesc, încercând și formele articulate sau de plural.

    Întoarce perechea (traducere, parte de vorbire) sau None. Folosită și de
    detecția limbii: dacă lexiconul recunoaște cuvintele, textul e românesc.
    """
    key = normalize(word)
    if key in LEXICON:
        return LEXICON[key]
    for suffix in _SUFFIXES:
        if key.endswith(suffix) and len(key) - len(suffix) >= 3:
            stem = key[: -len(suffix)]
            if stem in LEXICON:
                return LEXICON[stem]
            # „pescarul” -> „pescar”, dar și „femeia” -> „femeie”
            for extra in ("e", "a", "u"):
                if stem + extra in LEXICON:
                    return LEXICON[stem + extra]
    return None


def _reorder_tagged(tagged: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Mută adjectivele înaintea substantivului, cum cere engleza."""
    out: list[tuple[str, str]] = []
    index = 0
    while index < len(tagged):
        word, pos = tagged[index]
        if pos == N:
            adjectives: list[tuple[str, str]] = []
            look = index + 1
            while look < len(tagged) and tagged[look][1] == ADJ:
                adjectives.append(tagged[look])
                look += 1
            out.extend(adjectives)
            out.append((word, pos))
            index = look
        else:
            out.append((word, pos))
            index += 1
    return [(word, pos) for word, pos in out if word]


def _insert_articles(tagged: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Adaugă „the” după o prepoziție, unde engleza îl cere iar româna nu.

    „pe plajă” se traduce „on the beach”, nu „on beach”. Se sare peste cazurile
    în care urmează deja un determinant sau un material folosit ca adjectiv.
    """
    out: list[tuple[str, str]] = []
    for index, (word, pos) in enumerate(tagged):
        out.append((word, pos))
        if pos != PREP or word in ("of", "with", "without"):
            continue
        # „într-un” devine deja „in a”: un al doilea articol ar da „in a the”.
        if word.split()[-1] in ("a", "an", "the", "some"):
            continue
        rest = tagged[index + 1:]
        if not rest:
            continue
        nxt_word, nxt_pos = rest[0]
        if nxt_pos in (DET, X) or nxt_word in ("a", "an", "the", "some"):
            continue
        if nxt_pos in (N, ADJ):
            out.append(("the", DET))
    return out


def to_english(text: str, min_coverage: float = 0.6) -> tuple[str, float]:
    """Traduce aproximativ un subiect vizual din română în engleză.

    Întoarce textul tradus și acoperirea — proporția cuvintelor de conținut
    recunoscute. Sub `min_coverage` textul original este întors neschimbat:
    o engleză pe jumătate ghicită e mai rea decât româna curată.
    """
    lowered = normalize(text)

    # O corecție salvată pentru exact această frază bate orice altceva.
    memory = learned()
    if lowered.strip() in memory:
        return memory[lowered.strip()], 1.0

    # Expresiile fixe se rezolvă întâi, ca „în picioare” să nu devină „in feet”.
    # Se înlocuiesc cu un marker numeric, fără spații: un marker cu spații ar fi
    # rupt de `split()` mai jos, iar fraza s-ar pierde.
    resolved: list[tuple[str, str]] = []
    # Fragmentele învățate intră în aceeași mecanică de expresii fixe.
    phrases = dict(PHRASES)
    for key, value in memory.items():
        phrases.setdefault(key, (value, N))
    for phrase, entry in sorted(phrases.items(), key=lambda kv: -len(kv[0])):
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            lowered = re.sub(pattern, f" \x00{len(resolved)}\x00 ", lowered)
            resolved.append(entry)

    tagged: list[tuple[str, str]] = []
    content = 0
    known = 0

    for raw in lowered.split():
        marker = re.fullmatch(r"\x00(\d+)\x00", raw)
        if marker:
            tagged.append(resolved[int(marker.group(1))])
            content += 1
            known += 1
            continue
        for token in _TOKEN_RE.findall(raw):
            if not token.isalpha():
                if token.isdigit():
                    tagged.append((token, X))
                continue
            entry = lookup_romanian(token)
            is_content = len(token) > 2
            if is_content:
                content += 1
            if entry:
                if is_content:
                    known += 1
                tagged.append(entry)
            else:
                tagged.append((token, N if is_content else X))

    coverage = known / content if content else 0.0
    if coverage < min_coverage:
        return text, coverage

    words = [word for word, _ in _insert_articles(_reorder_tagged(tagged))]
    result = " ".join(word for word in words if word)
    result = re.sub(r"\s+([,.;:!?])", r"\1", result)
    result = re.sub(r"\s{2,}", " ", result).strip()
    # „a old” -> „an old”
    result = re.sub(r"\ba ([aeiou])", r"an \1", result)
    return result, coverage


# ---------------------------------------------------------------------------
# Varianta românească a blocurilor de prompt vizual
# ---------------------------------------------------------------------------

IMAGE_LABELS: dict[str, str] = {
    "SUBJECT": "SUBIECT",
    "SETTING": "DECOR",
    "COMPOSITION": "COMPOZIȚIE",
    "CAMERA": "CAMERĂ ȘI OBIECTIV",
    "LIGHTING": "LUMINĂ",
    "COLOUR AND MOOD": "CULOARE ȘI ATMOSFERĂ",
    "STYLE": "STIL",
    "DETAIL": "DETALIU",
    "TECHNICAL": "CERINȚE TEHNICE",
    "MUST INCLUDE": "TREBUIE SĂ CONȚINĂ",
    "QUALITY GUARDS": "GARANȚII DE CALITATE",
    "ADDITIONAL DIRECTION": "INDICAȚIE SUPLIMENTARĂ",
    "COHERENCE": "COERENȚĂ",
    "FOCUS DISCIPLINE": "PRIORITATE",
    "OUTPUT SPECIFICATION": "SPECIFICAȚIE DE IEȘIRE",
    "PLATFORM RULES": "REGULI DE PLATFORMĂ",
}

# Frazele de legătură, în ordinea în care apar în image_engine.
IMAGE_PHRASES: dict[str, str] = {
    "subject_tail": (
        "Acesta este punctul focal unic al imaginii, iar toate alegerile de mai jos "
        "există ca să îl servească. Redă-l proeminent, fără ambiguitate și integral — "
        "nicio parte din subiectul principal nu este tăiată de cadru sau ascunsă în "
        "spatele altor elemente."
    ),
    "setting_head": "Plasat în",
    "setting_tail": (
        "Decorul susține subiectul și nu concurează niciodată cu el pentru atenție; "
        "elementele secundare rămân subordonate ca și contrast și detaliu."
    ),
    "composition_tail": (
        "Cadrul este echilibrat și intenționat, cu o ordine clară de citire pornind "
        "de la subiectul principal spre exterior."
    ),
    "camera_join": ", fotografiat cu",
    "camera_tail": (
        "Perspectiva este naturală și nedistorsionată, iar planul de focalizare cade "
        "exact pe subiect."
    ),
    "lighting_tail": (
        "O singură direcție coerentă a luminii guvernează întregul cadru; luminile "
        "sunt modelate, nu arse, iar umbrele păstrează detaliu."
    ),
    "mood_head": "Atmosfera generală este",
    "mood_tail": (
        "purtată de lumină și de relațiile dintre culori, nu de efecte adăugate."
    ),
    "style_tail": (
        "Tratamentul stilistic rămâne consecvent pe toată imaginea, fără amestec de "
        "abordări de randare incompatibile."
    ),
    "must_head": "Imaginea trebuie să conțină, clar vizibil:",
    "coherence": (
        "Fiecare element din cadru este plauzibil fizic: raporturile de scară se "
        "respectă, umbrele cad consecvent cu direcția de lumină indicată, reflexiile "
        "corespund surselor lor, iar materialele se comportă cum se comportă "
        "materialele reale în această lumină."
    ),
    "focus": (
        "Dacă vreo instrucțiune de mai sus intră în conflict cu alta, rezolvă în "
        "favoarea descrierii subiectului: un subiect clar, corect și bine luminat "
        "contează mai mult decât orice înfloritură stilistică."
    ),
    "guards": (
        "Cerințe tehnice formulate pozitiv: anatomia și mâinile trebuie să fie corecte "
        "și complete, focalizarea clară pe subiect, fundalul curat și neaglomerat, "
        "echilibrul de culoare natural și nu suprasaturat, suprafețele texturate și nu "
        "plasticoase, iar cadrul complet lipsit de text, filigran, semnătură sau logo."
    ),
    "guards_avoid": "Păstrează cadrul lipsit de",
}
