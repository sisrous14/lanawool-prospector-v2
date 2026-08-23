"""Secțiunea prin care modelul primește voie să gândească singur.

Un prompt bun spune ce vrei. Un prompt foarte bun spune ce vrei și lasă loc
modelului să găsească o cale mai bună spre același rezultat, cu condiția să
declare abaterea.

Granița e importantă și e scrisă explicit în text: latitudinea e pe execuție,
nu pe domeniu. Modelul are voie să aleagă altă structură, alt exemplu, altă
ordine — nu are voie să rezolve altceva decât s-a cerut. Cine vrea execuție
literală pornește cu `--strict`.
"""

from __future__ import annotations

from .models import Section

TITLES = {
    "ro": "JUDECATĂ PROPRIE",
    "en": "YOUR OWN JUDGMENT",
}

TAG = "judecata"

# Primul rând spune totul și rămâne mereu; restul apar când bugetul permite.
_LINES = {
    "ro": [
        "Cererea descrie rezultatul dorit, nu neapărat cel mai bun drum spre el: dacă vezi o cale "
        "mai bună — altă structură, alt unghi, alt exemplu — ia-o, spune într-un rând ce ai "
        "schimbat, dar nu rezolva altceva decât s-a cerut.",
    ],
    "en": [
        "The request describes the result wanted, not necessarily the best route to it: if you see "
        "a better route — a different structure, angle or example — take it and say in one line "
        "what you changed, but do not solve anything other than what was asked.",
    ],
}

_EXPANSIONS = {
    "ro": [
        "Latitudinea e pe execuție, nu pe domeniu. Ai voie să alegi cum rezolvi; nu ai voie să "
        "rezolvi altceva, să restrângi cererea sau să adaugi livrabile care nu s-au cerut.",
        "Nu te opri la varianta suficient de bună. Întreabă-te, înainte de a livra, ce ar face "
        "rezultatul vizibil mai bun și, dacă răspunsul intră în cererea dată, fă-o.",
        "Dacă două abordări sunt aproape la fel de bune, alege-o pe cea mai ușor de verificat "
        "de către cel care primește rezultatul.",
        "Dacă cererea conține o presupunere care ți se pare greșită, respect-o în rezultat și "
        "semnaleaz-o separat, în două propoziții, la final.",
    ],
    "en": [
        "The latitude is over execution, not over scope. You may choose how to solve it; you may "
        "not solve something else, narrow the request, or add deliverables nobody asked for.",
        "Do not stop at good enough. Before delivering, ask what would make the result visibly "
        "better and, if the answer fits the request as given, do it.",
        "If two approaches are nearly as good, pick the one that is easier for the recipient to verify.",
        "If the request contains an assumption you believe is wrong, honour it in the result and "
        "flag it separately, in two sentences, at the end.",
    ],
}

# Pentru imagine și video, latitudinea se formulează vizual și rămâne în engleză,
# ca restul descriptorilor.
_VISUAL = (
    "Where this description leaves a choice open, make the choice that produces the strongest "
    "image rather than the most literal one — but never at the cost of the subject, which is "
    "rendered exactly as described."
)

_VISUAL_RO = (
    "Acolo unde descrierea lasă o alegere deschisă, ia decizia care dă imaginea cea mai bună, "
    "nu pe cea mai literală — dar niciodată în dauna subiectului, care se redă exact cum e descris."
)


def text_section(lang: str) -> Section:
    """Secțiunea de latitudine pentru prompturile de text și SEO."""
    return Section(
        TITLES[lang],
        list(_LINES[lang]),
        # Un rând rămâne întotdeauna: latitudinea e o instrucțiune, nu un ornament.
        # Restul crește odată cu bugetul. Prioritatea 2 o pune în aceeași categorie
        # cu criteriile de calitate — se scurtează, dar nu dispare.
        priority=2,
        bullet="-",
        droppable=True,
        min_lines=1,
        expansions=list(_EXPANSIONS[lang]),
    )


def visual_line(lang: str) -> str:
    """Rândul de latitudine pentru prompturile vizuale."""
    return _VISUAL_RO if lang == "ro" else _VISUAL
