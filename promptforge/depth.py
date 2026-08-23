"""Materialul care se adaugă la bugete mari de cuvinte.

Un prompt de 300 de cuvinte spune ce vrei. Unul de 2000 spune și cum arată
reușita, unde se greșește de obicei și ce să facă modelul când se blochează.
Secțiunile de aici sunt exact asta: conținut real, adăugat doar când bugetul îl
cere, niciodată umplutură.

Tot ce e aici are `min_lines=0` și prioritate mare, deci la bugete mici dispare
primul, fără să atingă structura de bază.
"""

from __future__ import annotations

from .catalog import PLATFORMS
from .models import Section

# ---------------------------------------------------------------------------
# Secțiuni suplimentare pentru prompturile de text
# ---------------------------------------------------------------------------

_TEXT_DEPTH: list[dict] = [
    {
        "ro": ("CRITERII DE ACCEPTANȚĂ", [
            "Rezultatul e gata când cineva care nu a participat la discuție îl poate folosi fără să pună nicio întrebare.",
            "Fiecare cerință din secțiunile de mai sus are un corespondent vizibil în rezultat; dacă una lipsește, spui de ce.",
            "Nimic din ce livrezi nu are nevoie de o completare ulterioară pentru a funcționa.",
        ]),
        "en": ("ACCEPTANCE CRITERIA", [
            "The result is done when someone who was not part of the discussion can use it without asking a single question.",
            "Every requirement above has a visible counterpart in the result; if one is missing, you say why.",
            "Nothing you deliver needs a follow-up to work.",
        ]),
    },
    {
        "ro": ("ÎNTREBĂRILE LA CARE RĂSPUNDE REZULTATUL", [
            "Înainte de a scrie, formulează cele trei-cinci întrebări la care rezultatul trebuie să răspundă.",
            "Fiecare secțiune pe care o scrii răspunde la cel puțin una dintre ele; ce nu răspunde la niciuna nu intră.",
            "La final, verifică lista: dacă o întrebare a rămas fără răspuns, ai livrat altceva decât s-a cerut.",
        ]),
        "en": ("QUESTIONS THE RESULT MUST ANSWER", [
            "Before writing, formulate the three to five questions the result has to answer.",
            "Every section you write answers at least one of them; anything that answers none does not go in.",
            "At the end, check the list: if a question is left unanswered, you delivered something other than what was asked.",
        ]),
    },
    {
        "ro": ("STRUCTURA RECOMANDATĂ", [
            "Pornește de la concluzie, nu de la context: cititorul decide în primele rânduri dacă merge mai departe.",
            "Fiecare secțiune are un singur rol; dacă două secțiuni fac același lucru, unește-le.",
            "Ordinea secțiunilor urmează ordinea în care cititorul are nevoie de informație, nu ordinea în care ai gândit-o tu.",
            "Titlurile sunt informative, nu decorative: din ele singure trebuie să se înțeleagă traseul.",
        ]),
        "en": ("RECOMMENDED STRUCTURE", [
            "Start from the conclusion, not the context: the reader decides in the first lines whether to continue.",
            "Each section has exactly one job; if two sections do the same thing, merge them.",
            "Section order follows the order in which the reader needs the information, not the order you thought of it.",
            "Headings are informative rather than decorative: the path should be clear from them alone.",
        ]),
    },
    {
        "ro": ("EXEMPLU DE BUN ȘI DE SLAB", [
            "Slab: „soluția oferă multiple beneficii și optimizează procesele.” Nu se poate verifica nimic din propoziția asta.",
            "Bun: „reduce timpul de procesare de la 40 la 12 minute, pentru că elimină pasul de validare manuală.”",
            "Diferența nu e lungimea, ci faptul că a doua propoziție poate fi contrazisă cu date. Scrie propoziții care pot fi contrazise.",
        ]),
        "en": ("AN EXAMPLE OF GOOD AND BAD", [
            "Bad: `the solution offers multiple benefits and optimises processes.` Nothing in that sentence can be checked.",
            "Good: `it cuts processing from 40 minutes to 12, because it removes the manual validation step.`",
            "The difference is not length but that the second sentence can be contradicted with data. Write sentences that can be contradicted.",
        ]),
    },
    {
        "ro": ("IPOTEZE ȘI NECUNOSCUTE", [
            "Ține o listă scurtă cu ce ai presupus fiindcă cererea nu spunea. O pui la finalul rezultatului, nu la început.",
            "Pentru fiecare ipoteză, spune ce s-ar schimba în rezultat dacă ar fi greșită.",
            "Nu transforma o necunoscută într-o certitudine ca să sune mai bine. O ipoteză marcată e utilă; una ascunsă e o eroare.",
        ]),
        "en": ("ASSUMPTIONS AND UNKNOWNS", [
            "Keep a short list of what you assumed because the request did not say. Put it at the end of the result, not the start.",
            "For each assumption, state what would change in the result if it turned out wrong.",
            "Do not turn an unknown into a certainty to make it sound better. A flagged assumption is useful; a hidden one is a defect.",
        ]),
    },
    {
        "ro": ("MODURI TIPICE DE EȘEC", [
            "Răspuns corect, dar la altă întrebare decât cea pusă: verifică cererea originală înainte de a livra.",
            "Rezultat care enumeră opțiuni fără să recomande niciuna, lăsând decizia grea tot în seama cititorului.",
            "Text care sună competent fiindcă folosește vocabularul domeniului, dar nu conține niciun mecanism concret.",
            "Detaliu abundent acolo unde e ușor de produs și subțire exact unde e greu — și unde contează.",
        ]),
        "en": ("TYPICAL FAILURE MODES", [
            "A correct answer to a different question than the one asked: check the original request before delivering.",
            "A result that lists options without recommending one, leaving the hard decision with the reader.",
            "Text that sounds competent because it uses the field's vocabulary but contains no concrete mechanism.",
            "Abundant detail where it is easy to produce and thin exactly where it is hard — and where it matters.",
        ]),
    },
    {
        "ro": ("PRIORITIZARE ÎN CAZ DE CONFLICT", [
            "Dacă nu poți respecta toate cerințele, ordinea e: corectitudinea faptelor, apoi acoperirea cererii, apoi forma, apoi lungimea.",
            "Sacrifică eleganța înaintea exactității și lungimea înaintea completitudinii.",
            "Când tai ceva din cauza unui conflict, spui într-un rând ce ai tăiat și de ce.",
        ]),
        "en": ("PRIORITIES WHEN REQUIREMENTS CONFLICT", [
            "If you cannot satisfy every requirement, the order is: factual correctness, then coverage of the request, then form, then length.",
            "Sacrifice elegance before accuracy, and length before completeness.",
            "When you cut something because of a conflict, say in one line what you cut and why.",
        ]),
    },
    {
        "ro": ("GESTIONAREA INCERTITUDINII", [
            "Distinge trei situații: știi, estimezi, nu ai de unde ști. Marchează-le diferit în text.",
            "O estimare vine cu baza ei: „pe la 15%, pornind de la mărimea tipică a pieței”, nu doar „aproximativ 15%”.",
            "Când nu ai de unde ști, spune asta scurt și treci mai departe; nu compensa cu prudență în tot restul textului.",
        ]),
        "en": ("HANDLING UNCERTAINTY", [
            "Distinguish three cases: you know, you are estimating, you cannot know. Mark them differently in the text.",
            "An estimate comes with its basis: `around 15%, from typical market size`, not just `roughly 15%`.",
            "When you cannot know, say so briefly and move on; do not compensate with hedging throughout the rest.",
        ]),
    },
    {
        "ro": ("VOCABULAR ȘI TERMINOLOGIE", [
            "Alege un singur termen pentru fiecare noțiune și folosește-l consecvent; sinonimele elegante creează confuzie.",
            "Orice termen tehnic apare definit la prima folosire, într-o propoziție, fără paranteze lungi.",
            "Evită abrevierile pe care nu le-ai introdus și metaforele care cer o explicație suplimentară.",
        ]),
        "en": ("VOCABULARY AND TERMINOLOGY", [
            "Pick one term per concept and use it consistently; elegant synonyms create confusion.",
            "Any technical term is defined at first use, in one sentence, without long parentheses.",
            "Avoid abbreviations you have not introduced and metaphors that need a further explanation.",
        ]),
    },
    {
        "ro": ("RITM ȘI LIZIBILITATE", [
            "Alternează fraze scurte cu fraze medii. Trei fraze lungi la rând pierd cititorul, indiferent cât de bune sunt.",
            "Un paragraf are o singură idee. Când al doilea gând vrea să intre, începe un paragraf nou.",
            "Folosește liste doar pentru elemente cu adevărat paralele; altfel proza spune mai mult în mai puțin spațiu.",
        ]),
        "en": ("RHYTHM AND READABILITY", [
            "Alternate short sentences with medium ones. Three long sentences in a row lose the reader, however good they are.",
            "One paragraph, one idea. When a second thought wants in, start a new paragraph.",
            "Use lists only for genuinely parallel items; otherwise prose says more in less space.",
        ]),
    },
    {
        "ro": ("CE FACI DACĂ TE BLOCHEZI", [
            "Dacă o parte a cererii pare imposibilă, livrează restul complet și explică într-un paragraf ce te-a blocat și ce ți-ar debloca.",
            "Nu înlocui partea grea cu o variantă mai ușoară fără să spui că ai făcut schimbul.",
            "Un rezultat parțial, cu limitele declarate, e util. Un rezultat complet în aparență, dar ocolit pe dinăuntru, nu e.",
        ]),
        "en": ("WHAT TO DO IF YOU GET STUCK", [
            "If part of the request seems impossible, deliver the rest in full and explain in one paragraph what blocked you and what would unblock it.",
            "Do not swap the hard part for an easier one without saying you made the swap.",
            "A partial result with declared limits is useful. One that looks complete but was quietly worked around is not.",
        ]),
    },
    {
        "ro": ("REVIZUIRE ÎNAINTE DE LIVRARE", [
            "Citește rezultatul o dată de la capăt, ca și cum l-ai primi de la altcineva și ai avea puțin timp.",
            "Taie prima și ultima propoziție a fiecărei secțiuni și verifică dacă s-a pierdut ceva. De obicei nu.",
            "Caută propozițiile care încep cu „este important să” sau „trebuie menționat că” și rescrie-le direct.",
            "Verifică fiecare cifră și fiecare denumire proprie. O singură eroare de acest fel discreditează tot restul.",
        ]),
        "en": ("REVISION BEFORE DELIVERY", [
            "Read the result once from the top, as if someone handed it to you and you were short on time.",
            "Cut the first and last sentence of each section and check whether anything was lost. Usually not.",
            "Look for sentences starting with `it is important to` or `it should be mentioned that` and rewrite them directly.",
            "Verify every number and every proper name. A single error of that kind discredits everything else.",
        ]),
    },
    {
        "ro": ("CONTEXTUL ÎN CARE VA FI FOLOSIT", [
            "Rezultatul nu e citit în liniște, de la cap la coadă. E scanat, pe ecran, între alte lucruri.",
            "Scrie astfel încât cineva care citește doar titlurile și primele rânduri să plece cu mesajul corect.",
            "Presupune că va fi copiat și lipit în altă parte: să funcționeze și scos din contextul ăsta.",
        ]),
        "en": ("THE CONTEXT IT WILL BE USED IN", [
            "The result is not read quietly, end to end. It is scanned, on a screen, between other things.",
            "Write so that someone reading only the headings and opening lines leaves with the right message.",
            "Assume it will be copied and pasted elsewhere: it has to work outside this context too.",
        ]),
    },
    {
        "ro": ("PROFUNZIME ÎN LOC DE LUNGIME", [
            "Dacă un punct poate fi ilustrat, ilustrează-l. Dacă poate fi cuantificat, cuantifică-l. Dacă depinde de context, spune de care.",
            "Un exemplu concret valorează mai mult decât trei propoziții de generalitate; preferă-l de fiecare dată.",
            "Adâncimea nu înseamnă mai multe cuvinte pe aceeași idee, ci mai multe niveluri de detaliu verificabil.",
        ]),
        "en": ("DEPTH INSTEAD OF LENGTH", [
            "If a point can be illustrated, illustrate it. If it can be quantified, quantify it. If it depends on context, say which.",
            "One concrete example beats three sentences of generality; prefer it every time.",
            "Depth is not more words on the same idea but more levels of checkable detail.",
        ]),
    },
    {
        "ro": ("TRATAREA CIFRELOR ȘI A DATELOR", [
            "Orice cifră vine cu unitatea, perioada și sursa ei; „creștere de 30%” fără interval de timp nu înseamnă nimic.",
            "Nu rotunji în sus ca să sune mai bine și nu prezenta o valoare medie fără să spui cât de împrăștiate sunt datele.",
            "Când compari două mărimi, verifică întâi că se măsoară la fel; altfel comparația e falsă chiar dacă aritmetica e corectă.",
            "Dacă o cifră e centrală pentru concluzie, spune explicit ce s-ar schimba dacă ar fi cu 50% mai mică.",
        ]),
        "en": ("HANDLING NUMBERS AND DATA", [
            "Every number comes with its unit, period and source; `30% growth` without a timeframe means nothing.",
            "Do not round up to sound better, and do not present an average without saying how spread the data is.",
            "When comparing two quantities, first check they are measured the same way; otherwise the comparison is false even if the arithmetic is right.",
            "If a number is central to the conclusion, state explicitly what would change if it were half as large.",
        ]),
    },
    {
        "ro": ("SURSE ȘI ATRIBUIRE", [
            "Nu cita o sursă pe care nu o poți numi. „Studiile arată” fără studiu este o afirmație fără acoperire.",
            "Când reproduci ideea altcuiva, spune a cui e; când o contrazici, prezintă-i mai întâi varianta cea mai tare.",
            "Distinge între ce e consens în domeniu, ce e opinie majoritară și ce e poziția ta.",
        ]),
        "en": ("SOURCES AND ATTRIBUTION", [
            "Do not cite a source you cannot name. `Studies show` without a study is an unbacked claim.",
            "When you reproduce someone's idea, say whose it is; when you contradict it, present its strongest form first.",
            "Distinguish between field consensus, majority opinion, and your own position.",
        ]),
    },
    {
        "ro": ("CONTRAARGUMENTUL", [
            "Înainte de a susține o poziție, formulează cel mai bun argument împotriva ei, în varianta lui cea mai puternică.",
            "Dacă acel contraargument nu poate fi respins, schimbă concluzia; nu îl slăbi ca să încapă.",
            "Un text care nu conține nicio obiecție reală e fie despre un subiect banal, fie incomplet.",
        ]),
        "en": ("THE COUNTER-ARGUMENT", [
            "Before defending a position, state the best argument against it, in its strongest form.",
            "If that counter-argument cannot be answered, change the conclusion; do not weaken it to fit.",
            "A text containing no real objection is either about something trivial or incomplete.",
        ]),
    },
    {
        "ro": ("CALIBRAREA TONULUI, CU EXEMPLE", [
            "Prea formal: „se recomandă implementarea unei soluții de monitorizare.” Nu se știe cine face ce.",
            "Prea familiar: „hai să băgăm un monitoring, e super simplu.” Pierde credibilitatea în fața unui cititor exigent.",
            "Potrivit: „adaugă monitorizare pe cele trei servicii critice; durează o zi și îți arată căderile înainte să le vadă clienții.”",
        ]),
        "en": ("TONE CALIBRATION, WITH EXAMPLES", [
            "Too formal: `it is recommended that a monitoring solution be implemented.` Nobody knows who does what.",
            "Too casual: `let's just throw in some monitoring, it's super easy.` It loses credibility with a demanding reader.",
            "Right: `add monitoring on the three critical services; it takes a day and shows you outages before customers do.`",
        ]),
    },
    {
        "ro": ("DISCIPLINA LUNGIMII", [
            "Lungimea rezultatului o dictează subiectul, nu spațiul disponibil. Dacă ideea se epuizează, oprește-te.",
            "Nu extinde o secțiune slabă ca să o echilibrezi cu una puternică; taie din cea puternică ce nu e necesar.",
            "Verifică raportul dintre afirmații și dovezi: dacă ai mai multe propoziții decât motive, ai scris prea mult.",
        ]),
        "en": ("LENGTH DISCIPLINE", [
            "The subject dictates the length, not the space available. If the idea runs out, stop.",
            "Do not pad a weak section to balance a strong one; instead cut what is unnecessary from the strong one.",
            "Check the ratio of claims to evidence: more sentences than reasons means you wrote too much.",
        ]),
    },
    {
        "ro": ("CONSECVENȚĂ INTERNĂ", [
            "Nicio afirmație din final nu poate contrazice una de la început; dacă ai schimbat părerea pe parcurs, rescrie începutul.",
            "Aceleași unități, aceleași denumiri, același nivel de precizie pe tot textul.",
            "Dacă folosești o schemă de clasificare, aplic-o până la capăt; o categorie rămasă în afara ei arată că schema e greșită.",
        ]),
        "en": ("INTERNAL CONSISTENCY", [
            "No statement at the end may contradict one at the start; if you changed your mind along the way, rewrite the start.",
            "Same units, same names, same precision throughout.",
            "If you use a classification scheme, apply it fully; one item left outside it shows the scheme is wrong.",
        ]),
    },
    {
        "ro": ("EXEMPLE ȘI ILUSTRĂRI", [
            "Fiecare idee abstractă primește un exemplu concret, cu detalii verificabile, nu un caz ipotetic vag.",
            "Exemplul vine după idee, nu în locul ei; un text făcut doar din exemple nu are teză.",
            "Preferă exemplul din contextul cititorului. Un exemplu din alt domeniu cere o traducere pe care el n-o va face.",
        ]),
        "en": ("EXAMPLES AND ILLUSTRATIONS", [
            "Every abstract idea gets a concrete example with checkable detail, not a vague hypothetical.",
            "The example comes after the idea, not instead of it; a text made only of examples has no thesis.",
            "Prefer an example from the reader's own context. One from another field needs a translation they will not do.",
        ]),
    },
    {
        "ro": ("CE NU INTRĂ ÎN REZULTAT", [
            "Fără istoricul gândirii tale, fără explicații despre cât de complexă e sarcina, fără scuze pentru limitări.",
            "Fără rezumat al cererii la început și fără ofertă de continuare la final.",
            "Fără avertismente generice care s-ar potrivi oricărui text pe orice temă.",
        ]),
        "en": ("WHAT DOES NOT GO IN THE RESULT", [
            "No history of your thinking, no explanation of how complex the task is, no apologies for limitations.",
            "No summary of the request at the start and no offer to continue at the end.",
            "No generic caveats that would fit any text on any subject.",
        ]),
    },
    {
        "ro": ("ACCESIBILITATE ȘI CLARITATE", [
            "Scrie astfel încât textul să fie înțeles și de cineva care citește într-o a doua limbă.",
            "Evită construcțiile în care negația se combină cu condiționalul; se citesc de două ori.",
            "Dacă folosești un tabel sau o listă, textul din jur trebuie să funcționeze și fără ele.",
        ]),
        "en": ("ACCESSIBILITY AND CLARITY", [
            "Write so the text is understandable by someone reading in a second language.",
            "Avoid constructions combining negation with the conditional; they get read twice.",
            "If you use a table or a list, the surrounding text must work without it.",
        ]),
    },
    {
        "ro": ("PRECIZIE ÎN FORMULARE", [
            "Înlocuiește „mai multe”, „semnificativ”, „rapid” cu valori sau cu comparații explicite.",
            "Evită verbele care nu spun cine acționează: „se va face”, „urmează să fie implementat”.",
            "Când o propoziție poate fi citită în două feluri, rescrie-o; nu te baza pe context să dezambiguizeze.",
        ]),
        "en": ("PRECISION IN WORDING", [
            "Replace `several`, `significant`, `fast` with values or explicit comparisons.",
            "Avoid verbs that hide the actor: `it will be done`, `is to be implemented`.",
            "When a sentence can be read two ways, rewrite it; do not rely on context to disambiguate.",
        ]),
    },
    {
        "ro": ("DACĂ REZULTATUL VA FI ITERAT", [
            "Structurează-l astfel încât o secțiune să poată fi înlocuită fără să afecteze restul.",
            "Marchează explicit ce e decizie asumată și ce e propunere deschisă discuției.",
            "Lasă la final o listă scurtă cu ce ai schimba primul, dacă ai mai avea o rundă.",
        ]),
        "en": ("IF THE RESULT WILL BE ITERATED", [
            "Structure it so one section can be replaced without affecting the rest.",
            "Explicitly mark what is a committed decision and what is a proposal open to discussion.",
            "Leave a short list at the end of what you would change first, given another round.",
        ]),
    },
    {
        "ro": ("ULTIMA TRECERE", [
            "Citește doar titlurile. Dacă din ele nu se înțelege argumentul, titlurile sunt greșite, nu cititorul.",
            "Citește doar prima propoziție a fiecărui paragraf. Ar trebui să formeze un rezumat coerent.",
            "Caută fiecare adjectiv și întreabă dacă adaugă informație. Cele care nu adaugă, ies.",
            "Verifică dacă ai răspuns cererii inițiale, cuvânt cu cuvânt, nu unei versiuni pe care ai reformulat-o tu.",
        ]),
        "en": ("THE LAST PASS", [
            "Read only the headings. If the argument is not clear from them, the headings are wrong, not the reader.",
            "Read only the first sentence of each paragraph. They should form a coherent summary.",
            "Find every adjective and ask whether it adds information. Those that do not, go.",
            "Check that you answered the original request word for word, not a version you reworded yourself.",
        ]),
    },
    {
        "ro": ("GRANIȚELE SARCINII", [
            "Rezolvi exact ce s-a cerut. Nu extinzi domeniul din proprie inițiativă și nu adaugi livrabile care nu au fost cerute.",
            "Dacă observi o problemă reală în afara cererii, o menționezi în două propoziții la final și continui cu ce ai de făcut.",
            "Nu restrânge sarcina fiindcă o parte e grea; dacă o parte e imposibilă, spui care și de ce, dar livrezi restul complet.",
        ]),
        "en": ("SCOPE BOUNDARIES", [
            "Solve exactly what was asked. Do not widen the scope on your own initiative or add deliverables nobody requested.",
            "If you spot a real problem outside the request, mention it in two sentences at the end and carry on.",
            "Do not narrow the task because part of it is hard; if part is impossible, say which and why, but deliver the rest in full.",
        ]),
    },
    {
        "ro": ("CERINȚE CARE SE CONTRAZIC", [
            "Dacă două cerințe nu pot fi respectate simultan, spune-o explicit în loc să alegi tăcut una dintre ele.",
            "Alege varianta care servește mai bine scopul declarat, aplic-o și explică alegerea într-un rând.",
            "Nu împăca cerințele contradictorii printr-un compromis care nu satisface niciuna.",
        ]),
        "en": ("REQUIREMENTS THAT CONFLICT", [
            "If two requirements cannot both be met, say so explicitly instead of silently picking one.",
            "Choose the one that better serves the stated goal, apply it, and explain the choice in one line.",
            "Do not reconcile contradictory requirements with a compromise that satisfies neither.",
        ]),
    },
    {
        "ro": ("INFORMAȚIA CARE LIPSEȘTE", [
            "Când lipsește un detaliu necesar, alege valoarea cea mai rezonabilă și marcheaz-o ca ipoteză, în loc să te oprești.",
            "Alege ipoteza care face rezultatul cel mai ușor de corectat, nu pe cea care îl face să sune mai bine.",
            "Dacă lipsa e atât de mare încât orice ipoteză ar face rezultatul inutil, spune asta în prima propoziție.",
        ]),
        "en": ("MISSING INFORMATION", [
            "When a needed detail is missing, pick the most reasonable value and flag it as an assumption instead of stopping.",
            "Choose the assumption that makes the result easiest to correct, not the one that makes it sound better.",
            "If the gap is so large that any assumption would make the result useless, say so in the first sentence.",
        ]),
    },
    {
        "ro": ("ORDINEA DE LUCRU", [
            "Întâi stabilește ce livrezi, apoi structura, apoi conținutul. Scrisul înainte de structură produce text care rătăcește.",
            "Rezolvă partea cea mai grea prima; dacă o lași la final, va fi cea mai slabă.",
            "Verifică la jumătate dacă ce ai scris până acolo răspunde cererii; e mai ieftin decât să descoperi la final.",
        ]),
        "en": ("ORDER OF WORK", [
            "First decide what you deliver, then the structure, then the content. Writing before structuring produces text that wanders.",
            "Solve the hardest part first; left for last, it will be the weakest.",
            "Halfway through, check that what you have answers the request; it is cheaper than discovering it at the end.",
        ]),
    },
    {
        "ro": ("CRITERII DE OPRIRE", [
            "Te oprești când fiecare întrebare din listă are răspuns și fiecare afirmație are acoperire — nu când ai atins o lungime.",
            "Dacă mai adaugi ceva și nu poți spune ce problemă rezolvă adăugarea, ai terminat deja.",
            "O ultimă tăiere e aproape întotdeauna o îmbunătățire; o ultimă adăugare, aproape niciodată.",
        ]),
        "en": ("STOPPING CRITERIA", [
            "You stop when every question on the list is answered and every claim is backed — not when you hit a length.",
            "If you add something and cannot say what problem the addition solves, you were already done.",
            "One last cut is almost always an improvement; one last addition, almost never.",
        ]),
    },
    {
        "ro": ("FORMA CONCRETĂ A LIVRABILULUI", [
            "Titlurile la același nivel au aceeași formă gramaticală; amestecul de substantive și verbe se observă imediat.",
            "Listele au elemente paralele ca lungime și ca structură; un element de cinci rânduri lângă unul de trei cuvinte arată neterminat.",
            "Nu folosi îngroșare pentru accent în interiorul frazelor; dacă ideea e importantă, mut-o la începutul propoziției.",
        ]),
        "en": ("THE CONCRETE SHAPE OF THE DELIVERABLE", [
            "Headings at the same level share a grammatical form; mixing nouns and verbs shows immediately.",
            "List items are parallel in length and structure; a five-line item next to a three-word one looks unfinished.",
            "Do not bold for emphasis inside sentences; if the idea matters, move it to the start of the sentence.",
        ]),
    },
    {
        "ro": ("CUM FOLOSEȘTI DETALIILE DIN CERERE", [
            "Fiecare detaliu concret din cerere apare în rezultat, folosit, nu doar citat.",
            "Dacă un detaliu pare irelevant, întreabă-te de ce a fost menționat înainte să îl ignori.",
            "Termenii pe care i-a folosit cel care a cerut se păstrează; nu-i înlocui cu sinonimele tale preferate.",
        ]),
        "en": ("HOW TO USE THE DETAILS IN THE REQUEST", [
            "Every concrete detail in the request appears in the result, used rather than merely quoted.",
            "If a detail seems irrelevant, ask why it was mentioned before ignoring it.",
            "Keep the terms the requester used; do not swap them for your preferred synonyms.",
        ]),
    },
    {
        "ro": ("VERIFICAREA FINALĂ A FAPTELOR", [
            "Fiecare nume propriu, dată, versiune și cifră se verifică separat, la sfârșit, în afara fluxului de scris.",
            "Ce nu poate fi verificat se marchează, se reformulează ca estimare sau se scoate.",
            "O afirmație pe care nu ai susține-o dacă cineva te-ar întreba „de unde știi?” nu are ce căuta în rezultat.",
        ]),
        "en": ("FINAL FACT CHECK", [
            "Every proper name, date, version and number is checked separately at the end, outside the writing flow.",
            "What cannot be verified is flagged, reworded as an estimate, or removed.",
            "A claim you would not defend if someone asked `how do you know?` does not belong in the result.",
        ]),
    },
    {
        "ro": ("TESTUL DE UTILITATE", [
            "Întreabă-te ce face cititorul concret după ce termină de citit. Dacă răspunsul e „nimic”, rezultatul nu e util, oricât ar fi de corect.",
            "Un rezultat util schimbă o decizie, deblochează o acțiune sau înlocuiește o căutare. Verifică pe care dintre cele trei îl faci.",
            "Dacă cititorul ar fi ajuns la aceeași concluzie în cinci minute de gândire proprie, adaugă ce el nu avea de unde ști.",
            "Compară rezultatul cu ce s-ar găsi într-o căutare simplă. Dacă nu îl bate, rescrie-l.",
        ]),
        "en": ("THE USEFULNESS TEST", [
            "Ask what the reader concretely does after finishing. If the answer is `nothing`, the result is not useful, however correct.",
            "A useful result changes a decision, unblocks an action, or replaces a search. Check which of the three you are doing.",
            "If the reader would have reached the same conclusion after five minutes of thought, add what they could not have known.",
            "Compare the result with what a simple search would return. If it does not beat that, rewrite it.",
        ]),
    },
    {
        "ro": ("PUBLICUL SECUNDAR", [
            "Pe lângă cititorul principal, rezultatul va ajunge la cineva care nu a cerut nimic și nu cunoaște contextul.",
            "Scrie astfel încât acel al doilea cititor să nu aibă nevoie de explicații verbale ca să înțeleagă despre ce e vorba.",
            "Evită referințele interne, prescurtările de echipă și glumele de context; peste o lună nici primul cititor nu le mai înțelege.",
            "Presupune că rezultatul va fi citit și peste șase luni, când nimeni nu-și mai amintește de ce a fost cerut.",
        ]),
        "en": ("THE SECONDARY AUDIENCE", [
            "Beyond the primary reader, the result will reach someone who asked for nothing and knows none of the context.",
            "Write so that second reader needs no verbal explanation to understand what this is about.",
            "Avoid internal references, team shorthand and in-jokes; in a month even the first reader will not get them.",
            "Assume the result will also be read six months later, when nobody remembers why it was requested.",
        ]),
    },
    {
        "ro": ("CE FACE REZULTATUL DIFERIT", [
            "Numește, măcar pentru tine, ce anume aduce rezultatul ăsta și nu s-ar fi găsit în primul răspuns evident.",
            "Dacă nu găsești nimic, mai lucrează la el; un răspuns corect dar previzibil e cea mai frecventă formă de eșec.",
            "Caută unghiul pe care majoritatea l-ar rata: o constrângere ignorată, un cost ascuns, o ipoteză nechestionată.",
            "Nu confunda originalitatea cu contrarianismul; unghiul bun rezistă la verificare, nu doar surprinde.",
        ]),
        "en": ("WHAT MAKES THIS RESULT DIFFERENT", [
            "Name, at least for yourself, what this result brings that the first obvious answer would not have.",
            "If you find nothing, keep working; a correct but predictable answer is the most common form of failure.",
            "Look for the angle most would miss: an ignored constraint, a hidden cost, an unquestioned assumption.",
            "Do not confuse originality with contrarianism; a good angle survives checking, not just surprises.",
        ]),
    },
]


