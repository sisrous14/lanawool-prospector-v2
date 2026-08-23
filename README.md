# PromptForge

Transformă o idee scrisă în două rânduri într-un prompt detaliat — de la 300
până la 3000 de cuvinte — pentru modele de text, de imagine sau de video.

Motorul rulează local, fără dependențe și fără internet. Opțional, promptul
poate fi rescris de un model Claude, sau construit pornind de la pozele tale.

```
$ promptforge text "o aplicatie care imi urmareste cheltuielile lunare"
$ promptforge image "portret al unui pescar batran" --target midjourney
$ promptforge video "o reclama la cafea" --platform tiktok --duration 15
$ promptforge vision poza.jpg --instruct "vreau un prompt care sa refaca lumina asta"
$ promptforge remix stil.jpg subiect.jpg --take lumina si paleta
$ promptforge modele          # ce modele există și care sunt gratis
$ promptforge serve           # interfață web locală
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
| `--platform` | tiktok, instagram, facebook, google, youtube, linkedin, x |
| `--preset` | profil salvat, ca să nu repeți opțiunile |

Domeniile de text acoperă și cazuri specifice: `cod` pentru programe,
`descriere-imagini` pentru alt text și legende, `marketing`, `analiza`,
`naratiune`, `business`, `email`, `social`, `educatie`, `ux`, `articol`.

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

## Platforme: TikTok, Instagram, Facebook, Google…

Fiecare rețea are alte reguli, iar programul le știe pe ale ei — inclusiv
limitele de caractere, care sunt cele mai des ignorate:

```bash
promptforge text "anunt pentru o brutarie" --platform google
promptforge image "un produs pe masa" --platform instagram
promptforge video "prezentarea produsului" --platform tiktok --duration 20
```

Un prompt pentru Google Ads primește limita exactă de 30 de caractere pentru
titlu și 90 pentru descriere. Unul pentru TikTok primește regula celor 3 secunde
și zona sigură de sub interfață. Unul pentru Facebook, pragul de 20% text pe
imagine. Platforma stabilește și raportul de aspect, dacă nu îl dai tu.

Regulile intră în prompt în limba promptului: română la `--lang ro`, engleză la
prompturile de imagine și video.

## Dimensiuni

Programul înțelege dimensiunile în pixeli, în trei feluri.

```bash
promptforge image "un afis" --size 2480x3508      # dimensiune exactă
promptforge image "un reel" --size tiktok          # nume de platformă
promptforge image "un banner" --size fullhd        # nume uzual
```

Din dimensiune calculează raportul de aspect (`2480×3508` → `7:10`) și adaugă în
prompt un bloc de specificație: compune pentru cadrul ăsta, cu detaliul care
rezistă la exact atâția pixeli.

Când îi dai o poză prin `vision` sau `remix`, îi citește dimensiunile direct din
antetul fișierului — PNG, JPEG, GIF și WebP, fără nicio bibliotecă externă — și
folosește raportul real al pozei.

## Prompturi pentru video

```bash
promptforge video "un pescar repara o plasa pe chei" --target veo --duration 10
```

Un clip nu e o imagine care se mișcă, așa că blocurile sunt altele: acțiune
continuă, mișcare de cameră, ritm, fizica mișcării, sunet, cadru de început și
de final. Peste ele se adaugă disciplina vizuală comună cu imaginea — lumina
care nu are voie să pâlpâie între cadre, geometria care trebuie să reziste
în timp ce camera se mișcă.

| Țintă | Format |
|---|---|
| `sora`, `veo` | paragraf continuu, fără prompt negativ |
| `kling`, `runway` | blocuri etichetate, cu prompt negativ |

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

## Alegerea modelului

```bash
promptforge modele
promptforge modele --kind image
```

Îți listează toate țintele, cu eticheta de preț în dreptul fiecăreia —
`gratis`, `freemium` sau `platit` — și o notă cu ce înseamnă concret: „Flux
schnell are greutăți deschise și e gratuit local; Flux pro se plătește la
imagine.”

Etichetele sunt o orientare de la momentul scrierii, nu o garanție. Prețurile și
nivelurile gratuite se schimbă des, iar comanda îți spune și ea asta la final.
În interfața web, eticheta apare direct în lista de modele.

## Cât de lung să fie promptul

Implicit 300–500 de cuvinte. Poți cere până la 3000:

```bash
promptforge text "un plan de afaceri" --min-words 1500 --max-words 2000
```

Peste bugetul de bază, programul nu repetă ce a spus deja: adaugă secțiuni
noi cu conținut real — criterii de acceptanță, moduri tipice de eșec, tratarea
cifrelor, prioritizare în caz de conflict; la imagini, planurile de adâncime,
caracterul obiectivului, structura contrastului, logica spațiului.

Două lucruri pe care ți le spune singur: peste circa 1200 de cuvinte te
avertizează că modelele urmăresc tot mai slab instrucțiunile de la mijloc, iar
dacă materialul se termină înainte de minimul cerut, îți spune la ce număr s-a
oprit în loc să umple cu vorbe. În practică ajunge la circa 2900 de cuvinte
pentru text și 2800 pentru imagine.

## Profiluri salvate

Opțiunile pe care le repeți de fiecare dată:

```bash
promptforge preset salveaza produsele-mele \
  --set target=flux --set "style=studio product photography" --set aspect=1:1

