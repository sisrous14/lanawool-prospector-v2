# PromptForge

Transformă o idee scrisă în două rânduri într-un prompt detaliat — de la 300
până la 3000 de cuvinte — pentru modele de text, de imagine, de video sau
pentru conținut optimizat SEO.

Programul generează prompturi. Nu generează imagini și nu le va genera: pentru
asta ai modelul căruia îi dai promptul.

Motorul rulează local, fără dependențe și fără internet. Opțional, promptul
poate fi rescris de un model Claude, sau construit pornind de la pozele tale.

```
$ promptforge "un clip de 15 secunde pentru TikTok cu produsul nostru"
$ promptforge text "o aplicatie care imi urmareste cheltuielile lunare"
$ promptforge image "portret al unui pescar batran" --target midjourney
$ promptforge video "o reclama la cafea" --platform tiktok --duration 15
$ promptforge vision poza.jpg --instruct "vreau un prompt care sa refaca lumina asta"
$ promptforge remix stil.jpg subiect.jpg --take lumina si paleta
$ promptforge seo --file articol.txt --tip articol
$ promptforge serie --items "o cana" "un ceainic" "o rasnita"
$ promptforge verifica --platform google --file anunt.txt
$ promptforge modele          # ce modele există și care sunt gratis
$ promptforge serve           # interfață web locală
```

## Modul automat

Cel mai scurt mod de a-l folosi: scrie ce vrei, fără să alegi nimic.

```
$ promptforge "un clip de 15 secunde pentru TikTok cu produsul nostru"

PROMPT   (mod: video | domeniu: social | țintă: veo | cuvinte: 315)
  • Alegeri automate: mod video, fiindcă ai scris „clip”; domeniul „social”,
    din cuvintele cheie ale ideii; platformă TikTok, fiindcă ai numit-o.
```

Programul alege modul, domeniul, modelul-țintă, platforma, formatul, lungimea și
numărul de variante — apoi îți spune ce a ales și de ce, ca să poți contrazice.
Orice opțiune pe care o dai explicit rămâne a ta; automatul completează doar
golurile.

Lungimea urmează cererea: „pe scurt” dă un prompt de 300–450 de cuvinte, „complet
și detaliat” dă 900–1300. Imaginile primesc trei variante implicit, fiindcă
acolo direcția vizuală merită comparată.

## Judecata modelului

Fiecare prompt conține, implicit, un rând care îi dă modelului voie să gândească:

> Cererea descrie rezultatul dorit, nu neapărat cel mai bun drum spre el: dacă
> vezi o cale mai bună — altă structură, alt unghi, alt exemplu — ia-o, spune
> într-un rând ce ai schimbat, dar nu rezolva altceva decât s-a cerut.

Granița e scrisă în text și contează: latitudinea e pe **execuție**, nu pe
domeniu. Modelul poate alege cum rezolvă; nu poate rezolva altceva, nu poate
restrânge cererea și nu poate adăuga livrabile. La bugete mai mari, secțiunea
crește cu încă două-trei reguli de acest fel.

Cu `--strict` dispare complet, iar modelul execută litera cererii.

## Lucrări care nu încap într-un prompt

Un prompt are o limită practică de 3000 de cuvinte. Peste ea, programul nu taie:
împarte lucrarea într-un lanț de prompturi, fiecare continuând exact de unde s-a
oprit precedentul.

```bash
promptforge text "un manual complet despre paine cu maia" --max-words 9000
promptforge text "o documentatie de API" --parts 12
```

```
VERIGA 1/4   • Cere planul lucrării, apoi scrie partea 1.
VERIGA 2/4   • Lipește blocul de stare din partea 1 acolo unde promptul îți cere.
VERIGA 3/4   • …
VERIGA 4/4   • Închide lucrarea.
```

**Cum se leagă verigile.** Prima cere modelului planul numerotat al tuturor
părților, apoi partea 1, apoi un bloc de stare:

```
<<<STARE>>>
PARTEA: 1 din 4
PLAN: (planul numerotat al părților)
ACOPERIT: (ce ai scris efectiv)
ULTIMA FRAZĂ: (ultimele 15 cuvinte, textual)
URMEAZĂ: (ce intră în partea 2)
<<<SFÂRȘIT STARE>>>
```

Blocul ăsta îl lipești în veriga următoare, care continuă din punctul indicat de
„ULTIMA FRAZĂ”, fără să reia și fără să rezume. Ultima verigă închide lucrarea
și spune ce a rămas neacoperit, dacă a rămas ceva.

Programul nu vede rezultatele, deci nu poate transporta el conținutul între
prompturi — dar impune protocolul prin care se transportă singur. Fiecare verigă
poartă și cererea inițială, ca să funcționeze și într-o sesiune nouă.

Până la 100 de verigi, adică aproximativ 278.000 de cuvinte de prompt. Dacă îți
trebuie o sută, se generează o sută. Verigile primesc felii diferite din
materialul de îndrumare, ca fiecare să aducă ceva, nu să repete prima.

Lanțul are sens pentru text și SEO, unde rezultatul continuă. Pentru imagini și
clipuri, unde fiecare prompt produce ceva de sine stătător, comanda potrivită e
`serie`.

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

## Conținut SEO

Îi dai conținutul tău — text, fișier, adresă sau poză — și îți construiește
promptul care produce textul optimizat pentru căutare.