def text_depth(lang: str) -> list[Section]:
    """Secțiunile de adâncime pentru prompturile de text, în ordinea utilității."""
    sections: list[Section] = []
    for index, entry in enumerate(_TEXT_DEPTH):
        title, lines = entry[lang]
        sections.append(
            Section(title, [lines[0]], priority=4, bullet="-",
                    droppable=True, min_lines=0, expansions=lines[1:])
        )
        del index
    return sections


# Rânduri adăugate la secțiunile care există deja, când bugetul permite.
EXTRA_QUALITY: dict[str, list[str]] = {
    "ro": [
        "nicio propoziție nu poate fi mutată în alt răspuns fără să se observe",
        "fiecare secțiune ar rezista dacă ar fi citită singură",
        "cifrele și denumirile au fost verificate, nu reproduse din memorie",
        "cititorul știe, la final, ce are de făcut mai departe",
    ],
    "en": [
        "no sentence could be moved into another answer without it showing",
        "each section would hold up if read on its own",
        "numbers and names were checked, not reproduced from memory",
        "by the end, the reader knows what to do next",
    ],
}

EXTRA_MUST: dict[str, list[str]] = {
    "ro": [
        "Păstrează terminologia și denumirile exacte din cerere; nu le înlocui cu variante pe care le consideri mai potrivite.",
        "Când o afirmație depinde de un context anume, spune de care; o regulă generală prezentată fără condiții e o eroare.",
        "Livrează rezultatul complet dintr-o singură dată, nu o schiță urmată de oferta de a o dezvolta.",
        "Dacă rezultatul conține pași, numerotează-i și fă fiecare pas verificabil: cineva trebuie să poată spune dacă l-a făcut sau nu.",
    ],
    "en": [
        "Keep the exact terminology and names from the request; do not replace them with variants you consider better.",
        "When a claim depends on a specific context, say which; a general rule stated without conditions is an error.",
        "Deliver the complete result in one go, not a sketch followed by an offer to expand it.",
        "If the result contains steps, number them and make each one checkable: someone must be able to say whether they did it.",
    ],
}

