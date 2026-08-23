"""Baza de cunoștințe: domenii, descriptori și vocabular specializat.

Fișierul este pur date. Motoarele din `text_engine` și `image_engine` aleg
determinist (pe baza unui seed) din listele de aici, astfel încât aceeași
idee + același seed produc mereu același prompt, iar `--variants` produce
direcții creative diferite.
"""

from __future__ import annotations

import unicodedata

# ---------------------------------------------------------------------------
# Utilitare de normalizare (potrivirea cuvintelor-cheie ignoră diacriticele)
# ---------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Lowercase fără diacritice, pentru potrivirea cuvintelor-cheie RO/EN."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# ---------------------------------------------------------------------------
# DOMENII TEXT
# ---------------------------------------------------------------------------
#
# Fiecare domeniu oferă:
#   keywords   – termeni RO/EN care declanșează detecția automată
#   role       – expertiza pe care o primește modelul
#   deliverable– artefactul concret cerut
#   steps      – metoda de lucru impusă modelului
#   quality    – criteriile pe care modelul le auto-verifică
#   pitfalls   – capcanele tipice ale domeniului
#   format     – structura de ieșire recomandată

TEXT_DOMAINS: dict[str, dict[str, object]] = {
    "cod": {
        "keywords": [
            "cod", "aplicatie", "app", "script", "functie", "api", "backend",
            "frontend", "bug", "refactor", "test", "python", "javascript",
            "typescript", "sql", "docker", "microserviciu", "algoritm",
            "librarie", "framework", "endpoint", "baza de date", "database",
            "software", "program", "clasa", "modul", "compilator", "deploy",
        ],
        "role": {
            "ro": "inginer software senior cu 15 ani de experiență în sisteme de producție",
            "en": "senior software engineer with 15 years of experience shipping production systems",
        },
        "deliverable": {
            "ro": "cod funcțional, gata de rulat, însoțit de explicațiile deciziilor de arhitectură",
            "en": "working, runnable code together with the reasoning behind each architectural decision",
        },
        "steps": {
            "ro": [
                "Reformulează cerința în propriile cuvinte și enumeră ipotezele pe care le faci acolo unde specificația este incompletă.",
                "Alege structura de date și arhitectura potrivite și justifică alegerea în două-trei propoziții, comparând-o cu o alternativă respinsă.",
                "Scrie codul complet, fără fragmente de tip `# restul rămâne la fel` și fără funcții lăsate nescrise.",
                "Tratează explicit erorile, valorile lipsă și intrările invalide; nu presupune că datele de intrare sunt corecte.",
                "Adaugă teste care acoperă cazul obișnuit, cazul limită și cazul de eroare.",
                "Încheie cu instrucțiuni exacte de instalare și rulare, plus limitările cunoscute ale soluției.",
            ],
            "en": [
                "Restate the requirement in your own words and list every assumption you make where the spec is incomplete.",
                "Choose the data structures and architecture, justifying the choice in two or three sentences against one rejected alternative.",
                "Write the complete code — no `# rest stays the same` fragments and no unimplemented functions.",
                "Handle errors, missing values and invalid input explicitly; never assume the input is well-formed.",
                "Add tests covering the happy path, an edge case and a failure case.",
                "Finish with exact install and run instructions plus the known limitations of the solution.",
            ],
        },
        "quality": {
            "ro": [
                "codul rulează fără modificări, exact așa cum este scris",
                "denumirile sunt descriptive, iar comentariile explică *de ce*, nu *ce*",
                "nu există chei, parole sau căi absolute hardcodate",
                "complexitatea algoritmică este menționată acolo unde contează",
            ],
            "en": [
                "the code runs unmodified, exactly as written",
                "names are descriptive and comments explain *why*, not *what*",
                "no hardcoded keys, passwords or absolute paths",
                "algorithmic complexity is stated where it matters",
            ],
        },
        "pitfalls": {
            "ro": [
                "pseudocod prezentat drept cod funcțional",
                "biblioteci inventate sau metode care nu există în versiunea indicată",
                "tratarea erorilor redusă la un `try/except` care înghite excepția",
            ],
            "en": [
                "pseudocode presented as working code",
                "invented libraries or methods that do not exist in the stated version",
                "error handling reduced to a `try/except` that swallows the exception",
            ],
        },
        "format": {
            "ro": "Blocuri de cod marcate cu limbajul, precedate de un rezumat de maximum 5 rânduri și urmate de secțiunile «Cum rulezi» și «Limitări».",
            "en": "Language-tagged code blocks, preceded by a summary of at most 5 lines and followed by a `How to run` and a `Limitations` section.",
        },
    },
    "marketing": {
        "keywords": [
            "marketing", "reclama", "ad", "campanie", "vanzare", "landing",
            "copywriting", "copy", "brand", "slogan", "newsletter", "conversie",
            "clienti", "oferta", "promovare", "pitch", "produs", "lansare",
            "audienta", "funnel", "cta", "seo",
        ],
        "role": {
            "ro": "copywriter de performanță care a scris campanii cu buget de peste un milion de euro",
            "en": "performance copywriter who has written campaigns backed by seven-figure budgets",
        },
        "deliverable": {
            "ro": "text de vânzare gata de publicat, cu variante alternative pentru testare A/B",
            "en": "publish-ready sales copy with alternative variants for A/B testing",
        },
        "steps": {
            "ro": [
                "Identifică durerea reală a audienței, nu cea declarată; formuleaz-o într-o singură propoziție.",
                "Definește promisiunea centrală și dovada care o susține (cifră, mărturie, mecanism).",
                "Scrie mai întâi cârligul; dacă primele opt cuvinte nu opresc scroll-ul, reia.",
                "Construiește textul pe structura problemă → agitare → soluție → dovadă → acțiune.",
                "Livrează trei variante de titlu și două de call-to-action, cu ipoteza pe care o testează fiecare.",
            ],
            "en": [
                "Identify the audience's real pain, not the stated one; phrase it in a single sentence.",
                "Define the central promise and the proof backing it (a number, a testimonial, a mechanism).",
                "Write the hook first; if the first eight words do not stop the scroll, start over.",
                "Build the copy on problem → agitation → solution → proof → action.",
                "Deliver three headline variants and two call-to-action variants, each with the hypothesis it tests.",
            ],
        },
        "quality": {
            "ro": [
                "fiecare afirmație are un beneficiu concret în spate, nu un adjectiv",
                "textul se citește cu voce tare fără poticniri",
                "nu conține clișee de tipul «soluții inovatoare» sau «lider de piață»",
                "call-to-action-ul spune exact ce se întâmplă după clic",
            ],
            "en": [
                "every claim is backed by a concrete benefit, not an adjective",
                "the copy reads aloud without stumbling",
                "it contains no clichés such as `innovative solutions` or `market leader`",
                "the call to action states exactly what happens after the click",
            ],
        },
        "pitfalls": {
            "ro": [
                "limbaj corporatist care nu spune nimic verificabil",
                "beneficii formulate din perspectiva companiei, nu a clientului",
                "promisiuni pe care produsul nu le poate susține",
            ],
            "en": [
                "corporate language that says nothing verifiable",
                "benefits framed from the company's perspective rather than the customer's",
                "promises the product cannot support",
            ],
        },
        "format": {
            "ro": "Titlu, subtitlu, corp structurat pe secțiuni scurte, bullet-uri de beneficii, CTA, plus lista variantelor de testat.",
            "en": "Headline, subhead, body in short sections, benefit bullets, CTA, plus the list of variants to test.",
        },
    },
    "articol": {
        "keywords": [
            "articol", "blog", "postare", "text", "eseu", "ghid", "tutorial",
            "documentatie", "carte", "capitol", "continut", "redactare",
            "newsletter", "editorial", "recenzie", "sinteza",
        ],
        "role": {
            "ro": "redactor cu experiență în publicații de specialitate, obișnuit să transforme subiecte tehnice în text limpede",
            "en": "editor experienced in specialist publications, used to turning technical subjects into clear prose",
        },
        "deliverable": {
            "ro": "articol complet, structurat, gata de publicare, fără text de umplutură",
            "en": "a complete, structured, publish-ready article with no filler",
        },
        "steps": {
            "ro": [
                "Stabilește teza articolului într-o singură propoziție; tot ce nu o susține se elimină.",
                "Construiește scheletul: introducere cu miză, trei-cinci secțiuni cu titluri informative, concluzie cu concluzie reală.",
                "Deschide cu o observație concretă, nu cu o definiție de dicționar.",
                "Susține fiecare afirmație importantă cu un exemplu, o cifră sau un caz real.",
                "Variază ritmul frazelor și elimină la final orice propoziție care nu adaugă informație.",
            ],
            "en": [
                "State the article's thesis in a single sentence; cut anything that does not support it.",
                "Build the skeleton: an introduction with stakes, three to five sections with informative headings, a conclusion that concludes something.",
                "Open with a concrete observation, not a dictionary definition.",
                "Back every significant claim with an example, a number or a real case.",
                "Vary sentence rhythm and, at the end, delete any sentence that adds no information.",
            ],
        },
        "quality": {
            "ro": [
                "un cititor grăbit înțelege ideea principală doar din titluri",
                "nicio secțiune nu repetă ce s-a spus deja",
                "tonul este constant de la prima la ultima frază",
                "exemplele sunt specifice, nu generice",
            ],
            "en": [
                "a hurried reader gets the main idea from the headings alone",
                "no section repeats what was already said",
                "the tone stays constant from the first to the last sentence",
                "examples are specific rather than generic",
            ],
        },
        "pitfalls": {
            "ro": [
                "introduceri care anunță ce urmează în loc să înceapă",
                "paragrafe de tranziție goale de conținut",
                "concluzii care doar rezumă textul de mai sus",
            ],
            "en": [
                "introductions that announce what is coming instead of starting",
                "transition paragraphs empty of content",
                "conclusions that merely summarise the text above",
            ],
        },
        "format": {
            "ro": "Titlu, introducere, secțiuni cu subtitluri, concluzie. Fără liste acolo unde proza spune mai mult.",
            "en": "Title, introduction, subheaded sections, conclusion. No lists where prose says more.",
        },
    },
    "analiza": {
        "keywords": [
            "analiza", "cercetare", "research", "studiu", "comparatie",
            "evaluare", "raport", "date", "statistica", "piata", "concurenta",
            "diagnostic", "audit", "investigatie", "tendinte", "metrici",
        ],
        "role": {
            "ro": "analist care lucrează pentru decidenți și este evaluat după cât de utile sunt concluziile, nu după cât de lung este raportul",
            "en": "analyst working for decision-makers, judged by how useful the conclusions are rather than how long the report is",
        },
        "deliverable": {
            "ro": "analiză structurată care se termină cu o recomandare asumată și cu ce ar schimba-o",
            "en": "a structured analysis ending in a committed recommendation and what would change it",
        },
        "steps": {
            "ro": [
                "Formulează întrebarea la care răspunzi; dacă are mai multe sensuri, alege unul și spune de ce.",
                "Separă net faptele verificabile de interpretări și de ipoteze.",
                "Prezintă contraargumentul cel mai puternic împotriva concluziei tale înainte de a o susține.",
                "Cuantifică unde se poate; unde nu se poate, spune explicit că estimezi și pe ce bază.",
                "Termină cu o recomandare, nivelul tău de încredere în ea și indicatorul care ar infirma-o.",
            ],
            "en": [
                "State the question you are answering; if it is ambiguous, pick one reading and say why.",
                "Keep verifiable facts strictly separate from interpretation and assumption.",
                "Present the strongest counter-argument to your conclusion before defending it.",
                "Quantify where possible; where not, say explicitly that you are estimating and on what basis.",
                "End with a recommendation, your confidence in it, and the indicator that would falsify it.",
            ],
        },
        "quality": {
            "ro": [
                "fiecare cifră are o sursă sau este marcată drept estimare",
                "concluzia decurge din date, nu le precede",
                "incertitudinea este exprimată în cuvinte, nu ascunsă",
                "recomandarea poate fi pusă în practică luni dimineață",
            ],
            "en": [
                "every number has a source or is flagged as an estimate",
                "the conclusion follows from the data instead of preceding it",
                "uncertainty is stated in words rather than hidden",
                "the recommendation can be acted on Monday morning",
            ],
        },
        "pitfalls": {
            "ro": [
                "cifre inventate pentru a părea riguros",
                "concluzii echilibrate artificial, care nu recomandă nimic",
                "confuzia dintre corelație și cauzalitate",
            ],
            "en": [
                "invented numbers used to sound rigorous",
                "artificially balanced conclusions that recommend nothing",
                "confusing correlation with causation",
            ],
        },
        "format": {
            "ro": "Rezumat executiv de 5 rânduri, apoi secțiuni pe întrebări, tabel comparativ dacă ajută, recomandare finală.",
            "en": "A five-line executive summary, then sections per question, a comparison table if useful, and the final recommendation.",
        },
    },
    "email": {
        "keywords": [
            "email", "mail", "mesaj", "scrisoare", "raspuns", "corespondenta",
            "invitatie", "notificare", "follow-up", "reclamatie", "cerere",
        ],
        "role": {
            "ro": "profesionist care scrie zeci de mesaje pe zi și știe că un email bun se citește în douăzeci de secunde",
            "en": "professional who writes dozens of messages a day and knows a good email is read in twenty seconds",
        },
        "deliverable": {
            "ro": "email gata de trimis, cu subiect, corp și, dacă e cazul, variantă mai scurtă",
            "en": "a send-ready email with subject line, body and, where useful, a shorter variant",
        },
        "steps": {
            "ro": [
                "Scrie subiectul astfel încât destinatarul să știe din el ce se cere de la el.",
                "Pune cererea sau concluzia în primele două rânduri; contextul vine după.",
                "Un email, o singură cerere clară, cu termen și responsabil.",
                "Adaptează formula de adresare la relația dintre expeditor și destinatar.",
            ],
            "en": [
                "Write the subject so the recipient learns from it what is being asked of them.",
                "Put the request or conclusion in the first two lines; context comes after.",
                "One email, one clear request, with a deadline and an owner.",
                "Match the salutation to the relationship between sender and recipient.",
            ],
        },
        "quality": {
            "ro": [
                "sub 150 de cuvinte dacă subiectul nu cere mai mult",
                "nicio frază care există doar din politețe automată",
                "tonul este ferm fără să fie agresiv",
            ],
            "en": [
                "under 150 words unless the subject demands more",
                "no sentence that exists purely out of reflex politeness",
                "the tone is firm without being aggressive",
            ],
        },
        "pitfalls": {
            "ro": [
                "introduceri de tipul «sper că te găsesc bine» care amână mesajul",
                "cereri implicite pe care destinatarul trebuie să le ghicească",
            ],
            "en": [
                "openers such as `hope this finds you well` that delay the message",
                "implicit requests the recipient has to guess",
            ],
        },
        "format": {
            "ro": "Subiect pe un rând, corp în paragrafe scurte, semnătură. Fără antet decorativ.",
            "en": "Subject on one line, body in short paragraphs, signature. No decorative header.",
        },
    },
    "naratiune": {
        "keywords": [
            "poveste", "nuvela", "roman", "scenariu", "film", "personaj",
            "dialog", "fictiune", "naratiune", "story", "script", "joc",
            "monolog", "piesa", "basm", "poem", "poezie",
        ],
        "role": {
            "ro": "scriitor care a publicat proză scurtă și știe că tensiunea se construiește din detaliu concret, nu din adjective",
            "en": "writer of published short fiction who knows tension is built from concrete detail, not adjectives",
        },
        "deliverable": {
            "ro": "text narativ coerent, cu un conflict care se schimbă de la început până la final",
            "en": "a coherent narrative in which the conflict changes between the opening and the ending",
        },
        "steps": {
            "ro": [
                "Stabilește ce vrea personajul principal și ce îl împiedică; fără asta nu există poveste.",
                "Intră în scenă cât mai târziu posibil și ieși cât mai devreme.",
                "Arată prin acțiune și detaliu senzorial; explică doar ce nu poate fi arătat.",
                "Dă fiecărui personaj un mod propriu de a vorbi, recognoscibil fără atribuiri.",
                "Asigură-te că finalul răspunde întrebării ridicate de prima pagină, chiar dacă răspunsul e neașteptat.",
            ],
            "en": [
                "Establish what the protagonist wants and what stands in the way; without it there is no story.",
                "Enter each scene as late as possible and leave as early as possible.",
                "Show through action and sensory detail; explain only what cannot be shown.",
                "Give each character a distinct way of speaking, recognisable without dialogue tags.",
                "Make sure the ending answers the question the first page raised, even if the answer is unexpected.",
            ],
        },
        "quality": {
            "ro": [
                "detaliile sunt specifice și verificabile în lumea poveștii",
                "dialogul avansează acțiunea sau dezvăluie caracter",
                "nu există explicații ale emoțiilor pe care scena le arată deja",
            ],
            "en": [
                "details are specific and consistent within the story's world",
                "dialogue advances the action or reveals character",
                "emotions the scene already shows are not also explained",
            ],
        },
        "pitfalls": {
            "ro": [
                "personaje care rostesc informații pe care le știu amândoi, pentru cititor",
                "adjective emoționale în locul detaliilor concrete",
                "finaluri care rezolvă conflictul printr-o coincidență",
            ],
            "en": [
                "characters stating information both already know, for the reader's benefit",
                "emotional adjectives standing in for concrete detail",
                "endings that resolve the conflict through coincidence",
            ],
        },
        "format": {
            "ro": "Proză continuă, cu pauze de scenă marcate. Fără rezumat înainte sau după text.",
            "en": "Continuous prose with marked scene breaks. No summary before or after the text.",
        },
    },
    "business": {
        "keywords": [
            "afacere", "business", "plan", "strategie", "startup", "investitie",
            "buget", "model de business", "monetizare", "crestere", "operational",
            "proces", "management", "echipa", "kpi", "prezentare",
        ],
        "role": {
            "ro": "consultant care a lucrat atât cu firme la început de drum, cât și cu companii mature, și care preferă cifrele grosiere adevărate previziunilor elegante",
            "en": "consultant who has worked with both early-stage and mature companies and prefers rough true numbers to elegant forecasts",
        },
        "deliverable": {
            "ro": "document de decizie care poate fi prezentat unui investitor sau unui board",
            "en": "a decision document that can be put in front of an investor or a board",
        },
        "steps": {
            "ro": [
                "Descrie problema pieței și dovada că există, nu doar convingerea că există.",
                "Explică soluția și de ce câștigă în fața alternativei actuale a clientului, inclusiv «nu face nimic».",
                "Prezintă modelul de venit cu numere: preț, cost de achiziție, marjă, prag de rentabilitate.",
                "Enumeră cele trei riscuri care pot omorî planul și ce le-ar reduce.",
                "Termină cu următorii pași pe 30, 90 și 365 de zile.",
            ],
            "en": [
                "Describe the market problem and the evidence it exists, not just the belief that it does.",
                "Explain the solution and why it beats the customer's current alternative, including `do nothing`.",
                "Present the revenue model with numbers: price, acquisition cost, margin, break-even point.",
                "List the three risks that can kill the plan and what would reduce them.",
                "End with next steps at 30, 90 and 365 days.",
            ],
        },
        "quality": {
            "ro": [
                "fiecare presupunere financiară este vizibilă și poate fi contestată",
                "planul rămâne valid dacă cea mai optimistă cifră se înjumătățește",
                "nu conține jargon care ascunde lipsa unui mecanism",
            ],
            "en": [
                "every financial assumption is visible and can be challenged",
                "the plan survives halving the most optimistic number",
                "it contains no jargon hiding the absence of a mechanism",
            ],
        },
        "pitfalls": {
            "ro": [
                "proiecții în formă de crosă de hochei fără mecanism care le explice",
                "piață totală adresabilă folosită ca dovadă de cerere",
            ],
            "en": [
                "hockey-stick projections with no mechanism behind them",
                "total addressable market used as proof of demand",
            ],
        },
        "format": {
            "ro": "Secțiuni numerotate, tabel de cifre-cheie, listă de riscuri, plan pe termene.",
            "en": "Numbered sections, a key-numbers table, a risk list and a phased plan.",
        },
    },
    "educatie": {
        "keywords": [
            "explica", "invat", "lectie", "curs", "predare", "student",
            "elev", "scoala", "examen", "exercitiu", "material didactic",
            "training", "onboarding", "manual", "profesor",
        ],
        "role": {
            "ro": "profesor care a predat aceeași materie destul de mult timp încât să știe exact unde se blochează oamenii",
            "en": "teacher who has taught the same subject long enough to know exactly where people get stuck",
        },
        "deliverable": {
            "ro": "material de învățare care duce cititorul de la zero la aplicare independentă",
            "en": "a learning resource that takes the reader from zero to independent application",
        },
        "steps": {
            "ro": [
                "Pornește de la ce știe deja cititorul și construiește o singură idee nouă pe rând.",
                "Introdu fiecare noțiune printr-un exemplu concret înainte de definiția formală.",
                "Anticipează neînțelegerea tipică și adres-o explicit înainte să apară.",
                "Închide cu exerciții gradate și cu răspunsuri comentate, nu doar cu rezultatul.",
            ],
            "en": [
                "Start from what the reader already knows and add one new idea at a time.",
                "Introduce each concept through a concrete example before the formal definition.",
                "Anticipate the typical misconception and address it explicitly before it appears.",
                "Close with graded exercises and worked answers, not just the result.",
            ],
        },
        "quality": {
            "ro": [
                "orice termen tehnic este definit la prima apariție",
                "exemplele sunt din contextul real al cititorului",
                "cititorul poate rezolva singur ultimul exercițiu",
            ],
            "en": [
                "every technical term is defined at first use",
                "examples come from the reader's real context",
                "the reader can solve the final exercise unaided",
            ],
        },
        "pitfalls": {
            "ro": [
                "definiții circulare care folosesc termenul explicat",
                "salturi de dificultate nemarcate",
            ],
            "en": [
                "circular definitions that use the term being explained",
                "unmarked jumps in difficulty",
            ],
        },
        "format": {
            "ro": "Obiective de învățare, explicație, exemple, exerciții, răspunsuri comentate.",
            "en": "Learning objectives, explanation, examples, exercises, worked answers.",
        },
    },
    "social": {
        "keywords": [
            "social media", "instagram", "tiktok", "facebook", "linkedin",
            "twitter", "postare", "reel", "story", "youtube", "podcast",
            "caption", "hashtag", "video scurt", "thread",
        ],
        "role": {
            "ro": "creator de conținut care înțelege că primul cadru și primul rând decid totul",
            "en": "content creator who understands the first frame and the first line decide everything",
        },
        "deliverable": {
            "ro": "pachet de postare: cârlig, corp, încheiere, plus variante de test",
            "en": "a post package: hook, body, closing line, plus test variants",
        },
        "steps": {
            "ro": [
                "Scrie cârligul în maximum 12 cuvinte, cu o tensiune sau o afirmație contraintuitivă.",
                "Livrează valoarea promisă imediat; nu cere derulare pentru a o afla.",
                "Adaptează lungimea și ritmul la platforma indicată.",
                "Termină cu o invitație la reacție care nu sună a cerșit engagement.",
            ],
            "en": [
                "Write the hook in at most 12 words, carrying tension or a counter-intuitive claim.",
                "Deliver the promised value immediately; do not make people scroll for it.",
                "Match length and rhythm to the named platform.",
                "End with an invitation to respond that does not sound like engagement-begging.",
            ],
        },
        "quality": {
            "ro": [
                "primul rând funcționează și fără restul postării",
                "textul poate fi citit pe telefon, în picioare, în doi timpi",
                "nu folosește hashtag-uri decorative fără public real",
            ],
            "en": [
                "the first line works even without the rest of the post",
                "the text can be read on a phone, standing, in two beats",
                "no decorative hashtags without a real audience behind them",
            ],
        },
        "pitfalls": {
            "ro": [
                "cârlige care promit mai mult decât livrează postarea",
                "ton entuziast artificial, cu emoji în loc de conținut",
            ],
            "en": [
                "hooks promising more than the post delivers",
                "artificially enthusiastic tone with emoji standing in for content",
            ],
        },
        "format": {
            "ro": "Cârlig pe rând separat, corp în fragmente scurte, încheiere, listă de variante.",
            "en": "Hook on its own line, body in short fragments, closing line, list of variants.",
        },
    },
    "ux": {
        "keywords": [
            "ux", "ui", "interfata", "design", "flux", "wireframe", "utilizator",
            "aplicatie mobila", "site", "navigare", "accesibilitate", "onboarding",
            "formular", "dashboard", "experienta",
        ],
        "role": {
            "ro": "designer de produs care pornește de la sarcina utilizatorului, nu de la ecrane",
            "en": "product designer who starts from the user's task rather than from screens",
        },
        "deliverable": {
            "ro": "specificație de experiență: fluxuri, stări, texte de interfață și criterii de accesibilitate",
            "en": "an experience specification: flows, states, interface copy and accessibility criteria",
        },
        "steps": {
            "ro": [
                "Descrie sarcina utilizatorului și momentul în care ajunge la ea; abia apoi ecranele.",
                "Definește pentru fiecare ecran starea goală, starea de încărcare, starea de eroare și starea plină.",
                "Scrie textele de interfață exact cum vor apărea, inclusiv mesajele de eroare.",
                "Verifică fluxul pentru navigare de la tastatură, contrast și cititoare de ecran.",
            ],
            "en": [
                "Describe the user's task and the moment they arrive at it; only then the screens.",
                "For each screen define the empty, loading, error and populated states.",
                "Write the interface copy exactly as it will appear, error messages included.",
                "Check the flow for keyboard navigation, contrast and screen readers.",
            ],
        },
        "quality": {
            "ro": [
                "utilizatorul știe în orice moment unde este și cum se întoarce",
                "nicio eroare nu este afișată fără o cale de rezolvare",
                "fluxul funcționează și pe ecran mic",
            ],
            "en": [
                "the user always knows where they are and how to go back",
                "no error is shown without a path to resolution",
                "the flow works on a small screen too",
            ],
        },
        "pitfalls": {
            "ro": [
                "ecrane frumoase care ignoră stările de eroare",
                "texte-substituent lăsate în specificație",
            ],
            "en": [
                "beautiful screens that ignore error states",
                "placeholder copy left in the specification",
            ],
        },
        "format": {
            "ro": "Flux pas cu pas, apoi ecrane cu stări, apoi tabelul textelor de interfață.",
            "en": "Step-by-step flow, then screens with states, then the interface copy table.",
        },
    },
    "descriere-imagini": {
        "keywords": [
            "descriere imagine", "descrierea imaginii", "alt text", "alt-text",
            "text alternativ", "legenda", "caption", "subtitrare imagine",
            "descrie poza", "descrie imaginea", "accesibilitate imagine",
            "descriere foto", "descriere produs din poza", "image description",
        ],
        "role": {
            "ro": "specialist în descrieri de imagini, care scrie deopotrivă pentru cititoare de ecran și pentru motoare de căutare",
            "en": "image description specialist writing for screen readers and search engines alike",
        },
        "deliverable": {
            "ro": "descriere de imagine în trei lungimi: text alternativ scurt, legendă și descriere completă",
            "en": "an image description in three lengths: short alt text, a caption, and a full description",
        },
        "steps": {
            "ro": [
                "Începe cu ce este imaginea: fotografie, ilustrație, captură de ecran, diagramă. Cititorul nu o vede.",
                "Descrie subiectul principal, apoi acțiunea, apoi contextul — în ordinea în care le-ar observa cineva care privește.",
                "Textul alternativ are sub 125 de caractere și spune doar ce e necesar pentru a înțelege pagina.",
                "Legenda adaugă ce nu se vede în imagine: cine, unde, când, de ce contează.",
                "Descrierea completă include detaliile vizuale relevante, inclusiv orice text prezent în imagine, transcris exact.",
                "Nu interpreta emoții sau intenții pe care imaginea nu le arată și nu presupune identitatea, vârsta sau etnia cuiva.",
            ],
            "en": [
                "Start with what the image is: photograph, illustration, screenshot, diagram. The reader cannot see it.",
                "Describe the main subject, then the action, then the context — in the order a viewer would notice them.",
                "Alt text stays under 125 characters and says only what is needed to understand the page.",
                "The caption adds what the image does not show: who, where, when, why it matters.",
                "The full description covers the relevant visual detail, including any text in the image, transcribed exactly.",
                "Do not interpret emotions or intentions the image does not show, and do not assume anyone's identity, age or ethnicity.",
            ],
        },
        "quality": {
            "ro": [
                "cineva care nu vede imaginea își poate face o reprezentare corectă din descriere",
                "textul alternativ nu începe cu „imagine cu” — cititorul de ecran anunță deja că e o imagine",
                "orice text din imagine este transcris, nu rezumat",
                "descrierea nu adaugă informație care nu se vede în cadru",
            ],
            "en": [
                "someone who cannot see the image can form an accurate picture from the description",
                "the alt text does not start with `image of` — the screen reader already announces it is an image",
                "any text inside the image is transcribed, not summarised",
                "the description adds no information that is not visible in the frame",
            ],
        },
        "pitfalls": {
            "ro": [
                "descrieri care enumeră obiecte fără să spună ce se întâmplă",
                "presupuneri despre cine sunt persoanele din imagine",
                "text alternativ umplut cu cuvinte-cheie pentru căutare",
            ],
            "en": [
                "descriptions that list objects without saying what is happening",
                "assumptions about who the people in the image are",
                "alt text stuffed with search keywords",
            ],
        },
        "format": {
            "ro": "Trei blocuri etichetate: TEXT ALTERNATIV (sub 125 de caractere), LEGENDĂ (una-două propoziții), DESCRIERE COMPLETĂ.",
            "en": "Three labelled blocks: ALT TEXT (under 125 characters), CAPTION (one or two sentences), FULL DESCRIPTION.",
        },
    },
    "general": {
        "keywords": [],
        "role": {
            "ro": "expert în domeniul cerut, obișnuit să lucreze cu oameni exigenți",
            "en": "expert in the requested field, used to working with demanding people",
        },
        "deliverable": {
            "ro": "răspuns complet, structurat și direct aplicabil",
            "en": "a complete, structured and directly applicable answer",
        },
        "steps": {
            "ro": [
                "Clarifică ce se cere exact și enunță ipotezele acolo unde cererea este ambiguă.",
                "Structurează răspunsul înainte de a-l scrie, pornind de la concluzie.",
                "Susține fiecare afirmație importantă cu un motiv, un exemplu sau o cifră.",
                "Verifică la final dacă răspunsul rezolvă cererea inițială, nu o versiune mai comodă a ei.",
            ],
            "en": [
                "Clarify exactly what is being asked and state assumptions where the request is ambiguous.",
                "Structure the answer before writing it, starting from the conclusion.",
                "Support every significant claim with a reason, an example or a number.",
                "At the end, check the answer solves the original request rather than a more convenient version of it.",
            ],
        },
        "quality": {
            "ro": [
                "răspunsul poate fi folosit fără întrebări suplimentare",
                "nu conține umplutură sau repetări",
                "limitele răspunsului sunt spuse explicit",
            ],
            "en": [
                "the answer is usable without follow-up questions",
                "it contains no filler or repetition",
                "the limits of the answer are stated explicitly",
            ],
        },
        "pitfalls": {
            "ro": [
                "generalități care s-ar potrivi oricărei alte cereri",
                "enumerarea opțiunilor fără o recomandare",
            ],
            "en": [
                "generalities that would fit any other request",
                "listing options without making a recommendation",
            ],
        },
        "format": {
            "ro": "Concluzie la început, apoi detalii pe secțiuni scurte, apoi limitări.",
            "en": "Conclusion first, then details in short sections, then limitations.",
        },
    },
}


