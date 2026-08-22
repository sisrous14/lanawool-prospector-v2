# PromptForge

Transformă o idee scrisă în două rânduri într-un prompt detaliat de 300–500 de
cuvinte, gata de dat unui model de text sau de imagine.

Motorul rulează local, fără dependențe și fără internet. Opțional, promptul
poate fi rescris de un model Claude, care îl adaptează mai fin la ideea ta.

```
$ promptforge text "o aplicatie care imi urmareste cheltuielile lunare"
$ promptforge image "portret al unui pescar batran" --target midjourney
$ promptforge serve          # interfață web locală
```

## Instalare

Ai nevoie doar de Python 3.10 sau mai nou.

```bash
git clone https://github.com/sisrous14/lanawool-prospector-v2.git
cd lanawool-prospector-v2
pip install -e .
```

Fără instalare merge la fel de bine: `python -m promptforge ...`.

Pentru rafinarea cu model (opțional):

```bash
pip install -e ".[refine]"
export ANTHROPIC_API_KEY=...        # sau: ant auth login
```

## Cum funcționează

Programul nu completează un șablon fix. Pentru fiecare idee:

1. **detectează domeniul** din cuvintele-cheie — cod, marketing, analiză,
   narațiune, portret, produs, peisaj, concept art și încă vreo douăzeci;
2. **alege descriptorii** potriviți acelui domeniu dintr-o bază de cunoștințe
   scrisă manual (metode de lucru, criterii de calitate, capcane tipice; pentru
   imagini: obiectiv, diafragmă, schemă de lumini, paletă, compoziție);
3. **asamblează secțiunile** și ajustează lungimea până cade în intervalul cerut,
   fără să taie vreo propoziție la jumătate;
4. **adaptează forma** la modelul-țintă: etichete pentru Claude, Markdown pentru
   GPT, paragraf continuu plus parametri pentru Midjourney, reformulare pozitivă
   a interdicțiilor pentru DALL·E, care nu are prompt negativ.

Ce ai cerut tu explicit — prin `--must` și `--avoid` — nu se pierde niciodată la
scurtare: cerințele tale sunt puse înaintea celor implicite.

## Prompturi pentru text

```bash
promptforge text "un plan de afaceri pentru o brutarie de cartier" \
  --target claude \
  --audience "un investitor care nu cunoaste domeniul" \
  --tone profesional \
  --must "include un prag de rentabilitate calculat" \
  --avoid "proiectii optimiste fara mecanism"
```

Promptul rezultat conține rol, context, audiență, livrabil, cerințe numerotate,
metodă de lucru pas cu pas, criterii de auto-verificare, format de ieșire și
lista lucrurilor de evitat.

| Opțiune | Ce face |
|---|---|
| `--target` | `claude` (etichete), `gpt`, `gemini`, `generic` |
| `--domain` | forțează domeniul, dacă detecția automată greșește |
| `--audience` | pentru cine e textul |
| `--tone` | un ton din listă sau o descriere liberă |
| `--lang` | `ro` (implicit) sau `en` — limba promptului generat |

## Prompturi pentru imagine

```bash
promptforge image "a portrait of an old fisherman" \
  --target flux --aspect 3:2 --variants 3
```

Ieșirea are trei părți: promptul propriu-zis, promptul negativ și parametrii
modelului. Blocurile acoperă subiect, decor, compoziție, cameră și obiectiv,
lumină, paletă și atmosferă, stil, textură și cerințe tehnice.

**Scrie subiectul în engleză.** Modelele de imagine sunt antrenate pe termeni
englezești, iar un subiect în română degradează vizibil rezultatul. Dacă
gândești în română, ai două variante:

```bash
promptforge image "un pescar batran pe chei" --subject "an old fisherman on a pier"
promptforge image "un pescar batran pe chei" --refine   # traduce modelul
```

Restul vocabularului vizual e oricum generat în engleză.

| Opțiune | Ce face |
|---|---|
| `--target` | `flux`, `sdxl`, `midjourney`, `dalle`, `imagen`, `generic` |
| `--subject` | subiectul formulat în engleză |
| `--style` | impune un stil vizual în locul celui ales automat |
| `--aspect` | raportul de aspect (altfel se alege după domeniu) |

## Variante și reproductibilitate

`--variants 3` dă trei direcții creative diferite pentru aceeași idee — altă
lumină, alt unghi, altă paletă. `--seed N` face rezultatul reproductibil: același
seed dă mereu același prompt.

```bash
promptforge image "a floating city" --variants 4 --seed 42
```

## Rafinare cu un model Claude

```bash
promptforge text "o aplicatie de bugetare" --refine
```

Promptul generat local e trimis unui model Claude, care îl rescrie: înlocuiește
formulările generice cu unele specifice ideii tale și traduce subiectele vizuale.
Fără pachetul `anthropic` sau fără credențiale, programul spune de ce nu a mers și
livrează promptul local — nu eșuează.

Modelul implicit este `claude-opus-5`; îl schimbi cu `--model`, iar adâncimea
raționamentului cu `--effort low|medium|high|xhigh|max`.

## Interfață web

```bash
promptforge serve
```

Pornește o pagină locală pe `http://127.0.0.1:8765` cu formular, comutator
text/imagine, variante și buton de copiere. Serverul ascultă doar pe interfața
locală și nu are dependențe în afara bibliotecii standard.

## Alte comenzi

```bash
promptforge ask          # mod interactiv, cu întrebări
promptforge liste        # domeniile, țintele și tonurile disponibile
promptforge istoric      # ce ai generat până acum
promptforge istoric --full
```

Istoricul se scrie în `~/.promptforge/history.jsonl`; schimbi locația cu
variabila de mediu `PROMPTFORGE_HOME`, iar `--no-save` nu salvează nimic.

## Ca bibliotecă

```python
from promptforge import Brief, generate, generate_many

brief = Brief(
    idea="un portret al unui pescar batran",
    mode="image",
    target="flux",
    aspect="3:2",
)

print(generate(brief).full_text())

for varianta in generate_many(brief, 3):
    print(varianta.word_count, varianta.domain)
```

`generate` întoarce un `GeneratedPrompt` cu `prompt`, `negative_prompt`,
`parameters`, `word_count`, `notes` și metoda `full_text()`, care le lipește pe
toate într-un text gata de copiat.

## Limite cunoscute

- Sub aproximativ 250 de cuvinte structura obligatorie nu mai încape. Programul
  nu o ciopârțește; îți spune în secțiunea de observații că a depășit limita.
- Detecția domeniului merge pe cuvinte-cheie, nu pe înțeles. Când greșește,
  `--domain` rezolvă imediat.
- Rafinarea cu model costă un apel API și câteva secunde. Motorul local nu costă
  nimic.

## Teste

```bash
python -m unittest discover tests -v
```