EXTRA_METHOD: dict[str, list[str]] = {
    "ro": [
        "Înainte de a scrie, decide ce NU intră în rezultat; lista asta te scutește de jumătate din reveniri.",
        "Scrie mai întâi partea despre care știi cel mai puțin; acolo vei descoperi ce îți lipsește.",
        "După ce ai terminat, recitește cererea inițială cuvânt cu cuvânt și bifează fiecare element al ei în rezultat.",
        "Dacă la recitire găsești o secțiune pe care ai sări-o ca cititor, rescrie-o sau scoate-o.",
    ],
    "en": [
        "Before writing, decide what does NOT go in the result; that list saves you half the revisions.",
        "Write the part you know least about first; that is where you will discover what is missing.",
        "When finished, reread the original request word by word and tick off each element in the result.",
        "If on rereading you find a section you would skip as a reader, rewrite it or cut it.",
    ],
}

EXTRA_AVOID: dict[str, list[str]] = {
    "ro": [
        "propoziții care încep prin a anunța ce urmează să spui",
        "prudență excesivă care lasă cititorul fără nicio direcție",
        "repetarea cererii cu alte cuvinte, în loc de răspuns",
        "formulări la pasiv acolo unde se știe cine face acțiunea",
    ],
    "en": [
        "sentences that begin by announcing what you are about to say",
        "excessive hedging that leaves the reader without direction",
        "restating the request in other words instead of answering it",
        "passive voice where the actor is known",
    ],
}