# ---------------------------------------------------------------------------
# DOMENII IMAGINE
# ---------------------------------------------------------------------------
#
# Vocabularul vizual rămâne în engleză indiferent de limba interfeței: modelele
# de imagine sunt antrenate pe descriptori englezești (termeni de optică,
# iluminare, peliculă), iar traducerea lor degradează rezultatul.

COMMON_IMAGE: dict[str, list[str]] = {
    "composition": [
        "rule-of-thirds placement with the focal point slightly off-centre and deliberate negative space on the opposite side",
        "centred symmetrical composition with strong vertical axis and balanced margins",
        "leading lines drawing the eye from the lower-left foreground toward the subject",
        "tight frame-within-a-frame composition using foreground elements as a natural border",
        "layered depth with a defocused foreground element, sharp mid-ground subject and softly separated background",
        "diagonal composition with the subject on the descending line and generous headroom",
        "low horizon with the subject occupying the upper two thirds against open sky or empty wall",
        "tight two-shot spacing where the gap between elements carries as much weight as the elements",
        "spiral arrangement drawing the eye inward through decreasing intervals toward the focal point",
        "flat frontal composition with everything on one plane, graphic and deliberately depthless",
        "off-balance framing with the subject pressed to one edge and the tension left unresolved",
    ],
    "palette": [
        "muted earth palette of warm ochre, clay brown and desaturated sage, with a single deep teal accent",
        "cool monochrome palette built on slate blue and graphite, lifted by one warm amber highlight",
        "high-contrast complementary palette of burnt orange against deep petrol blue",
        "soft pastel palette of blush, bone white and pale eucalyptus, low saturation throughout",
        "rich jewel palette of emerald, oxblood and antique gold with deep shadow density",
        "near-monochrome cream and ivory palette with texture carrying the visual interest",
        "split-tone palette of cool cyan shadows against warm sand highlights, mid-tones left neutral",
        "restrained palette of forest green, charcoal and bone, with weathered brass as the only warm note",
        "washed coastal palette of pale grey-blue, salt white and driftwood, low contrast throughout",
        "high-key palette built almost entirely of light values, with a single dark anchor for structure",
        "warm terracotta and dusty rose against deep shadow, saturated but never fluorescent",
    ],
    "mood": [
        "quiet, contemplative, unhurried",
        "tense and cinematic, charged with anticipation",
        "warm, intimate and reassuring",
        "clean, precise and confident",
        "nostalgic and slightly melancholic",
        "energetic and optimistic without being saccharine",
        "austere and formal, with a deliberate emotional distance",
        "sensual and warm, close and unhurried",
        "unsettling in a way that is hard to place",
        "hopeful but tired, the moment after effort rather than before it",
    ],
    "detail": [
        "fine surface texture visible — fabric weave, skin pores, dust motes in the air",
        "crisp micro-detail on the primary surfaces, gently falling off toward the frame edges",
        "tactile material rendering: brushed metal grain, matte paper fibre, condensation beads",
        "photographic grain structure of medium-format film, subtle and even",
        "hyper-fine detail in the focal plane falling to soft impressionistic form at the edges",
        "raw physical detail: chipped paint, hairline scratches, uneven wear along contact edges",
        "clean, almost clinical rendering where every surface is described precisely and nothing is suggested",
        "soft-focus rendering with detail present but never harsh, edges bloomed slightly by the light",
    ],
    "quality": [
        "photorealistic, ultra-detailed, sharp focus on the subject, natural depth of field, 8K resolution, professional colour grading",
        "highly detailed, physically accurate materials and light transport, no visible rendering artefacts",
    ],
    "negative": [
        "blurry", "low resolution", "distorted proportions", "extra limbs",
        "malformed hands", "watermark", "signature", "text artefacts",
        "oversaturated colours", "harsh on-camera flash", "plastic skin",
        "duplicated features", "cropped subject", "jpeg compression artefacts",
        "cluttered background", "unnatural anatomy",
    ],
}

