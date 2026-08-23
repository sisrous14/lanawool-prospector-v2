# Ghid de instalare și testare

De la repository gol la un program care generează prompturi. Toate comenzile de
mai jos au fost rulate, nu presupuse.

Cerințe: **Python 3.10 sau mai nou** și **git**. Atât — programul nu are nicio
dependență obligatorie.

## 1. Instalarea

```bash
git clone --branch claude/caveman-mode-2qs932 \
    https://github.com/sisrous14/lanawool-prospector-v2.git promptforge
cd promptforge

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

`-e` instalează „editabil”: programul rulează direct din directorul clonat, deci
un `git pull` îți aduce versiunea nouă fără reinstalare.

## 2. Merge?

```bash
promptforge --version
# PromptForge 1.4.5

promptforge "un clip de 15 secunde pentru TikTok cu produsul nostru"
```

Trebuie să vezi `mod: video | domeniu: social | țintă: veo`, iar la PARAMETRI
`Duration: 15s | Aspect: 9:16`. Dacă scrie `8s`, ai o versiune mai veche de
1.4.4 — fă `git pull`.

## 3. Testele automate

```bash
python -m unittest discover -s tests -q
# Ran 294 tests ... OK (skipped=16)
```

`OK` e tot ce contează. Cele 16 sărite au nevoie de pachete opționale:
10 de interfață (Playwright + Chromium), 4 de contract cu SDK-ul (`anthropic`),
2 de micșorare a pozelor (`pillow`).

## 4. Instalarea completă

```bash
python -m pip install -e ".[dev]"
python -m playwright install chromium

python -m unittest discover -s tests -q
# Ran 294 tests ... OK          (zero sărite)

python -m pyflakes promptforge/ tests/    # fără ieșire = curat
```

| Comanda | Aduce | Pentru |
|---|---|---|
| `pip install -e .` | nimic | generarea prompturilor, offline |
| `pip install -e ".[model]"` | `anthropic` | `--refine` |
| `pip install -e ".[images]"` | `anthropic`, `pillow` | `vision`, `remix` |
| `pip install -e ".[dev]"` | + `playwright`, `pyflakes` | suita întreagă |

## 5. Testarea cu mâna

Ca să nu-ți amesteci încercările cu datele reale:
`export PROMPTFORGE_HOME=/tmp/pf-test`.

```bash
# cele patru moduri
promptforge text "o aplicatie care imi urmareste cheltuielile lunare"
promptforge image "portret al unui pescar batran" --target midjourney
promptforge video "o reclama la cafea" --platform tiktok --duration 15
promptforge seo "ghid despre paine cu maia" --keyword "paine cu maia"

# lanțul: peste 3000 de cuvinte se împarte în verigi care se continuă
promptforge text "un manual complet despre paine cu maia" --max-words 9000
promptforge seo --file ghid.txt --parts 6

# serie cu aspect comun
promptforge serie --items "o cana" "un ceainic" "o rasnita"

# limitele platformelor (cod de ieșire 1 dacă ceva depășește)
printf 'TITLU: Cafea proaspat prajita, livrata acasa\n' > anunt.txt
promptforge verifica --platform google --file anunt.txt

# modele și etichete de preț
promptforge modele

# profiluri salvate — atenție, sintaxa e --set cheie=valoare
promptforge preset salveaza brutarie --set target=claude --set tone=cald
promptforge text "o brutarie de cartier" --preset brutarie
promptforge preset lista
promptforge preset sterge brutarie

# feedback care se învață
promptforge image "portret al unui pescar batran"
promptforge bun
promptforge preferinte

# auditul unui prompt scris de tine
promptforge audit --file promptul-meu.txt

# traducerea care se corectează și se ține minte
promptforge image "un pescar batran pe un chei de piatra" \
    --subject "an old fisherman on a stone pier"
promptforge lexicon

# export: formatul se ia din extensie
promptforge text "o brutarie" --export brief.md

# mod interactiv, istoric, liste
promptforge ask
promptforge istoric
promptforge liste
```

## 6. Interfața web

```bash
promptforge serve                        # http://127.0.0.1:8765/
promptforge serve --port 9000 --no-browser
```

De testat în pagină: modul automat, comutarea între cele patru moduri, tragerea
mai multor poze una după alta, verificarea lungimilor în modul SEO, schimbarea
temei sistemului.

Rute API: `POST /api/generate`, `POST /api/vision`, `POST /api/check`.

## 7. Cu un model Claude

Trei funcții au nevoie de credențiale: `--refine`, `vision` și `remix`. Restul
programului merge fără ele.

```bash
export ANTHROPIC_API_KEY="sk-ant-…"

promptforge text "o brutarie de cartier" --refine
promptforge vision poza.jpg --instruct "vreau lumina asta"
promptforge remix stil.jpg subiect.jpg --take lumina si paleta
```

Fără cheie nu primești traceback, ci un mesaj clar și codul de ieșire 3. La
`--refine`, promptul local se livrează oricum, cu un avertisment.

## Unde stau datele

Totul în `~/.promptforge/`, în fișiere pe care le poți citi și șterge cu mâna:
`history.jsonl`, `presets.json`, `feedback.json`, `lexicon.json`.
Muți dosarul cu `PROMPTFORGE_HOME`.

## Coduri de ieșire

| Cod | Înseamnă |
|---|---|
| 0 | a mers |
| 1 | numai la `verifica`: un câmp depășește limita platformei |
| 2 | greșeală în ce ai cerut — opțiune invalidă, fișier lipsă, profil inexistent |
| 3 | funcția cerută are nevoie de un model, iar credențialele lipsesc |

## Depanare

| Ce vezi | Ce faci |
|---|---|
| `promptforge: command not found` | mediul virtual nu e activ; sau folosește `python -m promptforge.cli …` |
| `Address already in use` | `promptforge serve --port 9000` |
| `unrecognized arguments: …` | `promptforge <comanda> --help` arată ce acceptă comanda |
| `Nu am găsit câmpuri etichetate` | `verifica` cere text de forma `TITLU: …`, sau `--field` |
| `skipped=16` la teste | normal pe instalarea minimă; dispar cu `.[dev]` + `playwright install chromium` |
| prompt de 8s deși ai cerut 15 | versiune mai veche de 1.4.4; `git pull` |
| diacritice ca `?` în terminal | consola Windows nu e pe UTF-8: `chcp 65001` |

## Ce nu e testat

- **Un apel adevărat cu o cheie adevărată.** Forma cererii și a răspunsului sunt
  testate, dar nicio cerere n-a plecat spre Anthropic.
- **Windows și macOS pe bune.** Ramura fără `fcntl` e testată prin simulare.
  Tot ce s-a rulat a fost Linux, pe Python 3.10 și 3.11.
- **Dacă prompturile produc ce vrei tu.** Structura, lungimea și limitele sunt
  verificate; potrivirea cu ce ai în cap o judeci tu.