# ---------------------------------------------------------------------------
# Blocuri suplimentare pentru prompturile de imagine
# ---------------------------------------------------------------------------
#
# Corpul rămâne în engleză și în varianta românească: sunt descriptori vizuali,
# nu proză. Se traduce doar eticheta.

_IMAGE_DEPTH: list[tuple[str, str, list[str]]] = [
    ("FOREGROUND", "PRIM-PLAN", [
        "In the near plane, a partially defocused element frames the subject and gives the eye a place to enter the image.",
        "This foreground element is darker and lower in contrast than the subject, so it reads as depth rather than as competition.",
        "It occupies no more than a quarter of the frame and never crosses the subject's face, hands or product label.",
    ]),
    ("MIDGROUND", "PLAN MEDIAN", [
        "The mid-ground carries the subject and the information that supports it, rendered at the highest sharpness in the frame.",
        "Nothing in the mid-ground duplicates the subject's shape or tone; separation is achieved by value, not by outline.",
        "Supporting objects sit at a clearly different distance, so the depth reads as continuous rather than as flat cut-outs.",
    ]),
    ("BACKGROUND", "FUNDAL", [
        "The background falls away in both focus and contrast, described enough to place the scene but never detailed enough to read as a second subject.",
        "Background tones sit at least two stops from the subject's, so the silhouette stays legible at thumbnail size.",
        "No hard vertical or horizontal line passes directly behind the subject's head or through its centre of mass.",
    ]),
    ("MATERIALS AND SURFACES", "MATERIALE ȘI SUPRAFEȚE", [
        "Every material is specific and identifiable: brushed metal, raw linen, aged oak, lime plaster, fogged glass — never simply 'texture'.",
        "Surfaces respond to the stated light as real materials do: matte surfaces scatter, polished ones carry shaped speculars, fabric absorbs.",
        "Wear is where wear happens: at edges, handles, corners and contact points, not spread evenly as a decorative pattern.",
    ]),
    ("ATMOSPHERE", "ATMOSFERĂ", [
        "Air is visible: fine haze, suspended dust, humidity or smoke separates the depth planes and softens the far distance.",
        "Atmospheric density increases with distance, so the furthest plane is the lightest and lowest in contrast.",
        "Any particles in the air are lit by the same source as the subject and drift in one consistent direction.",
    ]),
    ("TIME AND SEASON", "MOMENT ȘI ANOTIMP", [
        "The time of day is legible from the light alone: colour temperature, shadow length and shadow direction all agree.",
        "Seasonal cues — foliage state, clothing weight, ground condition — are consistent with that light rather than decorative.",
        "If the scene is interior, the light arriving through openings matches the exterior hour implied everywhere else.",
    ]),
    ("SECONDARY LIGHT", "LUMINI SECUNDARE", [
        "Beyond the key light, practical sources within the scene motivate every other highlight: a window, a lamp, a screen, a reflection.",
        "Fill comes from a plausible bounce surface, so shadow areas keep colour and detail instead of going flat black.",
        "Each additional source is at least one stop below the key, so the lighting stays readable rather than becoming a wash.",
    ]),
    ("LENS CHARACTER", "CARACTERUL OBIECTIVULUI", [
        "Out-of-focus areas render with a specific bokeh character — smooth and circular, or slightly swirled at the edges — consistent with the stated aperture.",
        "Optical behaviour is subtle and physically plausible: gentle vignetting, a trace of chromatic fringing at high-contrast edges, no artificial glow.",
        "Depth of field falls off gradually from the plane of focus, with the transition matching the focal length that was named.",
    ]),
    ("POST-PROCESSING", "POSTPROCESARE", [
        "The grade is restrained: lifted shadows with a slight cool cast, highlights rolled off rather than clipped, mid-tones left honest.",
        "Grain is fine and even across the frame, present in the shadows as it would be on film, not overlaid as an effect.",
        "No local dodging that contradicts the light direction, and no clarity slider pushed until edges acquire a halo.",
    ]),
    ("EMOTIONAL BEAT", "NOTA EMOȚIONALĂ", [
        "The image carries one emotion and only one; it is produced by light, posture and framing, never by an added effect or filter.",
        "A viewer should be able to name that emotion in a single word after looking for one second.",
        "Nothing in the frame contradicts that emotion — not a stray bright colour, not an incongruent expression in the background.",
    ]),
    ("ATTENTION FLOW", "TRASEUL PRIVIRII", [
        "The eye enters at the brightest or sharpest point, travels along the composition's leading line and rests on the subject.",
        "No competing bright spot sits near the frame edge, where it would pull the eye out of the image.",
        "If a person is in frame, their gaze direction points into the composition, not out of it.",
    ]),
    ("EDGE QUALITY", "CALITATEA MUCHIILOR", [
        "Edges vary deliberately: the subject's contour is crisp, the transitions inside soft, the background boundaries dissolved.",
        "There is no uniform sharpening halo; contrast at edges comes from the light, not from processing.",
        "Where the subject meets the background, tonal separation carries the edge — an outline is never drawn to force it.",
    ]),
    ("SCALE CUES", "REPERE DE SCARĂ", [
        "At least one element of known size establishes scale, so the viewer reads the subject's true dimensions without guessing.",
        "Relative sizes across the depth planes are geometrically consistent with the stated focal length.",
        "Perspective convergence is correct: parallel lines meet at a single plausible vanishing point, not at several.",
    ]),
    ("NEGATIVE SPACE", "SPAȚIU LIBER", [
        "Deliberate empty area balances the subject and gives the composition room to breathe; the frame is not filled edge to edge.",
        "That empty area is not featureless — it holds a gradient, a texture or a tonal shift that keeps it alive.",
        "The empty side is the side the subject faces or moves toward, so the space reads as intention rather than as an accident.",
    ]),
    ("FRAMING SAFETY", "MARJE DE SIGURANȚĂ", [
        "Essential content stays clear of the outer eight percent of the frame, so the image survives cropping to other formats.",
        "The composition still reads if cropped to a square and to a vertical, with the subject intact in both.",
        "Nothing critical sits where an interface, a caption bar or a logo would normally be overlaid.",
    ]),
    ("CONSISTENCY", "CONSECVENȚĂ", [
        "One light direction, one colour temperature logic and one rendering style govern the whole frame without exception.",
        "If this image belongs to a series, these choices are the ones that must repeat identically across the set.",
        "Any repeated element — a prop, a colour, a texture — appears the same way each time it occurs in the frame.",
    ]),
    ("SUBJECT DETAIL", "DETALIUL SUBIECTULUI", [
        "The subject is described down to the details a viewer would notice on second look: fastenings, seams, wear, small asymmetries.",
        "Anything held, worn or touched by the subject is fully resolved rather than suggested as a blur.",
        "Where the subject is a person, hands and eyes get the most rendering care, because they are where failure is most visible.",
    ]),
    ("CONTRAST STRUCTURE", "STRUCTURA CONTRASTULUI", [
        "The image has a clear tonal hierarchy: one brightest area, one deepest shadow, and a controlled mid-tone range between them.",
        "Highlights hold detail rather than clipping to pure white, and the deepest shadow occupies only a small part of the frame.",
        "Squinting at the image should still reveal the subject as a distinct shape against its surroundings.",
    ]),
    ("COLOUR DISCIPLINE", "DISCIPLINA CULORII", [
        "The palette is limited on purpose: two dominant hues, one accent, and neutrals carrying everything else.",
        "The accent colour appears once, on or near the subject, and nowhere else in the frame.",
        "Skin, food and natural materials keep believable hues; saturation is added to the surroundings, never to them.",
    ]),
    ("TEXTURE HIERARCHY", "IERARHIA TEXTURILOR", [
        "Texture is strongest on the subject and diminishes with distance, so detail itself becomes a depth cue.",
        "No two adjacent surfaces carry the same texture frequency; contrast between smooth and rough defines the forms.",
        "Fine texture appears where light rakes across a surface, not uniformly over everything in frame.",
    ]),
    ("MOTION AND STILLNESS", "MIȘCARE ȘI IMOBILITATE", [
        "If anything moves, the motion is deliberate and readable: a specific limb, a fabric edge, water, smoke — described as motion, not as blur.",
        "The shutter behaviour is consistent with that motion: a frozen instant or a controlled trail, not both at once.",
        "Everything not intended to move is completely still and sharp, so the movement reads as a choice.",
    ]),
    ("SPATIAL LOGIC", "LOGICA SPAȚIULUI", [
        "The viewer can tell where they are standing relative to the subject and how far away, from the perspective alone.",
        "Floor, walls and horizon meet at consistent angles; the camera height is implied by where the horizon crosses the subject.",
        "Objects rest on surfaces with visible contact shadows; nothing floats or intersects another object impossibly.",
    ]),
    ("WHAT MUST BE SHARP", "CE TREBUIE SĂ FIE CLAR", [
        "Name the plane that must be perfectly sharp and hold everything else to a softer standard: the eyes, the label, the leading edge.",
        "Sharpness falls away smoothly in both directions from that plane, never returning further back.",
        "If two elements compete for the focal plane, the one that carries the meaning wins and the other is allowed to soften.",
    ]),
    ("FINISHING", "FINISAJ", [
        "The final image looks captured rather than assembled: no compositing seams, no mismatched noise, no element lit differently from the rest.",
        "Any repetition in nature — leaves, bricks, crowd faces — varies as it does in reality, without visible tiling.",
        "At full size the image rewards inspection; at thumbnail size it still reads as one clear idea.",
    ]),
    ("WEATHER AND CONDITIONS", "VREME ȘI CONDIȚII", [
        "Weather is stated and visible in its consequences: wet stone darkens, wind shapes fabric and hair, cold tightens posture.",
        "The sky, if visible, agrees with the light on the subject in both direction and colour temperature.",
        "Ground condition matches recent weather: puddles after rain, dust in drought, tracks in snow.",
    ]),
    ("ERA AND PERIOD", "EPOCĂ ȘI PERIOADĂ", [
        "The period is legible from objects, clothing and technology, all belonging to the same decade without anachronism.",
        "The photographic era is consistent too: film stock character, lens rendering and colour response match the period implied.",
        "Nothing modern intrudes into a historical frame, and nothing dated intrudes into a contemporary one.",
    ]),
    ("WARDROBE AND STYLING", "COSTUM ȘI STILIZARE", [
        "Clothing is described by material, cut, condition and fit, not by category: worn indigo canvas, not simply a jacket.",
        "Garments hang and fold as their weight dictates; heavy fabric drapes, stiff fabric creases, knit stretches at the joints.",
        "Styling tells the subject's story without a caption: what they do, where they live, how much care they take.",
    ]),
    ("PROPS AND SET DRESSING", "RECUZITĂ", [
        "Every object in frame earns its place by saying something about the subject or the moment; nothing is filler.",
        "Objects show use: the handle is polished, the paper is creased, the cup has a ring beneath it.",
        "Arrangement looks lived in rather than composed, while still respecting the composition's balance.",
    ]),
    ("REFLECTIONS AND TRANSPARENCY", "REFLEXII ȘI TRANSPARENȚĂ", [
        "Reflective and transparent surfaces show what is actually around them, geometrically consistent with the camera position.",
        "Glass refracts and tints what passes through it; liquid bends the edges of whatever sits behind it.",
        "No reflection shows an object that could not be in that position, and none is left as a generic bright smear.",
    ]),
    ("SHADOW SHAPES", "FORMA UMBRELOR", [
        "Shadows are described as shapes, not as absence of light: their edge hardness, direction and length all follow the named source.",
        "Cast shadows fall across surfaces and take their contour from them, bending over edges and steps.",
        "Shadow areas keep colour from the fill light rather than collapsing into neutral grey.",
    ]),
    ("COMPOSITIONAL GEOMETRY", "GEOMETRIA COMPOZIȚIEI", [
        "The frame has an underlying geometry — thirds, a diagonal, a triangle, a spiral — and every major element sits on it.",
        "Horizontals are level and verticals are upright unless a tilt is deliberate and stated.",
        "Repeating shapes create rhythm across the frame instead of appearing at random intervals.",
    ]),
    ("IMPLIED STORY", "POVESTEA IMPLICITĂ", [
        "The image is a single moment from something longer: it implies what happened just before and what is about to happen.",
        "One unresolved detail invites the viewer to complete the story — an open door, an unfinished gesture, a second cup.",
        "The narrative stays open rather than illustrated; nothing in frame explains the moment away.",
    ]),
    ("COLOUR TEMPERATURE MIX", "AMESTEC DE TEMPERATURI", [
        "Where two light sources of different temperature meet, the transition is visible and intentional: warm key against cool ambient.",
        "White balance is set for the key light, so the secondary source keeps its colour cast instead of being neutralised.",
        "The temperature difference stays within about two thousand kelvin, beyond which the image reads as a processing error.",
    ]),
    ("CAMERA HEIGHT AND VIEWPOINT", "ÎNĂLȚIMEA CAMEREI", [
        "The camera height is stated in human terms — eye level, chest height, floor level, above the subject — and holds throughout.",
        "That height carries meaning: below the subject grants stature, above it grants vulnerability, level grants equality.",
        "The viewpoint is one a person could physically occupy, unless the image is deliberately impossible and says so.",
    ]),
    ("SUBJECT ISOLATION", "IZOLAREA SUBIECTULUI", [
        "The subject separates from its surroundings by at least two of: focus, tone, colour, and light direction.",
        "No background element touches the subject's outline in a way that merges the two shapes.",
        "If the background is busy, the separation is carried by light rather than by blur alone.",
    ]),
    ("RENDERING FIDELITY", "FIDELITATEA RANDĂRII", [
        "Physical accuracy over stylisation: light falls off with distance, surfaces obey their material, geometry stays consistent.",
        "Fine structures — hair, wire, fabric threads, foliage edges — resolve cleanly instead of dissolving into noise.",
        "Small text, if visible in frame, is either legible and correct or deliberately out of focus, never garbled.",
    ]),
    ("WHAT THE FRAME EXCLUDES", "CE RĂMÂNE ÎN AFARA CADRULUI", [
        "What is cropped out matters: the frame implies a world continuing past its edges rather than ending at them.",
        "Nothing essential is cut by an edge in a way that looks accidental; every crop is a decision.",
        "Elements entering from outside the frame do so with a clear direction and a plausible origin.",
    ]),
]


