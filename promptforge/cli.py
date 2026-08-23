"""Interfața de linie de comandă."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, feedback, generate_many, presets
from .catalog import MODELS, PLATFORMS, PRICING_DISCLAIMER, SIZES, parse_size
from .models import (
    Brief,
    DEFAULT_MAX_WORDS,
    DEFAULT_MIN_WORDS,
    GeneratedPrompt,
    MODE_IMAGE,
    MODE_TEXT,
    MODE_VIDEO,
)
from .targets import IMAGE_TARGETS, TEXT_TARGETS, VIDEO_TARGETS
from .vocab import IMAGE_DOMAINS, TEXT_DOMAINS, TONES, VIDEO_DOMAINS
from . import history as history_store

RULE = "─" * 72


def _add_common(parser: argparse.ArgumentParser, mode: str) -> None:
    parser.add_argument("idea", nargs="+", help="ideea pe care vrei să o transformi în prompt")
    parser.add_argument("--domain", help="forțează domeniul (vezi comanda `liste`)")
    parser.add_argument("--target", help="modelul-țintă (vezi comanda `liste`)")
    parser.add_argument("--must", action="append", default=[], metavar="CERINȚĂ",
                        help="cerință obligatorie suplimentară (se poate repeta)")
    parser.add_argument("--avoid", action="append", default=[], metavar="INTERDICȚIE",
                        help="ce trebuie evitat (se poate repeta)")
    parser.add_argument("--seed", type=int, default=0, help="seed pentru reproductibilitate")
    parser.add_argument("--variants", type=int, default=1, help="câte variante să genereze")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--refine", action="store_true",
                        help="rescrie promptul cu un model Claude (necesită credențiale)")
    parser.add_argument("--model", default=None, help="modelul folosit la --refine")
    parser.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--out", type=Path, help="scrie rezultatul într-un fișier")
    parser.add_argument("--json", action="store_true", dest="as_json", help="ieșire JSON")
    parser.add_argument("--no-save", action="store_true", help="nu salva în istoric")
    parser.add_argument("--preset", help="profil salvat cu `promptforge preset salveaza`")
    parser.add_argument("--platform", choices=sorted(PLATFORMS),
                        help="rețeaua sau produsul pentru care e conținutul")
    parser.add_argument("--size", help="dimensiune în pixeli („1080x1920”) sau nume "
                                       f"({', '.join(sorted(SIZES))})")

    if mode == MODE_VIDEO:
        parser.add_argument("--duration", type=int, default=0,
                            help="durata clipului în secunde (implicit 8)")
        parser.add_argument("--style", help="aspect vizual impus")
        parser.add_argument("--aspect", help="raport de aspect")
        parser.add_argument("--subject", help="subiectul formulat în engleză")
        parser.add_argument("--lang", default=None, choices=["ro", "en"])
    elif mode == MODE_TEXT:
        parser.add_argument("--audience", help="pentru cine este textul")
        parser.add_argument("--tone", help=f"ton ({', '.join(sorted(TONES))}) sau o descriere liberă")
        parser.add_argument("--lang", default="ro", choices=["ro", "en"],
                            help="limba promptului generat")
    else:
        parser.add_argument("--style", help="stil vizual impus (altfel e ales automat)")
        parser.add_argument("--aspect", help="raport de aspect, ex. 16:9")
        parser.add_argument("--subject", help="subiectul formulat în engleză, dacă ideea e în română")
        parser.add_argument("--lang", default=None, choices=["ro", "en"],
                            help="limba promptului (implicit engleză, cum preferă modelele de imagine)")


def _brief_from_args(args: argparse.Namespace, mode: str) -> Brief:
    options: dict = {
        "domain": args.domain,
        "target": args.target,
        "audience": getattr(args, "audience", None),
        "tone": getattr(args, "tone", None),
        "style": getattr(args, "style", None),
        "aspect": getattr(args, "aspect", None),
        "platform": args.platform,
        "must": args.must,
        "avoid": args.avoid,
        "lang": getattr(args, "lang", None),
        "seed": args.seed,
        "duration": getattr(args, "duration", 0),
    }
    # Limitele de cuvinte se trimit doar dacă au fost schimbate, ca profilul să
    # poată fixa altele fără să fie suprascris de valorile implicite.
    if args.min_words != DEFAULT_MIN_WORDS:
        options["min_words"] = args.min_words
    if args.max_words != DEFAULT_MAX_WORDS:
        options["max_words"] = args.max_words

    if args.size:
        width, height = parse_size(args.size)
        options["width"], options["height"] = width, height

    if args.preset:
        options = presets.apply(args.preset, options)

    options.setdefault("min_words", DEFAULT_MIN_WORDS)
    options.setdefault("max_words", DEFAULT_MAX_WORDS)
    options.pop("mode", None)

    subject = getattr(args, "subject", None)
    idea = " ".join(args.idea)

    # O corecție dată cu --subject e o traducere pe care merită să o reținem.
    if subject and mode in (MODE_IMAGE, MODE_VIDEO):
        from .image_engine import looks_romanian
        from .translate import learn

        if looks_romanian(idea):
            learn(idea, subject)

    return Brief(idea=idea, mode=mode, subject=subject, **options)


def _render_result(result: GeneratedPrompt, total: int) -> str:
    header = f"VARIANTA {result.variant}/{total}" if total > 1 else "PROMPT"
    meta = (
        f"mod: {result.mode} | domeniu: {result.domain} | țintă: {result.target} "
        f"| cuvinte: {result.word_count}"
    )
    if result.refined_by:
        meta += f" | rafinat de: {result.refined_by}"

    parts = [RULE, f"{header}   ({meta})", RULE, "", result.prompt]
    if result.negative_prompt:
        parts += ["", "NEGATIVE PROMPT", result.negative_prompt]
    if result.parameters:
        parts += ["", "PARAMETRI", result.parameters]
    if result.notes:
        parts += ["", "OBSERVAȚII"] + [f"  • {note}" for note in result.notes]
    return "\n".join(parts)


def _run_generation(args: argparse.Namespace, mode: str) -> int:
    try:
        brief = _brief_from_args(args, mode)
    except ValueError as exc:
        print(f"Eroare: {exc}", file=sys.stderr)
        return 2

    try:
        results = generate_many(brief, max(1, args.variants))
    except ValueError as exc:
        print(f"Eroare: {exc}", file=sys.stderr)
        return 2

    warnings: list[str] = []
    if args.refine:
        from .refine import DEFAULT_MODEL, RefineUnavailable, refine

        model = args.model or DEFAULT_MODEL
        refined: list[GeneratedPrompt] = []
        for result in results:
            try:
                refined.append(refine(brief, result, model=model, effort=args.effort))
            except RefineUnavailable as exc:
                warnings.append(f"Rafinarea a eșuat, folosesc promptul local: {exc}")
                refined.append(result)
        results = refined

    if args.as_json:
        payload = json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)
        output = payload
    else:
        output = "\n\n".join(_render_result(r, len(results)) for r in results)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
        print(f"Scris în {args.out}")
    else:
        print(output)

    for warning in warnings:
        print(f"\nAtenție: {warning}", file=sys.stderr)

    if not args.no_save:
        for result in results:
            history_store.save(brief, result)

    return 0


def _add_source_options(parser: argparse.ArgumentParser) -> None:
    """Opțiunile comune comenzilor care pornesc de la poze sau linkuri."""
    parser.add_argument("--target", help="modelul-țintă")
    parser.add_argument("--mode", default=MODE_IMAGE, choices=[MODE_IMAGE, MODE_TEXT],
                        help="ce fel de prompt vrei pornind de la surse")
    parser.add_argument("--lang", default=None, choices=["ro", "en"])
    parser.add_argument("--must", action="append", default=[], metavar="CERINȚĂ")
    parser.add_argument("--avoid", action="append", default=[], metavar="INTERDICȚIE")
    parser.add_argument("--aspect", help="raport de aspect impus")
    parser.add_argument("--style", help="stil vizual impus")
    parser.add_argument("--variants", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--model", default=None, help="modelul care analizează imaginile")
    parser.add_argument("--effort", default="high",
                        choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--no-save", action="store_true")


def _run_from_sources(args: argparse.Namespace, sources: list[str], instruction: str) -> int:
    """Firul comun al comenzilor `vision` și `remix`."""
    from .llm import DEFAULT_MODEL, ModelUnavailable
    from .media import MediaError
    from .pipeline import from_sources
    from .vision import VisionError

    options = {
        "target": args.target,
        "lang": args.lang,
        "must": args.must,
        "avoid": args.avoid,
        "seed": args.seed,
        "min_words": args.min_words,
        "max_words": args.max_words,
    }
    if args.mode == MODE_IMAGE:
        options["aspect"] = args.aspect
        options["style"] = args.style

    try:
        brief, results = from_sources(
            sources,
            instruction,
            mode=args.mode,
            variants=max(1, args.variants),
            model=args.model or DEFAULT_MODEL,
            effort=args.effort,
            **options,
        )
    except MediaError as exc:
        print(f"Eroare la încărcarea surselor: {exc}", file=sys.stderr)
        return 2
    except ModelUnavailable as exc:
        print(
            f"Analiza imaginilor are nevoie de un model: {exc}\n"
            f"Instalează dependența cu: pip install \"promptforge[images]\"",
            file=sys.stderr,
        )
        return 3
    except (VisionError, ValueError) as exc:
        print(f"Eroare: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        output = json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)
    else:
        output = "\n\n".join(_render_result(r, len(results)) for r in results)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
        print(f"Scris în {args.out}")
    else:
        print(output)

    if not args.no_save:
        for result in results:
            history_store.save(brief, result)
    return 0


def _cmd_vision(args: argparse.Namespace) -> int:
    return _run_from_sources(args, args.sources, " ".join(args.instruct or []))


def _cmd_remix(args: argparse.Namespace) -> int:
    """Ia elemente dintr-o imagine și le pune în alta."""
    instruction = " ".join(args.take)
    source_label = f"imaginea {args.source}"
    target_label = f"imaginea {args.into}"
    if args.source == args.into:
        print("Sursa și destinația nu pot fi aceeași imagine.", file=sys.stderr)
        return 2
    if max(args.source, args.into) > len(args.sources):
        print(
            f"Ai dat {len(args.sources)} imagini, dar te referi la imaginea "
            f"{max(args.source, args.into)}.",
            file=sys.stderr,
        )
        return 2

    full = (
        f"Ia {instruction} din {source_label} și aplică-le peste subiectul și "
        f"conținutul din {target_label}. Rezultatul păstrează ce este în "
        f"{target_label}, dar preia {instruction} din {source_label}."
    )
    return _run_from_sources(args, args.sources, full)


def _cmd_ask(args: argparse.Namespace) -> int:
    """Mod interactiv: întrebări scurte, prompt la final."""
    print("PromptForge — mod interactiv. Enter pentru valoarea implicită.\n")
    idea = input("Ce vrei să obții? ").strip()
    if not idea:
        print("Fără idee nu pot genera nimic.", file=sys.stderr)
        return 2

    mode_answer = input("Prompt pentru [t]ext sau [i]magine? (t) ").strip().lower()
    mode = MODE_IMAGE if mode_answer.startswith("i") else MODE_TEXT

    targets = IMAGE_TARGETS if mode == MODE_IMAGE else TEXT_TARGETS
    print(f"Modele disponibile: {', '.join(sorted(targets))}")
    target = input("Model-țintă? (implicit) ").strip() or None

    extra: dict[str, object] = {}
    if mode == MODE_TEXT:
        extra["audience"] = input("Pentru cine e textul? (opțional) ").strip() or None
        extra["tone"] = input(f"Ton ({', '.join(sorted(TONES))})? (opțional) ").strip() or None
    else:
        extra["style"] = input("Stil vizual impus? (opțional) ").strip() or None
        extra["aspect"] = input("Raport de aspect? (automat) ").strip() or None

    must = input("Ceva ce trebuie neapărat inclus? (opțional) ").strip()
    avoid = input("Ceva de evitat? (opțional) ").strip()

    brief = Brief(
        idea=idea,
        mode=mode,
        target=target,
        must=[must] if must else [],
        avoid=[avoid] if avoid else [],
        **extra,  # type: ignore[arg-type]
    )
    result = generate_many(brief, 1)[0]
    print("\n" + _render_result(result, 1))
    history_store.save(brief, result)
    return 0


def _cmd_history(args: argparse.Namespace) -> int:
    entries = history_store.load(args.limit)
    if not entries:
        print("Istoricul este gol.")
        return 0
    for entry in entries:
        print(RULE)
        print(f"{entry['timestamp']} | {entry['mode']}/{entry['domain']} → {entry['target']} "
              f"| {entry['word_count']} cuvinte")
        print(f"Idee: {entry['idea']}")
        if args.full:
            print()
            print(entry["prompt"])
    return 0


def _cmd_lists(_: argparse.Namespace) -> int:
    print("DOMENII TEXT:")
    print("  " + ", ".join(sorted(TEXT_DOMAINS)))
    print("\nDOMENII IMAGINE:")
    print("  " + ", ".join(sorted(IMAGE_DOMAINS)))
    print("\nȚINTE TEXT:")
    for name, spec in sorted(TEXT_TARGETS.items()):
        print(f"  {name:<12} {spec['label']}")
    print("\nDOMENII VIDEO:")
    print("  " + ", ".join(sorted(VIDEO_DOMAINS)))
    print("\nȚINTE IMAGINE:")
    for name, spec in sorted(IMAGE_TARGETS.items()):
        print(f"  {name:<12} {spec['label']}")
    print("\nȚINTE VIDEO:")
    for name, spec in sorted(VIDEO_TARGETS.items()):
        print(f"  {name:<12} {spec['label']}")
    print("\nPLATFORME:")
    print("  " + ", ".join(sorted(PLATFORMS)))
    print("\nTONURI:")
    print("  " + ", ".join(sorted(TONES)))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from .web import serve

    serve(host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def _cmd_models(args: argparse.Namespace) -> int:
    """Modelele-țintă disponibile, cu eticheta de preț."""
    kinds = [args.kind] if args.kind else ["text", "image", "video"]
    titles = {"text": "TEXT", "image": "IMAGINE", "video": "VIDEO"}

    for kind in kinds:
        print(f"\n{titles[kind]}")
        print("─" * 72)
        for model in [m for m in MODELS.values() if m.kind == kind]:
            print(f"  {model.key:<16} {model.label:<28} [{model.pricing}]")
            print(f"  {'':<16} {model.pricing_note}")
            if model.note:
                print(f"  {'':<16} {model.note}")
            print()
    print(PRICING_DISCLAIMER)
    return 0


def _cmd_preset(args: argparse.Namespace) -> int:
    if args.action == "lista":
        saved = presets.all_presets()
        if not saved:
            print("Niciun profil salvat.")
            return 0
        for name, options in sorted(saved.items()):
            details = ", ".join(f"{k}={v}" for k, v in sorted(options.items()))
            print(f"{name}\n  {details}")
        return 0

    if not args.name:
        print("Comanda are nevoie de un nume de profil.", file=sys.stderr)
        return 2

    try:
        if args.action == "sterge":
            presets.delete(args.name)
            print(f"Profilul {args.name!r} a fost șters.")
            return 0

        options = {}
        for pair in args.set or []:
            if "=" not in pair:
                print(f"Aștept perechi cheie=valoare, am primit {pair!r}.", file=sys.stderr)
                return 2
            key, _, value = pair.partition("=")
            key = key.strip()
            if key in ("must", "avoid"):
                options.setdefault(key, []).append(value.strip())
            elif key in ("min_words", "max_words", "width", "height", "duration", "seed"):
                options[key] = int(value)
            else:
                options[key] = value.strip()
        saved = presets.save(args.name, options)
        print(f"Profilul {args.name!r} salvat: " + ", ".join(f"{k}={v}" for k, v in saved.items()))
        return 0
    except (presets.PresetError, ValueError) as exc:
        print(f"Eroare: {exc}", file=sys.stderr)
        return 2


def _cmd_feedback(args: argparse.Namespace, good: bool) -> int:
    """Notează ultimul prompt (sau unul din istoric) ca bun sau slab."""
    entries = history_store.load(limit=max(args.index, 1))
    if not entries:
        print("Istoricul e gol; nu am ce nota.", file=sys.stderr)
        return 2
    if args.index > len(entries):
        print(f"Am doar {len(entries)} intrări în istoric.", file=sys.stderr)
        return 2

    entry = entries[args.index - 1]
    descriptors = entry.get("used_descriptors") or []
    if not descriptors:
        print(
            "Intrarea aceea nu are descriptori salvați (a fost generată cu o "
            "versiune mai veche sau rafinată cu model).",
            file=sys.stderr,
        )
        return 2

    feedback.record(descriptors, good=good)
    verdict = "bun" if good else "slab"
    print(f"Notat ca {verdict}: {len(descriptors)} descriptori din „{entry['idea'][:60]}”.")
    return 0


def _cmd_preferences(args: argparse.Namespace) -> int:
    if args.reset:
        feedback.reset()
        print("Preferințele au fost șterse.")
        return 0
    rows = feedback.summary(limit=args.limit)
    if not rows:
        print("Nicio preferință încă. Folosește `promptforge bun` după un rezultat reușit.")
        return 0
    for descriptor, score in rows:
        mark = "+" if score > 0 else "−"
        print(f"{mark}{abs(score):<3} {descriptor[:90]}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    from .audit import audit as run_audit

    text = args.file.read_text(encoding="utf-8") if args.file else " ".join(args.prompt)
    try:
        result = run_audit(text, mode=args.mode)
    except ValueError as exc:
        print(f"Eroare: {exc}", file=sys.stderr)
        return 2

    print(RULE)
    print(f"AUDIT   {result.score}/100 — {result.verdict}   ({result.word_count} cuvinte)")
    print(RULE)
    if result.present:
        print("\nARE:")
        for label in result.present:
            print(f"  ✓ {label}")
    if result.missing:
        print("\nLIPSEȘTE:")
        for label, hint in result.missing:
            print(f"  ✗ {label}\n      {hint}")
    for note in result.notes:
        print(f"\n  • {note}")
    return 0


def _cmd_lexicon(args: argparse.Namespace) -> int:
    from .translate import forget, learn, learned

    if args.uita:
        print("Șters." if forget(args.uita) else "Nu aveam intrarea asta.")
        return 0
    if args.adauga:
        if "=" not in args.adauga:
            print("Aștept forma „română=engleză”.", file=sys.stderr)
            return 2
        romanian, _, english = args.adauga.partition("=")
        learn(romanian, english)
        print(f"Reținut: „{romanian.strip()}” → „{english.strip()}”.")
        return 0

    entries = learned()
    if not entries:
        print("Lexiconul învățat e gol. Se umple singur când corectezi cu --subject.")
        return 0
    for romanian, english in sorted(entries.items()):
        print(f"{romanian}  →  {english}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptforge",
        description="Generează prompturi detaliate (300-500 de cuvinte) pentru modele de text și de imagine.",
    )
    parser.add_argument("--version", action="version", version=f"PromptForge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    text_parser = sub.add_parser("text", help="prompt pentru un model de text")
    _add_common(text_parser, MODE_TEXT)
    text_parser.set_defaults(func=lambda a: _run_generation(a, MODE_TEXT))

    image_parser = sub.add_parser("image", help="prompt pentru un model de imagine")
    _add_common(image_parser, MODE_IMAGE)
    image_parser.set_defaults(func=lambda a: _run_generation(a, MODE_IMAGE))

    video_parser = sub.add_parser("video", help="prompt pentru un model video")
    _add_common(video_parser, MODE_VIDEO)
    video_parser.set_defaults(func=lambda a: _run_generation(a, MODE_VIDEO))

    models_parser = sub.add_parser("modele", help="modelele disponibile și dacă sunt gratis")
    models_parser.add_argument("--kind", choices=["text", "image", "video"])
    models_parser.set_defaults(func=_cmd_models)

    preset_parser = sub.add_parser("preset", help="profiluri de opțiuni salvate")
    preset_parser.add_argument("action", choices=["lista", "salveaza", "sterge"])
    preset_parser.add_argument("name", nargs="?")
    preset_parser.add_argument("--set", action="append", metavar="CHEIE=VALOARE",
                               help="opțiune de salvat (se poate repeta)")
    preset_parser.set_defaults(func=_cmd_preset)

    good_parser = sub.add_parser("bun", help="marchează ultimul prompt ca reușit")
    good_parser.add_argument("--index", type=int, default=1,
                             help="al câtelea din istoric (1 = ultimul)")
    good_parser.set_defaults(func=lambda a: _cmd_feedback(a, good=True))

    bad_parser = sub.add_parser("slab", help="marchează ultimul prompt ca nereușit")
    bad_parser.add_argument("--index", type=int, default=1)
    bad_parser.set_defaults(func=lambda a: _cmd_feedback(a, good=False))

    prefs_parser = sub.add_parser("preferinte", help="ce a învățat din feedback-ul tău")
    prefs_parser.add_argument("--limit", type=int, default=20)
    prefs_parser.add_argument("--reset", action="store_true")
    prefs_parser.set_defaults(func=_cmd_preferences)

    audit_parser = sub.add_parser("audit", help="verifică un prompt existent")
    audit_parser.add_argument("prompt", nargs="*", help="promptul de verificat")
    audit_parser.add_argument("--file", type=Path, help="citește promptul dintr-un fișier")
    audit_parser.add_argument("--mode", default=MODE_TEXT,
                              choices=[MODE_TEXT, MODE_IMAGE, MODE_VIDEO])
    audit_parser.set_defaults(func=_cmd_audit)

    lexicon_parser = sub.add_parser("lexicon", help="traducerile pe care le-a învățat")
    lexicon_parser.add_argument("--adauga", metavar="RO=EN")
    lexicon_parser.add_argument("--uita", metavar="RO")
    lexicon_parser.set_defaults(func=_cmd_lexicon)

    vision_parser = sub.add_parser(
        "vision", help="prompt pornind de la poze sau linkuri")
    vision_parser.add_argument("sources", nargs="+",
                               help="fișiere imagine, adrese de imagine sau pagini web")
    vision_parser.add_argument("--instruct", nargs="+", default=[],
                               help="ce vrei să obții din surse")
    _add_source_options(vision_parser)
    vision_parser.set_defaults(func=_cmd_vision)

    remix_parser = sub.add_parser(
        "remix", help="ia elemente dintr-o poză și le pune în alta")
    remix_parser.add_argument("sources", nargs="+", help="cel puțin două imagini")
    remix_parser.add_argument("--take", nargs="+", required=True,
                              metavar="ELEMENT",
                              help="ce preiei, ex: lumina si paleta")
    remix_parser.add_argument("--source", type=int, default=1,
                              help="din a câta imagine preiei (implicit 1)")
    remix_parser.add_argument("--into", type=int, default=2,
                              help="în a câta imagine pui (implicit 2)")
    _add_source_options(remix_parser)
    remix_parser.set_defaults(func=_cmd_remix)

    ask_parser = sub.add_parser("ask", help="mod interactiv, cu întrebări")
    ask_parser.set_defaults(func=_cmd_ask)

    hist_parser = sub.add_parser("istoric", help="prompturile generate anterior")
    hist_parser.add_argument("--limit", type=int, default=10)
    hist_parser.add_argument("--full", action="store_true", help="afișează și textul complet")
    hist_parser.set_defaults(func=_cmd_history)

    list_parser = sub.add_parser("liste", help="domeniile, țintele și tonurile disponibile")
    list_parser.set_defaults(func=_cmd_lists)

    serve_parser = sub.add_parser("serve", help="interfață web locală")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--no-browser", action="store_true")
    serve_parser.set_defaults(func=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nÎntrerupt.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