```bash
promptforge seo --file articol.txt --tip articol
promptforge seo --url https://exemplu.ro/produs --tip produs --intent tranzactional
promptforge seo --image poza.jpg --tip imagine
promptforge seo "ghid despre paine cu maia" --keyword "paine cu maia"
```

Cuvintele-cheie se **extrag din conținutul tău**, local, fără niciun apel de
rețea: frecvență peste cuvinte și peste perechi de cuvinte, cu deduplicare pe
rădăcini, ca „pâine maia” și „pâinea maia” să nu apară ca două lucruri diferite.
Îți spune ce a găsit; îl schimbi cu `--keyword` dacă vizezi altceva.

Promptul rezultat conține conținutul tău ca sursă a adevărului, cuvintele-cheie,
intenția de căutare, lista exactă de livrabile pentru tipul de pagină, limitele
reale de caractere ale platformei și regulile de optimizare.

| `--tip` | Livrabile |
|---|---|
| `articol` | title, meta, H1, structură H2, intro, corp, FAQ, slug, ancore interne |
| `produs` | title, meta, H1, descriere scurtă și lungă, bullet-uri, specificații, FAQ, alt text |
| `imagine` | alt text, nume de fișier, title, legendă, text înconjurător, schema ImageObject |
| `categorie` | title, meta, H1, intro, ghid de alegere, FAQ, ancore |
| `landing` | title, meta, H1, subtitlu, trei secțiuni, dovezi, CTA, FAQ |
| `local` | title, meta, H1, descriere Google Business, NAP, FAQ local |

`--intent informational｜comercial｜tranzactional｜navigational` schimbă structura:
cine compară are nevoie de criterii, cine cumpără are nevoie de preț.

## Verificarea lungimilor

Textul primit înapoi de la model se verifică aici, înainte să-l pui în CMS:

```
$ promptforge verifica --platform google --file anunt.txt
  ✗ Titlu de anunț       44 caractere — cu 14 caractere peste limita de 30
  ✓ Descriere de anunț   74 caractere — din 90
  ✗ Meta description    170 caractere — cu 10 caractere peste limita de 160
```

Textul se dă cu rânduri de forma `TITLU: …`, `DESCRIERE: …`, `META: …` — sau
`--field titlu "textul"` pentru un singur câmp. Comanda iese cu codul 1 dacă
ceva depășește, deci poate fi pusă într-un script. Câmpurile pe care platforma
nu le are sunt ignorate: nu inventăm limite.

Verificatorul e și în interfața web, sub formularul de generare.

## Serii cu același aspect

Pentru un catalog sau un feed, vrei zece imagini care arată ca o familie:

```bash
promptforge serie --items "o cana de cafea" "un ceainic" "o rasnita" \
  --target flux --style "studio product photography"
```

Primul element stabilește decorul, lumina, paleta, stilul, textura și
obiectivul. Restul le moștenesc identic și schimbă doar subiectul. Merge și pe
`--mode video`.

## Export

```bash
promptforge image "o cana" --variants 3 --export prompturi.csv
promptforge seo --file articol.txt --export brief.md
```

Formatul se ia din extensie: `.csv` (un rând per prompt, pentru foaie de
calcul), `.json` (structura completă), `.md` (document de citit) sau `.txt`
(doar prompturile, separate).

## Explică-mi promptul

```bash
promptforge image "un portret" --explain
```

După prompt, pentru fiecare secțiune, un rând despre ce face și ce se schimbă
fără ea. „LIGHTING — direcția și calitatea luminii. Dacă schimbi o singură
secțiune, schimb-o pe asta.” Scopul e să nu rămâi dependent de program.

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

Implicit 300–500 de cuvinte. Un singur prompt merge până la 3000; peste,
lucrarea se împarte automat într-un lanț (vezi mai sus).

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
pentru text și 2800 pentru imagine — peste atât intervine lanțul.

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

Pornește o pagină locală pe `http://127.0.0.1:8765`, cu șase moduri:
**Automat** (implicit), **Text**, **Imagine**, **Video**, **SEO** și **Din poze**.
Câmpul „Prompturi înlănțuite” cere direct un lanț de N verigi.

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
promptforge auto "..."   # programul alege singur (sau doar: promptforge "...")
promptforge ask          # mod interactiv, cu întrebări
promptforge verifica --platform google --file anunt.txt   # limitele de caractere
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
- Extragerea cuvintelor-cheie măsoară ce e în textul tău, nu ce caută lumea.
  Nu are date de volum de căutare și nu le poate inventa: pentru cercetarea
  propriu-zisă de cuvinte-cheie ai nevoie de un instrument cu date reale.
- Modul automat citește semnale din text, nu înțelege intenția. Când greșește,
  orice opțiune dată explicit îl corectează imediat.
- Lanțul impune protocolul de continuare, dar nu poate verifica dacă modelul l-a
  respectat: blocul de stare îl lipești tu. Dacă o parte iese scurtă, o reiei
  singură, fără să reiei tot lanțul.
- Programul generează prompturi, nu conținut final. Textul SEO îl produce
  modelul căruia îi dai promptul; cu `--refine` face și pasul ăsta, dar tot un
  model îl face, nu programul.

## Teste

```bash
python -m unittest discover tests -v
```