promptforge image "o cana de cafea" --preset produsele-mele
promptforge preset lista
promptforge preset sterge produsele-mele
```

Ce dai în linia de comandă bate întotdeauna profilul; `--must` și `--avoid` se
adună în loc să se înlocuiască.

## Învață ce îți place

```bash
promptforge image "un portret"
promptforge bun                    # rezultatul de mai sus a fost reușit
promptforge preferinte             # ce a reținut
```

Fiecare prompt reține descriptorii pe care i-a ales din vocabular. `bun` le
crește scorul, `slab` îl scade, iar generările următoare înclină spre cei
preferați și îi ocolesc pe ceilalți. Nu e învățare automată, e o listă de
preferințe pe care o poți citi și edita: `~/.promptforge/feedback.json`.

## Audit de prompt

```bash
promptforge audit "Deseneaza o pisica frumoasa" --mode image
promptforge audit --file promptul-meu.txt
```

Verifică ce părți standard lipsesc dintr-un prompt existent și dă un scor.
Verificarea e locală, pe cuvinte-cheie: nu poate spune dacă un prompt e *bun*,
dar un scor mic arată aproape sigur o problemă.

## Lexiconul care crește

Când corectezi traducerea unui subiect cu `--subject`, perechea se reține:

```bash
promptforge image "un pescar batran" --subject "an old fisherman"
promptforge lexicon                          # ce a învățat
promptforge lexicon --adauga "manete=levers"
promptforge lexicon --uita "manete"
```

Data viitoare traduce singur. Lexiconul offline se îmbogățește cu fiecare
corecție, fără niciun apel de rețea.

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

Pornește o pagină locală pe `http://127.0.0.1:8765`, cu patru moduri: **Text**,
**Imagine**, **Video** și **Din poze**.

În modul *Din poze* ai o zonă în care poți **trage pozele direct**, le poți alege
cu un clic sau le poți **lipi cu Ctrl+V**. Se adaugă la cele existente în loc să
le înlocuiască, deci poți construi setul pe rând, în aceeași sesiune. Fiecare
apare ca miniatură numerotată („imaginea 1”, „imaginea 2”) și are un buton de
scos. În căsuța de dedesubt scrii ce vrei — inclusiv „ia lumina din imaginea 1 și
pune-o peste subiectul din imaginea 2”.

Lista de modele arată eticheta de preț lângă fiecare nume, iar sub ea apare nota
cu ce înseamnă concret. Mai ai platformă, dimensiune (cu sugestii) și durată
pentru video.

Serverul ascultă doar pe interfața locală și nu are dependențe în afara
bibliotecii standard.

## Alte comenzi

```bash
promptforge ask          # mod interactiv, cu întrebări
promptforge liste        # domeniile, țintele, platformele și tonurile
promptforge modele       # modelele, cu eticheta de preț
promptforge istoric      # ce ai generat până acum
promptforge istoric --full
promptforge preferinte   # ce a învățat din feedback
promptforge lexicon      # traducerile reținute
```

Totul se scrie în `~/.promptforge/`: `history.jsonl` (istoricul),
`presets.json` (profilurile), `feedback.json` (preferințele) și `lexicon.json`
(traducerile învățate). Schimbi locația cu `PROMPTFORGE_HOME`, iar `--no-save`
nu salvează nimic în istoric.

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
- Bugetul de 3000 de cuvinte e atins în practică pe la 2900 la text și 2800 la
  imagine. Când materialul se termină, programul ți-o spune; nu inventează
  umplutură ca să atingă cifra.
- Etichetele de preț ale modelelor sunt de la momentul scrierii. Se schimbă des.
- Auditul verifică structura, nu calitatea. Un scor de 100 nu garantează un
  prompt bun, dar unul mic arată aproape sigur ceva lipsă.

## Teste

```bash
python -m unittest discover tests -v
```
