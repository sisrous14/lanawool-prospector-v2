# PromptForge

Transformă o idee scrisă în două rânduri într-un prompt detaliat de 300–500 de
cuvinte, gata de dat unui model de text sau de imagine.

Motorul rulează local, fără dependențe și fără internet. Opțional, promptul
poate fi rescris de un model Claude, care îl adaptează mai fin la ideea ta.

```
$ promptforge text "o aplicatie care imi urmareste cheltuielile lunare"
$ promptforge image "portret al unui pescar batran" --target midjourney
$ promptforge vision poza.jpg --instruct "vreau un prompt care sa refaca lumina asta"
$ promptforge remix stil.jpg subiect.jpg --take lumina si paleta
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

Pentru funcțiile care se uită la poze (`vision`, `remix`) și pentru `--refine`:

```bash
pip install -e ".[images]"
export ANTHROPIC_API_KEY=...        # sau: ant auth login
```

Generarea din text funcționează în continuare fără nimic din toate astea.

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

### Româna, la imagini

Poți scrie ideea în română. Subiectul e tradus automat în engleză, fiindcă
modelele de imagine sunt antrenate pe termeni englezești:

```
$ promptforge image "un pescar batran pe un chei de piatra"
SUBJECT
An old fisherman on a stone pier. This is the single focal point...
```

Traducerea se face cu un lexicon de termeni vizuali, nu cu un model, deci e
aproximativă și îți spune cât a recunoscut. Când prea puține cuvinte îi sunt
cunoscute, refuză să traducă și te anunță, în loc să livreze engleză stricată.
Ai trei ieșiri din situație:

```bash
promptforge image "un pescar pe chei" --subject "a fisherman on a pier"  # dai tu subiectul
promptforge image "un pescar pe chei" --refine                            # traduce modelul
promptforge image "un pescar pe chei" --lang ro                           # prompt în română
```

`--lang ro` scrie tot promptul în română, util dacă vrei să-l citești și să-l
ajustezi. Termenii tehnici — `85mm at f/1.8`, `softbox`, `golden hour` — rămân
în engleză și acolo, fiindcă așa îi folosesc și fotografii români și așa îi
înțeleg modelele.

| Opțiune | Ce face |
|---|---|
| `--target` | `flux`, `sdxl`, `midjourney`, `dalle`, `imagen`, `generic` |
| `--subject` | subiectul formulat în engleză |
| `--style` | impune un stil vizual în locul celui ales automat |
| `--aspect` | raportul de aspect (altfel se alege după domeniu) |

## Poze și linkuri

Îi poți da poze de pe disc, adrese directe de imagine sau pagini web, iar el
îți dă promptul care ar reproduce ce vede.

```bash
promptforge vision poza.jpg
promptforge vision https://exemplu.ro/fotografie.jpg --target midjourney
promptforge vision https://exemplu.ro/articol --mode text
```

Cu `--instruct` spui ce vrei mai exact:

```bash
promptforge vision poza.jpg --instruct "vreau acelasi cadru, dar la apus"
```

O pagină web e citită întreagă: îi luăm titlul, textul și imaginea de
previzualizare. Cu `--mode text` promptul rezultat pornește de la conținutul
paginii; fără el, de la imaginea ei.

### Combinarea a două poze

Asta e cazul „ia ceva din poza asta și pune în cealaltă”:

```bash
promptforge remix lumina.jpg subiect.jpg --take lumina si paleta
promptforge remix stil.png produs.png --take "stilul si textura" --source 1 --into 2
```

Prima poză e sursa, a doua e baza. Le schimbi cu `--source` și `--into`.
Modelul se uită la amândouă și întoarce descrierea rezultatului combinat, iar
promptul final e construit local din ea, cu aceleași garanții de structură și
lungime ca oriunde altundeva.

Un detaliu care contează: promptul **nu** conține fraze de tipul „ia lumina din
imaginea 1”. Modelul de imagine primește doar text și nu vede pozele tale, așa
că elementele preluate sunt topite direct în descriere. Ce ai luat de unde apare
ca observație, pentru tine. La Midjourney primești și un memento că poți atașa
referința vizuală cu `--sref`.

### Ce se trimite și ce nu

Pozele locale ajung la model codificate base64; adresele web sunt trimise ca
adrese, deci le descarcă modelul, nu programul. Peste 5 MB o poză e
redimensionată automat dacă ai Pillow instalat, altfel primești un mesaj clar.
Fără poze și fără linkuri, programul nu face niciun apel de rețea.

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

Pornește o pagină locală pe `http://127.0.0.1:8765`, cu trei moduri: **Text**,
**Imagine** și **Din poze**. În ultimul poți alege mai multe fișiere sau lipi
adrese, le vezi ca miniaturi numerotate („imaginea 1”, „imaginea 2”) și scrii în
căsuța de dedesubt ce vrei — inclusiv „ia lumina din imaginea 1 și pune-o peste
subiectul din imaginea 2”.

Serverul ascultă doar pe interfața locală și nu are dependențe în afara
bibliotecii standard.

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

Pentru poze și linkuri:

```python
from promptforge.pipeline import from_sources

brief, results = from_sources(
    ["lumina.jpg", "subiect.jpg"],
    "ia lumina si paleta din imaginea 1 si pune-le peste subiectul din imaginea 2",
    target="flux",
)
print(results[0].full_text())
```

`from_sources` acceptă și `sender=`, o funcție care înlocuiește apelul la model
— așa sunt testate toate căile vizuale, fără rețea și fără chei.

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
- Traducerea automată română → engleză merge pe un lexicon de termeni vizuali
  frecvenți. Prinde bine descrierile obișnuite, dar nu e un traducător general:
  la construcții neobișnuite îți spune că n-a reușit, în loc să ghicească.
- `vision` și `remix` au nevoie de un model, deci de pachetul `anthropic` și de
  credențiale. Fără ele, comenzile ies cu un mesaj care spune exact ce lipsește;
  restul programului merge mai departe.

## Teste

```bash
python -m unittest discover tests -v
```