IMAGE_DOMAINS: dict[str, dict[str, object]] = {
    "portret": {
        "keywords": [
            "portret", "portrait", "persoana", "om", "fata", "chip", "barbat",
            "femeie", "copil", "model", "headshot", "selfie", "actor",
            "batran", "batrana", "tanar", "muncitor", "pescar", "bucatar",
            "man", "woman", "girl", "boy", "person", "face", "elderly",
            "worker", "fisherman", "chef", "musician", "dancer",
        ],
        "subject_hint": {
            "ro": "persoana din centrul cadrului",
            "en": "the person at the centre of the frame",
        },
        "environment": [
            "seamless studio backdrop in deep charcoal, subject separated by a rim of light",
            "sunlit interior beside a tall window, sheer curtain diffusing the light, room falling into shadow behind",
            "urban street at blue hour, bokeh of shop signs compressed behind the subject",
            "weathered plaster wall in warm afternoon light, shallow depth keeping only the eyes sharp",
        ],
        "camera": [
            "medium close-up, eye level, camera at the subject's eye height",
            "tight head-and-shoulders crop, slightly low angle for quiet authority",
            "three-quarter body shot, eye level, subject turned fifteen degrees from the lens",
        ],
        "lens": [
            "85mm prime at f/1.8, shallow depth of field, creamy background separation",
            "50mm at f/2.0, natural perspective with mild environmental context",
            "135mm at f/2.8, compressed perspective and flattering facial rendering",
        ],
        "lighting": [
            "large softbox key at 45 degrees camera-left, white bounce fill camera-right, subtle hair light from behind",
            "single window as key light, natural falloff, deep unfilled shadow on the shadow side for drama",
            "golden-hour backlight creating a rim around hair and shoulders, reflector lifting the face",
            "overcast daylight, even and shadowless, catchlights high in the eyes",
        ],
        "style": [
            "editorial portrait photography in the tradition of magazine cover work",
            "documentary portraiture, unposed, honest, no retouching gloss",
            "classic studio portraiture with controlled falloff and deliberate shadow shapes",
        ],
        "extra": [
            "natural skin texture retained, pores and fine lines visible, no beauty-filter smoothing",
            "genuine micro-expression rather than a held smile; the gaze carries the image",
        ],
        "negative": ["deformed face", "asymmetrical eyes", "waxy skin", "airbrushed texture"],
    },
    "produs": {
        "keywords": [
            "produs", "product", "packshot", "ambalaj", "sticla", "cutie",
            "telefon", "pantof", "ceas", "cosmetic", "bautura", "gadget",
            "ecommerce", "magazin", "parfum", "borcan", "bottle", "packaging",
            "shoe", "sneaker", "watch", "device", "perfume", "jar", "can",
        ],
        "subject_hint": {
            "ro": "produsul care trebuie să vândă din prima privire",
            "en": "the product that has to sell at first glance",
        },
        "environment": [
            "clean seamless backdrop in soft gradient grey, subtle contact shadow anchoring the object",
            "textured stone slab surface with a single dried botanical element for scale",
            "reflective black acrylic surface producing a controlled mirror reflection below the product",
            "lifestyle context: kitchen counter in morning light, props deliberately out of focus",
        ],
        "camera": [
            "three-quarter hero angle, slightly above the product, full object in frame with breathing room",
            "straight-on eye-level product shot, perfectly square to the label",
            "tight macro detail of the material transition and logo embossing",
        ],
        "lens": [
            "100mm macro at f/8, focus stacked for edge-to-edge sharpness",
            "50mm at f/5.6, mild perspective, product occupying two thirds of the frame",
        ],
        "lighting": [
            "large overhead softbox with white bounce cards left and right, gradient falloff on the background",
            "strip-box rim lights on both sides defining the silhouette, soft frontal fill",
            "single hard light producing a crisp defined shadow, high-contrast advertising look",
        ],
        "style": [
            "high-end commercial product photography, catalogue standard",
            "minimalist Scandinavian advertising aesthetic, generous negative space",
            "premium beauty-industry still life with controlled speculars",
        ],
        "extra": [
            "labels and typography crisp and correctly proportioned, material finish clearly readable",
            "no dust or fingerprints on the surfaces, speculars shaped rather than blown out",
        ],
        "negative": ["floating object without shadow", "distorted label text", "blown highlights", "visible studio equipment"],
    },
    "peisaj": {
        "keywords": [
            "peisaj", "landscape", "natura", "munte", "munti", "mare", "padure",
            "camp", "rau", "lac", "desert", "cer", "apus", "rasarit", "furtuna",
            "plaja", "valea", "deal", "mountain", "mountains", "sea", "ocean",
            "forest", "field", "river", "lake", "sunset", "sunrise", "beach",
            "valley", "cliff", "storm", "sky",
        ],
        "subject_hint": {
            "ro": "peisajul, cu un element clar de interes în prim-plan",
            "en": "the landscape, with one clear point of interest in the foreground",
        },
        "environment": [
            "mountain valley with layered ridgelines fading into atmospheric haze",
            "wind-shaped coastline with long exposure smoothing the water into mist",
            "old-growth forest interior, shafts of light through morning fog between trunks",
            "open plain under a towering cloud formation, horizon low in the frame",
        ],
        "camera": [
            "wide establishing shot, tripod height, horizon on the lower third",
            "elevated vantage point looking down across receding layers of terrain",
            "low camera position emphasising foreground rock and texture",
        ],
        "lens": [
            "24mm at f/11, hyperfocal distance, sharp from foreground to horizon",
            "16mm ultra-wide at f/8 with strong foreground presence and deep perspective",
            "70-200mm telephoto at f/8 compressing distant ridges into graphic layers",
        ],
        "lighting": [
            "golden-hour side light raking across the terrain, long shadows revealing form",
            "blue-hour ambient light, cool shadows and a warm residual glow at the horizon",
            "broken storm light with a single shaft illuminating the focal area",
        ],
        "style": [
            "large-format landscape photography with meticulous tonal control",
            "atmospheric naturalism, restrained saturation, true-to-scene colour",
        ],
        "extra": [
            "convincing atmospheric perspective — distant planes lighter and lower in contrast",
            "weather and light consistent across the whole frame",
        ],
        "negative": ["hdr halos", "oversaturated sunset", "fake-looking sky replacement", "tilted horizon"],
    },
    "arhitectura": {
        "keywords": [
            "arhitectura", "cladire", "casa", "building", "constructie",
            "fatada", "urban", "oras", "pod", "biserica", "muzeu", "structura",
            "turn", "architecture", "facade", "house", "tower", "bridge",
            "church", "museum", "skyscraper", "brutalist", "brutalista",
        ],
        "subject_hint": {
            "ro": "construcția și relația ei cu spațiul din jur",
            "en": "the building and its relationship to the space around it",
        },
        "environment": [
            "quiet street with no pedestrians, early morning, clean pavement",
            "dense urban context where neighbouring volumes frame the facade",
            "open landscape setting where the structure reads as a single sculptural object",
        ],
        "camera": [
            "one-point perspective straight on to the facade, verticals perfectly parallel",
            "three-quarter view revealing two elevations and the massing of the volume",
            "worm's-eye view emphasising height and structural rhythm",
        ],
        "lens": [
            "24mm tilt-shift at f/8, corrected verticals, no keystone distortion",
            "35mm at f/9, natural perspective, full structure in frame",
        ],
        "lighting": [
            "raking late-afternoon sun revealing material texture and casting long geometric shadows",
            "blue-hour exterior with warm interior lighting glowing through the glazing",
            "flat overcast light for even material description and honest colour",
        ],
        "style": [
            "professional architectural photography for a design monograph",
            "brutalist-documentary approach, geometry and material foremost",
        ],
        "extra": [
            "structurally plausible geometry — consistent floor heights, aligned openings, coherent load paths",
            "materials clearly identifiable: board-marked concrete, oxidised steel, fluted glass",
        ],
        "negative": ["converging verticals", "impossible geometry", "melting structure", "warped windows"],
    },
    "mancare": {
        "keywords": [
            "mancare", "food", "preparat", "reteta", "farfurie", "desert",
            "cafea", "restaurant", "bucatarie", "paine", "cocktail", "meniu",
            "prajitura", "supa", "paste", "dish", "recipe", "plate", "coffee",
            "bread", "cake", "pasta", "soup", "pizza", "breakfast",
        ],
        "subject_hint": {
            "ro": "preparatul, fotografiat astfel încât să pară proaspăt gătit",
            "en": "the dish, shot so it reads as freshly made",
        },
        "environment": [
            "dark slate surface with scattered ingredient traces and a linen napkin at the edge",
            "warm wooden table in window light, secondary props softly out of focus",
            "clean marble counter, minimal styling, one utensil entering the frame",
        ],
        "camera": [
            "45-degree angle, the natural way a diner sees the plate",
            "overhead flat-lay, elements arranged with deliberate spacing",
            "low table-level angle emphasising height and layering of the dish",
        ],
        "lens": [
            "100mm macro at f/4, shallow plane keeping the front edge crisp",
            "50mm at f/5.6, whole plate and immediate context in focus",
        ],
        "lighting": [
            "single large window as backlight with a white bounce card in front, translucency in sauces and glassware",
            "soft side light with a black flag deepening the shadow side for appetite appeal",
        ],
        "style": [
            "editorial food photography for a cookbook spread",
            "rustic, unstyled realism — imperfect edges, genuine crumbs",
        ],
        "extra": [
            "steam, gloss and moisture rendered convincingly; textures read as edible",
            "portion and plating consistent with how the dish is actually served",
        ],
        "negative": ["plastic-looking food", "artificial gloss", "melting textures", "unappetising grey tones"],
    },
    "concept-art": {
        "keywords": [
            "concept art", "fantezie", "fantasy", "sci-fi", "creatura",
            "monstru", "robot", "astronava", "lume", "mitologic", "epic",
            "joc video", "arma", "vehicul", "dragon", "plutitor", "cyberpunk",
            "creature", "monster", "spaceship", "starship", "mech", "alien",
            "futuristic", "postapocaliptic", "dystopian",
        ],
        "subject_hint": {
            "ro": "subiectul conceptului, prezentat ca într-o planșă de producție",
            "en": "the concept subject, presented as a production art plate",
        },
        "environment": [
            "vast environment establishing scale, small human figure included for reference",
            "neutral gradient backdrop so the silhouette reads cleanly",
            "atmospheric setting with volumetric haze separating depth planes",
        ],
        "camera": [
            "cinematic wide shot, low horizon, subject dominating the upper frame",
            "three-quarter hero angle, slightly below eye level for scale and presence",
        ],
        "lens": [
            "anamorphic 40mm equivalent, cinematic framing with gentle edge distortion",
            "35mm equivalent, natural but dramatic perspective",
        ],
        "lighting": [
            "strong key from one side with cool bounce fill, dramatic value separation",
            "backlit silhouette with volumetric god rays and glowing atmospheric particles",
            "practical light sources within the scene motivating every highlight",
        ],
        "style": [
            "digital concept art in the tradition of feature-film production design, painterly but precise",
            "matte-painting quality with strong graphic silhouette and readable value structure",
        ],
        "extra": [
            "silhouette readable in pure black; design language consistent across every element",
            "believable functional detail — panel lines, wear patterns, structural logic",
        ],
        "negative": ["muddy values", "unreadable silhouette", "random detail noise", "inconsistent design language"],
    },
    "personaj": {
        "keywords": [
            "personaj", "character", "erou", "avatar", "mascota", "razboinic",
            "vrajitoare", "cavaler", "design de personaj", "turnaround",
        ],
        "subject_hint": {
            "ro": "personajul, cu identitate vizuală clară de la prima privire",
            "en": "the character, with a visual identity readable at first glance",
        },
        "environment": [
            "neutral studio-grey backdrop, full figure isolated for design clarity",
            "minimal contextual setting hinting at the character's world without competing",
        ],
        "camera": [
            "full-body three-quarter view, feet in frame, slight low angle",
            "medium shot from the knees up, weight on one leg, natural contrapposto",
        ],
        "lens": ["50mm equivalent, minimal distortion, honest proportions"],
        "lighting": [
            "three-point setup: key at 45 degrees, cool fill, crisp rim separating the figure from the background",
            "dramatic single-source light shaping the costume's volumes",
        ],
        "style": [
            "character design sheet quality, clean rendering, every costume element deliberate",
            "stylised realism with exaggerated proportions held consistently",
        ],
        "extra": [
            "costume, materials and props tell the character's story without captions",
            "hands, footwear and fastenings fully resolved rather than suggested",
        ],
        "negative": ["extra fingers", "inconsistent costume details", "floating accessories", "mismatched proportions"],
    },
    "ilustratie": {
        "keywords": [
            "ilustratie", "illustration", "desen", "grafica", "carte pentru copii",
            "poster", "afis", "coperta", "banda desenata", "vectorial", "icon",
            "editorial", "acuarela", "pictura", "drawing", "painting",
            "watercolor", "watercolour", "cartoon", "logo", "cover", "comic",
            "vector", "sketch",
        ],
        "subject_hint": {
            "ro": "scena ilustrată, construită în jurul unei singure idei vizuale",
            "en": "the illustrated scene, built around a single visual idea",
        },
        "environment": [
            "flat stylised background with simplified shapes and no unnecessary detail",
            "textured paper ground where the medium itself is part of the image",
        ],
        "camera": [
            "flat frontal composition, graphic and poster-like",
            "gentle isometric view giving depth without perspective complexity",
        ],
        "lens": ["not applicable — illustrated perspective, deliberately non-photographic"],
        "lighting": [
            "flat graphic lighting with two-value shading and a single accent shadow colour",
            "warm ambient glow with soft gradient transitions painted rather than rendered",
        ],
        "style": [
            "modern editorial illustration, limited palette, confident shape language",
            "watercolour and ink with visible brush edges and paper grain",
            "flat vector illustration with clean geometry and generous negative space",
            "hand-drawn children's-book illustration, warm and rounded, gentle outlines",
        ],
        "extra": [
            "consistent line weight and a coherent shape vocabulary across the whole image",
            "the composition reads instantly at thumbnail size",
        ],
        "negative": ["photorealistic rendering", "muddy colour mixing", "inconsistent line weight", "3d plastic shading"],
    },
    "interior": {
        "keywords": [
            "interior", "camera", "living", "dormitor", "birou", "amenajare",
            "mobila", "decor", "bucatarie interior", "hotel", "cafenea",
            "room", "bedroom", "office", "cafe", "lobby", "furniture",
            "apartment", "apartament", "showroom",
        ],
        "subject_hint": {
            "ro": "spațiul interior și atmosfera pe care o creează",
            "en": "the interior space and the atmosphere it creates",
        },
        "environment": [
            "residential room with lived-in detail — a book left open, a throw off-centre",
            "showroom-clean space, everything intentional, nothing accidental",
            "commercial hospitality interior at dusk with layered practical lighting",
        ],
        "camera": [
            "one-point perspective from the doorway, verticals parallel, full room read",
            "corner vignette showing the relationship between two furniture groups",
        ],
        "lens": ["24mm tilt-shift at f/8, corrected verticals", "35mm at f/5.6, natural room proportions"],
        "lighting": [
            "daylight through a large window as the dominant source, warm practicals switched on for balance",
            "evening interior lit entirely by practicals, pools of warm light and deep corners",
        ],
        "style": [
            "interior design magazine photography, restrained and precise",
            "warm documentary interior with genuine signs of habitation",
        ],
        "extra": [
            "furniture at plausible scale relative to the ceiling height and door openings",
            "materials clearly distinguishable: oak, boucle, brushed brass, lime plaster",
        ],
        "negative": ["impossible room geometry", "furniture at wrong scale", "duplicated windows", "harsh mixed white balance"],
    },
    "general": {
        "keywords": [],
        "subject_hint": {
            "ro": "subiectul principal al imaginii",
            "en": "the main subject of the image",
        },
        "environment": [
            "context that supports the subject without competing for attention",
            "simplified setting with clear separation between subject and background",
            "richly detailed environment where every element reinforces the story",
        ],
        "camera": [
            "medium shot at eye level, subject occupying roughly two thirds of the frame",
            "wide shot establishing the subject within its context",
            "close shot on the most telling detail",
        ],
        "lens": ["50mm at f/2.8, natural perspective", "35mm at f/4, mild context inclusion"],
        "lighting": [
            "soft directional key light with gentle fill, natural falloff",
            "dramatic side light with deep shadows and shaped highlights",
            "even diffused daylight, no harsh transitions",
        ],
        "style": [
            "photorealistic, contemporary, restrained processing",
            "cinematic still with deliberate colour grading",
        ],
        "extra": [
            "every element in frame is there for a reason",
            "coherent single light direction across the whole image",
        ],
        "negative": [],
    },
}


