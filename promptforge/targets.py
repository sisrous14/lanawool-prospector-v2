"""Adaptoare pentru modelele-țintă.

Fiecare model are convenții proprii: Claude preferă secțiuni marcate cu
etichete, Midjourney vrea un paragraf continuu urmat de parametri, DALL·E
ignoră prompturile negative și le tratează mai bine reformulate pozitiv.
Aici sunt codificate diferențele.
"""

from __future__ import annotations

# --- ȚINTE PENTRU TEXT -----------------------------------------------------
#
# style: "xml" (etichete, recomandat pentru Claude), "markdown" sau "plain".

TEXT_TARGETS: dict[str, dict] = {
    "claude": {
        "label": "Claude",
        "style": "xml",
        "notes": [
            "Secțiunile sunt marcate cu etichete, forma pe care modelele Claude o urmăresc cel mai fidel.",
            "Poate fi folosit ca mesaj de utilizator sau, fără secțiunea CONTEXT, ca prompt de sistem.",
        ],
    },
    "gpt": {
        "label": "GPT / ChatGPT",
        "style": "markdown",
        "notes": ["Secțiunile sunt titluri Markdown, forma preferată de modelele OpenAI."],
    },
    "gemini": {
        "label": "Gemini",
        "style": "markdown",
        "notes": ["Structură Markdown; păstrează cerințele numerotate pentru urmărire fidelă."],
    },
    "generic": {
        "label": "Generic",
        "style": "plain",
        "notes": ["Titluri simple, fără marcaje — funcționează în orice interfață."],
    },
}


def default_text_target() -> str:
    return "claude"


# --- ȚINTE PENTRU IMAGINE --------------------------------------------------
#
# layout:   "blocks"  – paragrafe etichetate (Flux, Stable Diffusion, generic)
#           "prose"   – un singur paragraf continuu (Midjourney, DALL·E)
# negative: "prompt"  – prompt negativ separat
#           "param"   – transformat în parametrul --no
#           "none"    – modelul nu suportă negative; se reformulează pozitiv
# params:   șablon de parametri, cu {aspect} înlocuit la generare

IMAGE_TARGETS: dict[str, dict] = {
    "flux": {
        "label": "Flux",
        "layout": "blocks",
        "negative": "prompt",
        "params": "--aspect {aspect}",
        "notes": [
            "Flux urmărește bine limbajul natural descriptiv; păstrează frazele complete.",
        ],
    },
    "sdxl": {
        "label": "Stable Diffusion / SDXL",
        "layout": "blocks",
        "negative": "prompt",
        "params": "Steps: 30 | CFG: 6.5 | Sampler: DPM++ 2M Karras | Aspect: {aspect}",
        "notes": [
            "Promptul negativ contează mult la SDXL — folosește-l ca atare, nu îl lipi în promptul principal.",
        ],
    },
    "midjourney": {
        "label": "Midjourney",
        "layout": "prose",
        "negative": "param",
        "params": "--ar {aspect} --style raw --stylize 250 --v 7",
        "notes": [
            "Midjourney citește un paragraf continuu, nu secțiuni; interdicțiile intră în parametrul --no.",
            "Dacă rezultatul iese prea încărcat, scade --stylize spre 100.",
        ],
    },
    "dalle": {
        "label": "DALL·E / GPT Image",
        "layout": "prose",
        "negative": "none",
        "params": "",
        "notes": [
            "DALL·E nu are prompt negativ: interdicțiile au fost reformulate ca cerințe pozitive.",
            "Modelul rescrie intern promptul; formulările explicite și repetate rezistă cel mai bine.",
        ],
    },
    "imagen": {
        "label": "Imagen / Gemini Image",
        "layout": "prose",
        "negative": "none",
        "params": "Aspect ratio: {aspect}",
        "notes": ["Imagen preferă descrierea continuă, cu detaliile fotografice grupate la final."],
    },
    "generic": {
        "label": "Generic",
        "layout": "blocks",
        "negative": "prompt",
        "params": "Aspect ratio: {aspect}",
        "notes": ["Format neutru, ușor de adaptat la orice model."],
    },
}


def default_image_target() -> str:
    return "flux"