def image_depth(lang: str) -> list[Section]:
    """Blocurile de adâncime pentru prompturile de imagine."""
    sections: list[Section] = []
    for english, romanian, lines in _IMAGE_DEPTH:
        title = romanian if lang == "ro" else english
        sections.append(
            Section(title, [lines[0]], priority=4, droppable=True,
                    min_lines=0, expansions=lines[1:])
        )
    return sections


# ---------------------------------------------------------------------------
# Reguli de platformă
# ---------------------------------------------------------------------------

_PLATFORM_TITLE = {
    "ro": "REGULI DE PLATFORMĂ",
    "en": "PLATFORM RULES",
}

_PLATFORM_LEAD = {
    "ro": "Conținutul e pentru {label}. Regulile ei nu sunt sugestii:",
    "en": "The content is for {label}. Its rules are not suggestions:",
}


def platform_section(platform: str, mode: str, lang: str) -> Section | None:
    """Regulile concrete ale platformei, ca secțiune de prompt."""
    entry = PLATFORMS.get(platform)
    if entry is None:
        return None

    by_language = entry.rules.get(mode) or entry.rules.get("text") or {}
    rules = by_language.get(lang) or by_language.get("ro") or []
    if not rules:
        return None

    lines = list(rules)
    limit = entry.limits.get(lang)
    if limit:
        lines.append(limit)

    return Section(
        _PLATFORM_TITLE[lang],
        [lines[0]],
        priority=1,
        bullet="-",
        droppable=True,
        min_lines=1,
        lead=_PLATFORM_LEAD[lang].format(label=entry.display(lang)),
        expansions=lines[1:],
    )