# ---------------------------------------------------------------------------
# TONURI (pentru prompturi de text)
# ---------------------------------------------------------------------------

TONES: dict[str, dict[str, str]] = {
    "profesional": {
        "ro": "profesional și direct, fără formalism inutil",
        "en": "professional and direct, without needless formality",
    },
    "prietenos": {
        "ro": "cald și accesibil, ca o explicație dată unui coleg",
        "en": "warm and approachable, like an explanation given to a colleague",
    },
    "tehnic": {
        "ro": "tehnic și precis, cu terminologie exactă",
        "en": "technical and precise, with exact terminology",
    },
    "persuasiv": {
        "ro": "persuasiv, cu energie controlată și dovezi la vedere",
        "en": "persuasive, with controlled energy and visible proof",
    },
    "academic": {
        "ro": "academic, sobru, cu argumentare explicită",
        "en": "academic, sober, with explicit argumentation",
    },
    "jurnalistic": {
        "ro": "jurnalistic: fapte întâi, adjective aproape deloc",
        "en": "journalistic: facts first, adjectives almost never",
    },
    "neutru": {
        "ro": "neutru și clar",
        "en": "neutral and clear",
    },
}

# Formate de imagine uzuale, pentru sugestia raportului de aspect
ASPECT_BY_DOMAIN: dict[str, str] = {
    "portret": "4:5",
    "produs": "1:1",
    "peisaj": "16:9",
    "arhitectura": "4:5",
    "mancare": "4:5",
    "concept-art": "16:9",
    "personaj": "2:3",
    "ilustratie": "1:1",
    "interior": "3:2",
    "general": "16:9",
}


