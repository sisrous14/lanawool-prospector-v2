"""Explicația fiecărei secțiuni: de ce e acolo și ce se schimbă fără ea.

Se afișează cu `--explain`. Scopul e să nu rămâi dependent de program: după
câteva rulări știi singur ce contează într-un prompt și ce e decor.
"""

from __future__ import annotations

_TEXT = {
    "ROL": "Fixează expertiza și standardul. Fără el, modelul răspunde ca un asistent generalist: corect, dar fără judecata cuiva care a mai făcut asta.",
    "CONTEXT ȘI OBIECTIV": "Reia cererea ta cuvânt cu cuvânt și spune ce înseamnă „gata”. Fără el, modelul rezolvă o versiune mai comodă a cererii.",
    "AUDIENȚĂ": "Decide nivelul de detaliu și vocabularul. Fără el, textul iese calibrat pentru nimeni.",
    "LIVRABIL": "Spune ce artefact vrei, nu despre ce subiect. Fără el, primești un eseu în loc de lucrul cerut.",
    "REGULI DE PLATFORMĂ": "Aduce limitele reale ale rețelei. Fără ele, textul e bun și inutilizabil, fiindcă nu încape.",
    "CERINȚE OBLIGATORII": "Lucrurile care nu au voie să lipsească. Sunt primele verificate la final.",
    "METODĂ DE LUCRU": "Ordinea în care se lucrează. Are cel mai mare efect dintre toate secțiunile: schimbă felul în care modelul gândește, nu doar ce scrie.",
    "TON ȘI STIL": "Registrul. Fără el, tonul alunecă spre neutru-corporatist, care e implicitul tuturor modelelor.",
    "CRITERII DE CALITATE": "Lista pe care modelul se autoverifică înainte să răspundă. Prinde greșelile pe care le-ai fi găsit tu la recitire.",
    "FORMAT DE IEȘIRE": "Forma concretă. Fără el, primești conținutul bun în ambalajul greșit și îl rearanjezi manual.",
    "DE EVITAT": "Capcanele domeniului. Numite explicit, sunt evitate; presupuse, apar.",
}

_IMAGE = {
    "SUBJECT": "Ce se vede. Singura secțiune fără de care nu există imagine.",
    "SETTING": "Unde se întâmplă. Fără ea, modelul inventează un fundal, de obicei aglomerat.",
    "COMPOSITION": "Unde stă subiectul în cadru. Diferența dintre o poză și un instantaneu.",
    "CAMERA": "Unghiul, focala și diafragma. Cel mai puternic control după subiect: schimbă perspectiva și cât e neclar.",
    "LIGHTING": "Direcția și calitatea luminii. Dacă schimbi o singură secțiune, schimb-o pe asta — mută cel mai mult rezultatul.",
    "COLOUR AND MOOD": "Paleta și emoția. Fără ele, modelul alege saturația maximă, care arată a randare, nu a fotografie.",
    "STYLE": "Fotografie, ilustrație, randare. Fără el, iese un amestec între toate trei.",
    "DETAIL": "Textura și cât de fin e redat. Controlează dacă suprafețele arată reale sau plasticoase.",
    "TECHNICAL": "Rezoluție și calitate. Efect mic la modelele noi, dar nu strică.",
    "PLATFORM RULES": "Zonele acoperite de interfață și formatul cerut. Fără ele, subiectul ajunge sub butoane.",
    "OUTPUT SPECIFICATION": "Dimensiunea exactă în pixeli. Compoziția se face pentru cadrul ăsta, nu pentru altul decupat după.",
    "QUALITY GUARDS": "Interdicțiile reformulate pozitiv, pentru modelele care nu au prompt negativ și care desenează exact ce le ceri să evite.",
}

_VIDEO = {
    "SUBJECT AND ACTION": "Ce se întâmplă, de la primul până la ultimul cadru. Un clip fără acțiune declarată iese ca o imagine care tremură.",
    "SHOT": "Tipul de cadru și miza lui.",
    "CAMERA MOVEMENT": "Mișcarea, spusă explicit. Nespusă, modelele adaugă un zoom lent pe care nu l-ai cerut.",
    "PACING": "Ritmul și durata. Decide dacă momentul are timp să se întâmple.",
    "LIGHTING AND LOOK": "Lumina care trebuie să rămână identică între cadre. Cea mai frecventă cauză de pâlpâire.",
    "MOTION PHYSICS": "Greutate și inerție. Fără ele, obiectele plutesc.",
    "AUDIO": "Contează doar la modelele care generează sunet, dar acolo contează mult.",
    "OPENING AND ENDING": "Unde intri și unde ieși. Primul cadru e și miniatura.",
}

_SEO = {
    "ROL": "Fixează că textul trebuie să fie bun și pentru cititor, nu doar pentru motor.",
    "CONȚINUTUL SURSĂ": "Materialul tău. Îl leagă pe model de faptele reale și îl împiedică să inventeze.",
    "CUVINTE-CHEIE": "Extrase din conținutul tău, nu ghicite. Spun despre ce e textul, nu ce ai vrea tu să fie.",
    "INTENȚIA DE CĂUTARE": "Ce vrea omul care caută. Schimbă complet structura: cine compară are nevoie de criterii, cine cumpără are nevoie de preț.",
    "LIVRABILE": "Lista exactă de elemente. Fără ea, primești un articol în loc de un set de câmpuri gata de pus în CMS.",
    "LIMITE DE CARACTERE": "Numerele reale ale platformei. Un title de 70 de caractere se taie; unul de 32 într-un câmp de 30 e respins.",
    "REGULI DE OPTIMIZARE": "Unde se pune cuvântul-cheie și cum. Diferența dintre optimizat și îndesat.",
    "DE EVITAT": "Practicile care par SEO și sunt, de fapt, penalizate.",
}

ALL: dict[str, dict[str, str]] = {
    "text": _TEXT,
    "image": _IMAGE,
    "video": _VIDEO,
    "seo": _SEO,
}


def explain(prompt: str, mode: str) -> list[tuple[str, str]]:
    """Găsește secțiunile prezente în prompt și le explică rostul.

    Caută titlurile atât în forma cu etichete, cât și în cea cu titluri simple,
    ca explicația să funcționeze indiferent de modelul-țintă.
    """
    table = ALL.get(mode, _TEXT)
    found: list[tuple[str, str]] = []
    haystack = prompt.upper()
    for title, why in table.items():
        tokens = (title, title.replace(" ", "_").lower().upper())
        if any(token in haystack for token in tokens):
            found.append((title, why))
    return found