# ---------------------------------------------------------------------------
# DOMENII VIDEO
# ---------------------------------------------------------------------------
#
# Un clip nu e o imagine care se mișcă: are durată, ritm, mișcare de cameră și,
# tot mai des, sunet. Vocabularul de aici acoperă exact ce lipsește imaginii.

COMMON_VIDEO: dict[str, list[str]] = {
    "camera_move": [
        "slow dolly in toward the subject, ending in a medium close-up, no zoom",
        "locked-off static frame; only the subject moves within it",
        "smooth lateral tracking shot following the subject at walking pace",
        "handheld with restrained movement, breathing rather than shaking",
        "slow crane rise revealing the wider space behind the subject",
        "gentle orbit around the subject, holding the same distance throughout",
        "push-in on a fixed axis, the background compressing as the shot tightens",
    ],
    "pacing": [
        "one continuous take, no cuts, letting the moment play out in real time",
        "three beats: establish, develop, resolve, with the change landing in the final third",
        "steady rhythm with a single change of energy at the midpoint",
        "slow build in the first half, quicker resolution in the second",
    ],
    "physics": [
        "movement obeys weight and inertia: nothing accelerates instantly and nothing floats",
        "cloth, hair and liquid respond to the motion with a natural lag",
        "contact between objects produces the reaction it would in reality",
    ],
    "audio": [
        "ambient sound of the location, no music, with one clear diegetic detail",
        "sparse score entering only in the final third, under the ambience",
        "no dialogue; the sound design carries the emotion",
        "close, intimate sound: breath, fabric, footsteps on the surface underfoot",
    ],
    "transition": [
        "opens on the action already in progress and ends before it fully resolves",
        "starts from black and holds one beat of stillness before the movement begins",
        "ends on a held frame that works as a still image",
    ],
    "look": [
        "cinematic film look, shallow depth of field, natural motion blur at 180-degree shutter",
        "documentary realism, available light, no stylised grade",
        "clean commercial polish, controlled lighting, high dynamic range",
    ],
    "negative": [
        "morphing faces", "flickering", "warping limbs", "unstable geometry",
        "sudden style shifts", "text artefacts", "watermark", "jittery motion",
        "objects popping in and out", "inconsistent lighting between frames",
        "unnatural speed ramps", "duplicated subjects",
    ],
}

VIDEO_DOMAINS: dict[str, dict[str, object]] = {
    "reclama": {
        "keywords": [
            "reclama", "ad", "spot", "campanie", "promo", "produs video",
            "commercial", "brand video", "lansare",
        ],
        "shot": [
            "product hero shot with the subject entering frame in the first second",
            "lifestyle scene where the product is used naturally, never presented to camera",
        ],
        "beat": [
            "the benefit is visible before the brand appears",
            "the final frame holds the product and nothing else",
        ],
    },
    "cinematic": {
        "keywords": [
            "cinematic", "film", "scena", "scenă", "trailer", "scurtmetraj",
            "atmosferic", "dramatic",
        ],
        "shot": [
            "wide establishing frame that places the character in their world",
            "intimate close-up held long enough to become uncomfortable",
        ],
        "beat": [
            "the emotional turn happens in a single unbroken moment",
            "the frame withholds as much as it shows",
        ],
    },
    "social": {
        "keywords": [
            "tiktok", "reel", "short", "shorts", "story", "social", "viral",
            "vertical", "clip scurt",
        ],
        "shot": [
            "vertical framing with the subject centred and large in frame",
            "first frame is a complete visual hook, readable without sound",
        ],
        "beat": [
            "the payoff arrives before the third second",
            "the last frame loops cleanly back into the first",
        ],
    },
    "tutorial": {
        "keywords": [
            "tutorial", "explicativ", "demo", "demonstratie", "curs video",
            "explainer", "how-to", "pas cu pas",
        ],
        "shot": [
            "clear overhead or over-the-shoulder view of the hands and the work surface",
            "framing that keeps both the tool and the result visible at once",
        ],
        "beat": [
            "each step is visually distinct from the one before it",
            "nothing important happens outside the frame",
        ],
    },
    "produs": {
        "keywords": ["packshot video", "produs", "unboxing", "detaliu produs"],
        "shot": [
            "slow rotation around the product against a controlled background",
            "macro pass across the material transitions and the branding",
        ],
        "beat": [
            "every surface of the product is seen at least once",
            "the movement never outpaces the eye",
        ],
    },
    "general": {
        "keywords": [],
        "shot": [
            "medium shot holding the subject and enough context to read the situation",
            "framing that stays stable while the action develops inside it",
        ],
        "beat": [
            "one thing changes between the first frame and the last",
            "the shot earns its duration",
        ],
    },
}

ASPECT_BY_VIDEO_DOMAIN: dict[str, str] = {
    "reclama": "16:9",
    "cinematic": "21:9",
    "social": "9:16",
    "tutorial": "16:9",
    "produs": "1:1",
    "general": "16:9",
}
