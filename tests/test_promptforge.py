"""Teste pentru PromptForge. Rulează cu: python -m unittest discover tests"""

from __future__ import annotations

import base64
import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from promptforge import Brief, feedback, generate, generate_many, presets
from promptforge.assembly import count_words, fit, range_note, sentence
from promptforge.cli import main
from promptforge.detect import detect_domain, keywords_of
from promptforge.history import load, save
from promptforge.image_engine import looks_romanian
from promptforge.audit import audit as run_audit
from promptforge.catalog import (
    FREE,
    FREEMIUM,
    MODELS,
    PAID,
    PLATFORMS,
    aspect_of,
    parse_size,
)
from promptforge.media import ImageRef, MediaError, load_image, read_dimensions
from promptforge.models import Section
from promptforge.pipeline import from_sources
from promptforge.translate import forget, learn, learned, to_english
from promptforge.vision import VisionError, analyze_images
from promptforge.web import _decode_uploads
from promptforge.targets import IMAGE_TARGETS, TEXT_TARGETS, VIDEO_TARGETS
from promptforge.vocab import IMAGE_DOMAINS, TEXT_DOMAINS


class TestBrief(unittest.TestCase):
    def test_refuza_ideea_goala(self):
        with self.assertRaises(ValueError):
            Brief(idea="   ")

    def test_refuza_mod_necunoscut(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", mode="audio")

    def test_accepta_modul_video(self):
        self.assertEqual(Brief(idea="ceva", mode="video").lang, "en")

    def test_refuza_limite_inversate(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", min_words=400, max_words=300)

    def test_normalizeaza_spatiile(self):
        self.assertEqual(Brief(idea="  a   b  ").idea, "a b")


class TestDetectie(unittest.TestCase):
    def test_domeniu_text_din_cuvinte_cheie(self):
        self.assertEqual(detect_domain("scrie un script python", "text"), "cod")
        self.assertEqual(detect_domain("un email catre client", "text"), "email")
        self.assertEqual(detect_domain("o poveste despre un far", "text"), "naratiune")

    def test_domeniu_imagine_din_cuvinte_cheie(self):
        self.assertEqual(detect_domain("un portret in lumina de seara", "image"), "portret")
        self.assertEqual(detect_domain("peisaj cu munti", "image"), "peisaj")

    def test_subiecte_in_engleza_sunt_recunoscute(self):
        cases = {
            "an old fisherman mending nets on a pier": "portret",
            "a mountain landscape at sunrise": "peisaj",
            "a luxury perfume bottle on marble": "produs",
            "brutalist building facade at dusk": "arhitectura",
            "a plate of homemade pasta": "mancare",
            "a floating city, concept art": "concept-art",
            "watercolour illustration of a fox": "ilustratie",
            "a cozy living room with morning light": "interior",
        }
        for idea, expected in cases.items():
            with self.subTest(idea=idea):
                self.assertEqual(detect_domain(idea, "image"), expected)

    def test_fara_potrivire_da_general(self):
        self.assertEqual(detect_domain("qwerty zxcvb", "text"), "general")

    def test_diacriticele_nu_impiedica_potrivirea(self):
        self.assertEqual(detect_domain("o analiză de piață", "text"), "analiza")

    def test_potrivirea_e_pe_cuvant_intreg(self):
        # „codru” nu trebuie să declanșeze domeniul „cod”
        self.assertNotEqual(detect_domain("un codru des si intunecat", "text"), "cod")

    def test_cuvintele_de_umplutura_sunt_ignorate(self):
        found = keywords_of("o aplicatie care imi arata unde pierd bani")
        self.assertNotIn("arata", found)
        self.assertNotIn("unde", found)
        self.assertIn("aplicatie", found)


class TestIncadrareCuvinte(unittest.TestCase):
    def test_numara_ignorand_marcajele(self):
        self.assertEqual(count_words("## Titlu\n- unu\n- doi"), 3)

    def test_completeaza_din_rezerva(self):
        base = [Section("A", ["unu doi trei"])]
        reserve = [Section("B", ["patru cinci sase sapte opt noua zece"])]
        chosen, text = fit(base, min_words=8, max_words=50, reserve=reserve)
        self.assertEqual(len(chosen), 2)

    def test_nu_coboara_sub_podeaua_de_randuri(self):
        section = Section("A", [f"rand numarul {i}" for i in range(10)],
                          bullet="-", droppable=True, min_lines=4)
        chosen, _ = fit([section], min_words=1, max_words=12)
        self.assertGreaterEqual(len(chosen[0].lines), 4)

    def test_elimina_sectiunile_care_pot_lipsi(self):
        keep = Section("KEEP", ["unu doi trei patru cinci"])
        drop = Section("DROP", ["sase sapte opt noua zece"], droppable=True, min_lines=0)
        chosen, _ = fit([keep, drop], min_words=1, max_words=6)
        self.assertEqual([s.title for s in chosen], ["KEEP"])

    def test_randul_introductiv_supravietuieste_taierii(self):
        section = Section("A", ["unu", "doi", "trei"], bullet="-",
                          droppable=True, min_lines=1, lead="Verifică:")
        _, text = fit([section], min_words=1, max_words=4)
        self.assertIn("Verifică:", text)

    def test_masoara_redarea_reala(self):
        # Un renderer care adaugă text trebuie luat în calcul la numărare.
        section = Section("A", ["unu doi trei"])
        _, text = fit(
            [section], min_words=1, max_words=100,
            renderer=lambda secs: "prefix " + " ".join(l for s in secs for l in s.lines),
        )
        self.assertTrue(text.startswith("prefix"))

    def test_sentence_normalizeaza(self):
        self.assertEqual(sentence("un text fara punct"), "Un text fara punct.")
        self.assertEqual(sentence("Deja corect."), "Deja corect.")
        self.assertEqual(sentence("  "), "")

    def test_range_note(self):
        self.assertIsNone(range_note(400, 300, 500))
        self.assertIn("peste limita", range_note(600, 300, 500))
        self.assertIn("sub minimul", range_note(100, 300, 500))


class TestGenerareText(unittest.TestCase):
    def test_respecta_intervalul_pe_toate_tintele(self):
        for target in TEXT_TARGETS:
            for lang in ("ro", "en"):
                with self.subTest(target=target, lang=lang):
                    result = generate(Brief(
                        idea="o aplicatie care imi urmareste cheltuielile lunare",
                        mode="text", target=target, lang=lang,
                    ))
                    self.assertGreaterEqual(result.word_count, 300)
                    self.assertLessEqual(result.word_count, 500)

    def test_toate_domeniile_produc_prompt_valid(self):
        for domain in TEXT_DOMAINS:
            with self.subTest(domain=domain):
                result = generate(Brief(idea="o cerere de test", mode="text", domain=domain))
                self.assertEqual(result.domain, domain)
                self.assertGreaterEqual(result.word_count, 300)
                self.assertLessEqual(result.word_count, 500)

    def test_ideea_apare_in_prompt(self):
        idea = "un generator de facturi pentru freelanceri"
        result = generate(Brief(idea=idea, mode="text"))
        self.assertIn(idea, result.prompt)

    def test_cerintele_si_interdictiile_utilizatorului_ajung_in_prompt(self):
        result = generate(Brief(
            idea="o pagina de prezentare",
            mode="text",
            must=["include un tabel de preturi"],
            avoid=["limbaj corporatist"],
        ))
        self.assertIn("include un tabel de preturi", result.prompt)
        self.assertIn("limbaj corporatist", result.prompt)

    def test_cerintele_utilizatorului_supravietuiesc_scurtarii(self):
        # Cu o limită strânsă, secțiunile se taie — dar nu ce a cerut omul.
        result = generate(Brief(
            idea="o pagina de prezentare",
            mode="text",
            must=["include un tabel de preturi"],
            avoid=["limbaj corporatist"],
            min_words=150,
            max_words=260,
        ))
        self.assertIn("include un tabel de preturi", result.prompt)
        self.assertIn("limbaj corporatist", result.prompt)

    def test_tinta_claude_foloseste_etichete(self):
        result = generate(Brief(idea="o cerere oarecare", mode="text", target="claude"))
        self.assertIn("<rol>", result.prompt)
        self.assertIn("</rol>", result.prompt)

    def test_tinta_gpt_foloseste_markdown(self):
        result = generate(Brief(idea="o cerere oarecare", mode="text", target="gpt"))
        self.assertIn("## ROL", result.prompt)

    def test_limba_engleza_schimba_titlurile(self):
        result = generate(Brief(idea="a request", mode="text", target="gpt", lang="en"))
        self.assertIn("## ROLE", result.prompt)
        self.assertNotIn("## ROL\n", result.prompt)

    def test_ton_liber_este_preluat(self):
        result = generate(Brief(idea="o cerere", mode="text", tone="sarcastic dar politicos"))
        self.assertIn("sarcastic dar politicos", result.prompt)

    def test_tinta_necunoscuta_da_eroare(self):
        with self.assertRaises(ValueError):
            generate(Brief(idea="o cerere", mode="text", target="inexistent"))


class TestGenerareImagine(unittest.TestCase):
    def test_respecta_intervalul_pe_toate_tintele(self):
        for target in IMAGE_TARGETS:
            with self.subTest(target=target):
                result = generate(Brief(
                    idea="a portrait of an old woman by the window",
                    mode="image", target=target,
                ))
                self.assertGreaterEqual(result.word_count, 300)
                self.assertLessEqual(result.word_count, 500)

    def test_toate_domeniile_produc_prompt_valid(self):
        for domain in IMAGE_DOMAINS:
            with self.subTest(domain=domain):
                result = generate(Brief(idea="a test subject", mode="image", domain=domain))
                self.assertGreaterEqual(result.word_count, 300)
                self.assertLessEqual(result.word_count, 500)

    def test_flux_primeste_prompt_negativ(self):
        result = generate(Brief(idea="a product shot", mode="image", target="flux"))
        self.assertTrue(result.negative_prompt)

    def test_dalle_nu_primeste_prompt_negativ(self):
        result = generate(Brief(idea="a product shot", mode="image", target="dalle"))
        self.assertEqual(result.negative_prompt, "")
        self.assertIn("stated positively", result.prompt)

    def test_midjourney_este_paragraf_cu_parametri(self):
        result = generate(Brief(idea="a product shot", mode="image", target="midjourney"))
        self.assertNotIn("\n\n", result.prompt)
        self.assertIn("--ar", result.parameters)
        self.assertIn("--no", result.parameters)

    def test_interdictiile_utilizatorului_supravietuiesc_scurtarii_midjourney(self):
        result = generate(Brief(
            idea="a product shot", mode="image", target="midjourney",
            avoid=["neon lighting"],
        ))
        self.assertIn("neon lighting", result.parameters)

    def test_aspectul_implicit_depinde_de_domeniu(self):
        portrait = generate(Brief(idea="a portrait of a man", mode="image", target="flux"))
        self.assertIn("4:5", portrait.parameters)
        landscape = generate(Brief(idea="a mountain landscape", mode="image", target="flux"))
        self.assertIn("16:9", landscape.parameters)

    def test_aspectul_impus_are_prioritate(self):
        result = generate(Brief(idea="a portrait", mode="image", target="flux", aspect="21:9"))
        self.assertIn("21:9", result.parameters)

    def test_subiectul_romanesc_este_tradus(self):
        result = generate(Brief(idea="un pescar batran pe un chei de piatra", mode="image"))
        self.assertIn("old fisherman on a stone pier", result.prompt)
        self.assertTrue(any("tradus automat" in note for note in result.notes))

    def test_subiectul_netradus_este_semnalat(self):
        result = generate(Brief(idea="un dispozitiv ciudat cu manete si zgomote", mode="image"))
        self.assertTrue(any("rămas în română" in note for note in result.notes))

    def test_subiectul_in_engleza_inlatura_avertismentul(self):
        result = generate(Brief(
            idea="un portret cu o femeie la fereastra",
            mode="image",
            subject="a portrait of a woman by a window",
        ))
        self.assertFalse(any("română" in note for note in result.notes))
        # Subiectul primește majusculă de început, dar rămâne neschimbat în rest.
        self.assertIn("portrait of a woman by a window", result.prompt)

    def test_stilul_impus_apare_in_prompt(self):
        result = generate(Brief(idea="a cat", mode="image", style="1950s technicolor film still"))
        self.assertIn("1950s technicolor film still", result.prompt)

    def test_looks_romanian(self):
        self.assertTrue(looks_romanian("un câine în parc"))
        self.assertTrue(looks_romanian("o casa cu o gradina"))
        self.assertFalse(looks_romanian("a dog in the park"))


class TestVariante(unittest.TestCase):
    def test_acelasi_seed_da_acelasi_rezultat(self):
        brief = Brief(idea="a portrait of a chef", mode="image", seed=7)
        self.assertEqual(generate(brief).prompt, generate(brief).prompt)

    def test_variantele_difera(self):
        brief = Brief(idea="a portrait of a chef", mode="image")
        prompts = {result.prompt for result in generate_many(brief, 3)}
        self.assertEqual(len(prompts), 3)

    def test_seed_diferit_da_rezultat_diferit(self):
        a = generate(Brief(idea="a portrait of a chef", mode="image", seed=1))
        b = generate(Brief(idea="a portrait of a chef", mode="image", seed=99))
        self.assertNotEqual(a.prompt, b.prompt)

    def test_numar_invalid_de_variante(self):
        with self.assertRaises(ValueError):
            generate_many(Brief(idea="ceva"), 0)


class TestIstoric(unittest.TestCase):
    def test_scrie_si_citeste(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            brief = Brief(idea="o idee de test", mode="text")
            save(brief, generate(brief), path=path)
            save(brief, generate(brief), path=path)
            entries = load(limit=10, path=path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["idea"], "o idee de test")

    def test_istoric_inexistent_da_lista_goala(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load(path=Path(tmp) / "lipsa.jsonl"), [])

    def test_o_linie_corupta_nu_strica_restul(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            path.write_text('{"idea": "buna"}\nnu-i json\n', encoding="utf-8")
            self.assertEqual(len(load(path=path)), 1)


class TestCLI(unittest.TestCase):
    def test_genereaza_in_fisier(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "prompt.txt"
            code = main(["text", "o", "idee", "de", "test", "--out", str(out), "--no-save"])
            self.assertEqual(code, 0)
            self.assertGreater(len(out.read_text(encoding="utf-8")), 500)

    def test_iesire_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "prompt.json"
            main(["image", "a", "red", "car", "--json", "--out", str(out), "--no-save"])
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["mode"], "image")

    def test_tinta_invalida_iese_cu_cod_de_eroare(self):
        code = main(["text", "o idee", "--target", "inexistent", "--no-save"])
        self.assertEqual(code, 2)

    def test_comanda_liste(self):
        self.assertEqual(main(["liste"]), 0)


class TestWebAPI(unittest.TestCase):
    def test_payload_valid(self):
        from promptforge.web import _page
        self.assertIn(b"PromptForge", _page())


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Traducere, surse vizuale și flux complet
# ---------------------------------------------------------------------------

class TestTraducere(unittest.TestCase):
    def test_fraze_uzuale(self):
        cases = {
            "un pescar batran pe un chei de piatra": "an old fisherman on a stone pier",
            "o femeie in varsta la fereastra": "an elderly woman by the window",
            "o pisica neagra pe un scaun de lemn": "a black cat on a wooden chair",
            "un pod de fier peste un rau": "an iron bridge over a river",
            "flori albe intr-un borcan de sticla": "white flowers in a glass jar",
        }
        for romanian, english in cases.items():
            with self.subTest(romanian=romanian):
                self.assertEqual(to_english(romanian)[0], english)

    def test_adjectivele_trec_inaintea_substantivului(self):
        self.assertEqual(to_english("o casa veche")[0], "an old house")

    def test_refuza_traducerea_cand_nu_recunoaste_destul(self):
        original = "un dispozitiv ciudat cu manete si zgomote"
        translated, coverage = to_english(original)
        self.assertEqual(translated, original)
        self.assertLess(coverage, 0.6)

    def test_prepozitia_bate_substantivul_omonim(self):
        # „peste” e prepoziție mult mai des decât „pește”.
        self.assertIn("over", to_english("un pod peste un rau")[0])

    def test_promptul_romanesc_isi_pastreaza_eticheta(self):
        result = generate(Brief(idea="un pescar batran", mode="image", lang="ro"))
        self.assertIn("SUBIECT", result.prompt)
        self.assertTrue(any("în română" in note for note in result.notes))


class TestMedia(unittest.TestCase):
    PNG = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQ"
        "DwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def test_incarca_fisier_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(self.PNG)
            ref = load_image(str(path), "imaginea 1")
            self.assertEqual(ref.media_type, "image/png")
            self.assertEqual(ref.to_block()["source"]["type"], "base64")

    def test_fisier_inexistent(self):
        with self.assertRaises(MediaError):
            load_image("/nu/exista/deloc.png")

    def test_format_nesuportat(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.txt"
            path.write_bytes(b"text simplu")
            with self.assertRaises(MediaError):
                load_image(str(path))

    def test_refuza_scheme_straine(self):
        with self.assertRaises(MediaError):
            load_image("ftp://exemplu.ro/a.png")

    def test_adresa_de_imagine_nu_se_descarca(self):
        ref = ImageRef(label="imaginea 1", origin="https://x/a.jpg", url="https://x/a.jpg")
        self.assertEqual(ref.to_block()["source"]["type"], "url")


class TestVision(unittest.TestCase):
    ANALYSIS = json.dumps({
        "domain": "portret",
        "subject": "an elderly fisherman mending a net",
        "environment": "a weathered stone pier at dawn",
        "lighting": "soft low-angle dawn light from camera-left",
        "palette": "muted slate blue and weathered oak",
        "aspect": "3:2",
        "negative": ["smooth skin", "plastic rope"],
        "transfer": "lumina din imaginea 1, subiectul din imaginea 2",
        "camp_inventat": "trebuie ignorat",
    })

    def _sender(self, response=None):
        captured = {}

        def send(*, system, content, model, effort):
            captured["content"] = content
            captured["model"] = model
            return response if response is not None else self.ANALYSIS

        return send, captured

    def test_extrage_campurile_cunoscute(self):
        send, _ = self._sender()
        images = [ImageRef(label="imaginea 1", origin="a.png", media_type="image/png", data="x")]
        fields = analyze_images(images, "descrie", sender=send)
        self.assertEqual(fields["domain"], "portret")
        self.assertEqual(fields["aspect"], "3:2")
        self.assertNotIn("camp_inventat", fields)

    def test_trimite_toate_imaginile(self):
        send, captured = self._sender()
        images = [
            ImageRef(label="imaginea 1", origin="a.png", media_type="image/png", data="x"),
            ImageRef(label="imaginea 2", origin="https://x/b.jpg", url="https://x/b.jpg"),
        ]
        analyze_images(images, "combina-le", sender=send)
        kinds = [block.get("type") for block in captured["content"]]
        self.assertEqual(kinds.count("image"), 2)

    def test_json_in_gard_de_cod(self):
        send, _ = self._sender(f"Iată:\n```json\n{self.ANALYSIS}\n```")
        images = [ImageRef(label="imaginea 1", origin="a.png", media_type="image/png", data="x")]
        self.assertIn("subject", analyze_images(images, sender=send))

    def test_raspuns_fara_json(self):
        send, _ = self._sender("nu am putut analiza")
        images = [ImageRef(label="imaginea 1", origin="a.png", media_type="image/png", data="x")]
        with self.assertRaises(VisionError):
            analyze_images(images, sender=send)

    def test_json_fara_campuri_utile(self):
        send, _ = self._sender('{"altceva": 1}')
        images = [ImageRef(label="imaginea 1", origin="a.png", media_type="image/png", data="x")]
        with self.assertRaises(VisionError):
            analyze_images(images, sender=send)

    def test_fara_imagini(self):
        with self.assertRaises(VisionError):
            analyze_images([], sender=lambda **kw: "{}")


class TestFluxDinSurse(unittest.TestCase):
    PNG = TestMedia.PNG

    def _two_images(self, tmp):
        first, second = Path(tmp) / "a.png", Path(tmp) / "b.png"
        first.write_bytes(self.PNG)
        second.write_bytes(self.PNG)
        return [str(first), str(second)]

    def test_analiza_ajunge_in_prompt(self):
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            brief, results = from_sources(
                self._two_images(tmp),
                "ia lumina din imaginea 1 si pune-o peste subiectul din imaginea 2",
                target="flux", sender=send,
            )
        result = results[0]
        self.assertIn("elderly fisherman mending a net", result.prompt)
        self.assertIn("weathered stone pier", result.prompt)
        self.assertIn("3:2", result.parameters)
        self.assertEqual(result.domain, "portret")
        self.assertGreaterEqual(result.word_count, 300)
        self.assertLessEqual(result.word_count, 500)

    def test_negativele_din_analiza_ajung_in_prompt_negativ(self):
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            _, results = from_sources(self._two_images(tmp), "combina", target="flux", sender=send)
        self.assertIn("smooth skin", results[0].negative_prompt)

    def test_combinarea_apare_ca_observatie_nu_in_prompt(self):
        # „imaginea 1” nu înseamnă nimic pentru modelul-țintă, care primește doar
        # text; nota îi este utilă omului, nu promptului.
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            _, results = from_sources(self._two_images(tmp), "combina", target="flux", sender=send)
        result = results[0]
        self.assertNotIn("imaginea 1", result.prompt)
        self.assertTrue(any("Combinare:" in note for note in result.notes))

    def test_sursele_sunt_notate(self):
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            _, results = from_sources(self._two_images(tmp), "combina", sender=send)
        self.assertTrue(any("Generat din 2 imagini" in note for note in results[0].notes))

    def test_mod_text_din_imagine(self):
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            brief, results = from_sources(
                self._two_images(tmp), "scrie o descriere de produs",
                mode="text", sender=send,
            )
        self.assertEqual(results[0].mode, "text")
        self.assertIn("scrie o descriere de produs", brief.idea)

    def test_variante_multiple(self):
        send = lambda **kw: TestVision.ANALYSIS  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            _, results = from_sources(self._two_images(tmp), "combina", variants=3, sender=send)
        self.assertEqual(len(results), 3)


class TestCLISurse(unittest.TestCase):
    def test_remix_refuza_indici_gresiti(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(TestMedia.PNG)
            self.assertEqual(
                main(["remix", str(path), "--take", "lumina", "--into", "2", "--no-save"]), 2
            )

    def test_remix_refuza_aceeasi_imagine(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(TestMedia.PNG)
            self.assertEqual(
                main(["remix", str(path), str(path), "--take", "lumina",
                      "--source", "1", "--into", "1", "--no-save"]), 2
            )

    def test_vision_semnaleaza_lipsa_modelului(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(TestMedia.PNG)
            # Fără pachetul `anthropic` instalat, codul 3 spune exact asta.
            self.assertIn(main(["vision", str(path), "--no-save"]), (0, 3))


class TestIncarcareWeb(unittest.TestCase):
    def test_decodeaza_data_url(self):
        encoded = base64.standard_b64encode(TestMedia.PNG).decode()
        refs = _decode_uploads([{"name": "a.png", "data_url": f"data:image/png;base64,{encoded}"}])
        self.assertEqual(refs[0].media_type, "image/png")

    def test_refuza_tip_nesuportat(self):
        with self.assertRaises(MediaError):
            _decode_uploads([{"name": "x", "data_url": "data:text/plain;base64,AAAA"}])

    def test_refuza_format_stricat(self):
        with self.assertRaises(MediaError):
            _decode_uploads([{"name": "x", "data_url": "nu-i data url"}])


# ---------------------------------------------------------------------------
# Catalog, platforme, dimensiuni
# ---------------------------------------------------------------------------

class TestCatalog(unittest.TestCase):
    def test_fiecare_model_are_eticheta_de_pret(self):
        for key, model in MODELS.items():
            with self.subTest(model=key):
                self.assertIn(model.pricing, (FREE, FREEMIUM, PAID))
                self.assertTrue(model.pricing_note.strip())

    def test_fiecare_tinta_are_un_model_in_catalog(self):
        # Fără asta, interfața ar arăta o țintă fără etichetă de preț.
        for keys, kind in [(TEXT_TARGETS, "text"), (IMAGE_TARGETS, "image"),
                           (VIDEO_TARGETS, "video")]:
            for key in keys:
                with self.subTest(target=key, kind=kind):
                    self.assertTrue(
                        key in MODELS or f"{key}-{kind}" in MODELS,
                        f"{key} nu are intrare în catalog",
                    )

    def test_parseaza_dimensiuni(self):
        self.assertEqual(parse_size("1080x1920"), (1080, 1920))
        self.assertEqual(parse_size("FullHD"), (1920, 1080))
        self.assertEqual(parse_size("tiktok"), (1080, 1920))
        self.assertEqual(parse_size("reel"), (1080, 1920))

    def test_dimensiune_invalida(self):
        for value in ("mare", "0x100", "abcxdef", "1080"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_size(value)

    def test_raport_de_aspect(self):
        cases = {
            (1920, 1080): "16:9", (1080, 1350): "4:5", (1080, 1920): "9:16",
            (1200, 628): "1.91:1", (1000, 1000): "1:1", (3000, 2000): "3:2",
        }
        for (width, height), expected in cases.items():
            with self.subTest(size=(width, height)):
                self.assertEqual(aspect_of(width, height), expected)

    def test_aspect_refuza_valori_nule(self):
        with self.assertRaises(ValueError):
            aspect_of(0, 100)

    def test_platformele_au_reguli_in_ambele_limbi(self):
        for key, platform in PLATFORMS.items():
            for mode in ("text", "image", "video"):
                rules = platform.rules.get(mode, {})
                for lang in ("ro", "en"):
                    with self.subTest(platform=key, mode=mode, lang=lang):
                        self.assertTrue(rules.get(lang), f"{key}/{mode}/{lang} lipsește")


class TestDimensiuniImagine(unittest.TestCase):
    """Citirea dimensiunilor din antet, fără nicio dependență externă."""

    @staticmethod
    def _png(width, height):
        def chunk(tag, data):
            payload = tag + data
            return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload))
        header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")

    @staticmethod
    def _jpeg(width, height):
        sof = (b"\xff\xc0" + struct.pack(">H", 17) + b"\x08"
               + struct.pack(">HH", height, width)
               + b"\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01")
        return b"\xff\xd8" + sof + b"\xff\xd9"

    def test_png(self):
        self.assertEqual(read_dimensions(self._png(1920, 1080)), (1920, 1080))

    def test_jpeg(self):
        self.assertEqual(read_dimensions(self._jpeg(1080, 1350)), (1080, 1350))

    def test_gif(self):
        raw = b"GIF89a" + struct.pack("<HH", 640, 480) + b"\x00\x00\x00"
        self.assertEqual(read_dimensions(raw), (640, 480))

    def test_webp(self):
        body = (b"VP8X" + struct.pack("<I", 10) + b"\x00\x00\x00\x00"
                + (1199).to_bytes(3, "little") + (627).to_bytes(3, "little"))
        raw = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WEBP" + body
        self.assertEqual(read_dimensions(raw), (1200, 628))

    def test_format_necunoscut_nu_arunca(self):
        self.assertEqual(read_dimensions(b"nu e o imagine"), (0, 0))

    def test_dimensiunea_ajunge_pe_imagine(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(self._png(1080, 1920))
            ref = load_image(str(path))
            self.assertEqual((ref.width, ref.height), (1080, 1920))
            self.assertIn("9:16", ref.size_note())


class TestPlatformeSiDimensiuni(unittest.TestCase):
    def test_platforma_da_aspectul(self):
        result = generate(Brief(idea="a product shot", mode="image", platform="tiktok"))
        self.assertIn("9:16", result.parameters)

    def test_dimensiunea_bate_platforma(self):
        result = generate(Brief(
            idea="a product shot", mode="image", platform="tiktok",
            width=1080, height=1080,
        ))
        self.assertIn("1:1", result.parameters)

    def test_aspectul_explicit_bate_tot(self):
        result = generate(Brief(
            idea="a product shot", mode="image", platform="tiktok",
            width=1080, height=1080, aspect="21:9",
        ))
        self.assertIn("21:9", result.parameters)

    def test_regulile_platformei_ajung_in_prompt(self):
        result = generate(Brief(idea="anunt pentru produs", mode="text", platform="google"))
        self.assertIn("30 de caractere", result.prompt)

    def test_regulile_sunt_in_limba_promptului(self):
        english = generate(Brief(idea="a product shot", mode="image", platform="tiktok"))
        self.assertIn("covered by the interface", english.prompt)
        self.assertNotIn("acoperită de interfață", english.prompt)
        romanian = generate(Brief(idea="a product shot", mode="image",
                                  platform="tiktok", lang="ro"))
        self.assertIn("acoperită de interfață", romanian.prompt)

    def test_dimensiunea_apare_in_prompt(self):
        result = generate(Brief(idea="a poster", mode="image", width=2480, height=3508))
        self.assertIn("2480×3508", result.prompt)

    def test_platforma_necunoscuta(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", platform="myspace")

    def test_dimensiune_incompleta(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", width=1080)


class TestPrompturiLungi(unittest.TestCase):
    def test_intervale_mari_sunt_respectate(self):
        for mode in ("text", "image", "video"):
            for lo, hi in [(300, 500), (800, 1000), (1500, 1800)]:
                with self.subTest(mode=mode, interval=(lo, hi)):
                    result = generate(Brief(
                        idea="an old fisherman mending nets on a stone pier",
                        mode=mode, min_words=lo, max_words=hi,
                    ))
                    self.assertGreaterEqual(result.word_count, lo)
                    self.assertLessEqual(result.word_count, hi)

    def test_limita_superioara(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", min_words=100, max_words=5000)

    def test_semnaleaza_cand_materialul_se_termina(self):
        result = generate(Brief(idea="ceva", mode="image", min_words=2990, max_words=3000))
        self.assertTrue(any("epuizat" in note for note in result.notes))

    def test_avertisment_pentru_prompt_lung(self):
        result = generate(Brief(idea="ceva", mode="text", min_words=1300, max_words=1600))
        self.assertTrue(any("Prompt lung" in note for note in result.notes))

    def test_extensiile_apar_doar_la_buget_mare(self):
        scurt = generate(Brief(idea="a portrait", mode="image", seed=3))
        lung = generate(Brief(idea="a portrait", mode="image", seed=3,
                              min_words=1200, max_words=1500))
        self.assertGreater(lung.word_count, scurt.word_count * 2)


class TestVideo(unittest.TestCase):
    def test_toate_tintele(self):
        for target in VIDEO_TARGETS:
            with self.subTest(target=target):
                result = generate(Brief(idea="a coffee ad", mode="video", target=target))
                self.assertEqual(result.mode, "video")
                self.assertGreaterEqual(result.word_count, 300)
                self.assertLessEqual(result.word_count, 500)

    def test_domeniile_video_sunt_detectate(self):
        cases = {
            "un clip scurt pentru tiktok": "social",
            "o reclama de 15 secunde": "reclama",
            "o scena cinematica cu ploaie": "cinematic",
            "un tutorial video pas cu pas": "tutorial",
        }
        for idea, expected in cases.items():
            with self.subTest(idea=idea):
                self.assertEqual(detect_domain(idea, "video"), expected)

    def test_durata_ajunge_in_prompt_si_parametri(self):
        result = generate(Brief(idea="a coffee ad", mode="video", duration=12))
        self.assertIn("12 seconds", result.prompt)
        self.assertIn("Duration: 12s", result.parameters)

    def test_sora_nu_are_prompt_negativ(self):
        result = generate(Brief(idea="a coffee ad", mode="video", target="sora"))
        self.assertEqual(result.negative_prompt, "")
        self.assertIn("Stated positively", result.prompt)

    def test_kling_are_prompt_negativ(self):
        result = generate(Brief(idea="a coffee ad", mode="video", target="kling"))
        self.assertIn("morphing faces", result.negative_prompt)

    def test_modul_prose_nu_lipeste_propozitiile(self):
        result = generate(Brief(idea="a coffee ad", mode="video", target="sora",
                                platform="tiktok"))
        self.assertNotIn("suggestions:.", result.prompt)
        self.assertNotIn("\n\n", result.prompt)


class TestProfiluri(unittest.TestCase):
    def setUp(self):
        self._home = os.environ.get("PROMPTFORGE_HOME")
        self._tmp = tempfile.mkdtemp()
        os.environ["PROMPTFORGE_HOME"] = self._tmp

    def tearDown(self):
        if self._home is None:
            os.environ.pop("PROMPTFORGE_HOME", None)
        else:
            os.environ["PROMPTFORGE_HOME"] = self._home

    def test_salveaza_si_citeste(self):
        presets.save("al-meu", {"target": "flux", "aspect": "1:1"})
        self.assertEqual(presets.get("al-meu"), {"target": "flux", "aspect": "1:1"})

    def test_optiunile_din_linie_bat_profilul(self):
        presets.save("al-meu", {"target": "flux", "aspect": "1:1"})
        merged = presets.apply("al-meu", {"aspect": "16:9"})
        self.assertEqual(merged["aspect"], "16:9")
        self.assertEqual(merged["target"], "flux")

    def test_listele_se_aduna(self):
        presets.save("al-meu", {"avoid": ["neon"]})
        merged = presets.apply("al-meu", {"avoid": ["blur"]})
        self.assertEqual(merged["avoid"], ["neon", "blur"])

    def test_profil_inexistent(self):
        with self.assertRaises(presets.PresetError):
            presets.get("nu-exista")

    def test_camp_nepermis(self):
        with self.assertRaises(presets.PresetError):
            presets.save("x", {"idea": "nu are ce cauta aici"})

    def test_stergere(self):
        presets.save("temporar", {"target": "flux"})
        presets.delete("temporar")
        self.assertNotIn("temporar", presets.all_presets())


class TestFeedback(unittest.TestCase):
    def setUp(self):
        self._home = os.environ.get("PROMPTFORGE_HOME")
        os.environ["PROMPTFORGE_HOME"] = tempfile.mkdtemp()

    def tearDown(self):
        if self._home is None:
            os.environ.pop("PROMPTFORGE_HOME", None)
        else:
            os.environ["PROMPTFORGE_HOME"] = self._home

    def test_rezultatul_retine_descriptorii(self):
        result = generate(Brief(idea="a portrait", mode="image"))
        self.assertTrue(result.used_descriptors)

    def test_preferatele_sunt_reutilizate(self):
        first = generate(Brief(idea="a portrait", mode="image", seed=1))
        feedback.record(first.used_descriptors, good=True)
        second = generate(Brief(idea="another portrait", mode="image", seed=77))
        self.assertTrue(set(first.used_descriptors) & set(second.used_descriptors))

    def test_cele_slabe_sunt_ocolite(self):
        first = generate(Brief(idea="a portrait", mode="image", seed=1))
        feedback.record(first.used_descriptors, good=False)
        second = generate(Brief(idea="a portrait", mode="image", seed=1))
        self.assertLess(
            len(set(first.used_descriptors) & set(second.used_descriptors)),
            len(first.used_descriptors),
        )

    def test_lista_neagra_completa_nu_blocheaza(self):
        # Chiar dacă toate opțiunile sunt marcate slab, generarea trebuie să meargă.
        first = generate(Brief(idea="a portrait", mode="image"))
        for _ in range(5):
            feedback.record(first.used_descriptors, good=False)
        self.assertGreaterEqual(generate(Brief(idea="a portrait", mode="image")).word_count, 300)

    def test_reset(self):
        feedback.record(["ceva"], good=True)
        feedback.reset()
        self.assertEqual(feedback.preferences(), (set(), set()))


class TestLexiconInvatat(unittest.TestCase):
    def setUp(self):
        self._home = os.environ.get("PROMPTFORGE_HOME")
        os.environ["PROMPTFORGE_HOME"] = tempfile.mkdtemp()

    def tearDown(self):
        if self._home is None:
            os.environ.pop("PROMPTFORGE_HOME", None)
        else:
            os.environ["PROMPTFORGE_HOME"] = self._home

    def test_invata_o_fraza_intreaga(self):
        original = "un dispozitiv ciudat cu manete"
        self.assertEqual(to_english(original)[0], original)
        learn(original, "a strange machine with levers")
        self.assertEqual(to_english(original)[0], "a strange machine with levers")

    def test_invata_un_fragment(self):
        learn("dispozitiv", "machine")
        self.assertIn("machine", to_english("un dispozitiv vechi")[0])

    def test_uita(self):
        learn("manete", "levers")
        self.assertTrue(forget("manete"))
        self.assertFalse(forget("manete"))

    def test_nu_retine_o_traducere_goala(self):
        learn("ceva", "   ")
        self.assertEqual(learned(), {})


class TestAudit(unittest.TestCase):
    def test_prompt_slab_primeste_scor_mic(self):
        result = run_audit("Deseneaza o pisica.", mode="image")
        self.assertLess(result.score, 40)
        self.assertEqual(result.verdict, "incomplet")
        self.assertTrue(result.missing)

    def test_promptul_nostru_trece(self):
        for mode in ("text", "image"):
            with self.subTest(mode=mode):
                generated = generate(Brief(idea="an old fisherman on a pier", mode=mode))
                self.assertGreaterEqual(run_audit(generated.full_text(), mode=mode).score, 80)

    def test_semnaleaza_promptul_prea_scurt(self):
        result = run_audit("fa ceva", mode="text")
        self.assertTrue(any("cuvinte" in note for note in result.notes))

    def test_refuza_promptul_gol(self):
        with self.assertRaises(ValueError):
            run_audit("   ")


class TestCLIExtins(unittest.TestCase):
    def setUp(self):
        self._home = os.environ.get("PROMPTFORGE_HOME")
        os.environ["PROMPTFORGE_HOME"] = tempfile.mkdtemp()

    def tearDown(self):
        if self._home is None:
            os.environ.pop("PROMPTFORGE_HOME", None)
        else:
            os.environ["PROMPTFORGE_HOME"] = self._home

    def test_comanda_modele(self):
        self.assertEqual(main(["modele"]), 0)
        self.assertEqual(main(["modele", "--kind", "video"]), 0)

    def test_ciclu_complet_de_profil(self):
        self.assertEqual(main(["preset", "salveaza", "p", "--set", "target=flux"]), 0)
        self.assertEqual(main(["preset", "lista"]), 0)
        self.assertEqual(main(["image", "o cana", "--preset", "p", "--no-save"]), 0)
        self.assertEqual(main(["preset", "sterge", "p"]), 0)

    def test_profil_cu_camp_gresit(self):
        self.assertEqual(main(["preset", "salveaza", "p", "--set", "fara-egal"]), 2)

    def test_comanda_video(self):
        self.assertEqual(main(["video", "o reclama la cafea", "--duration", "10", "--no-save"]), 0)

    def test_comanda_audit(self):
        self.assertEqual(main(["audit", "Deseneaza o pisica", "--mode", "image"]), 0)

    def test_lexicon_prin_cli(self):
        self.assertEqual(main(["lexicon", "--adauga", "manete=levers"]), 0)
        self.assertEqual(main(["lexicon"]), 0)
        self.assertEqual(main(["lexicon", "--adauga", "fara-egal"]), 2)

    def test_feedback_din_istoric(self):
        self.assertEqual(main(["image", "o cana de cafea"]), 0)
        self.assertEqual(main(["bun"]), 0)
        self.assertEqual(main(["preferinte"]), 0)

    def test_feedback_fara_istoric(self):
        self.assertEqual(main(["bun"]), 2)

    def test_dimensiune_invalida_in_cli(self):
        # Eroarea e prinsă și raportată, nu propagată ca excepție.
        self.assertEqual(main(["image", "ceva", "--size", "gresit", "--no-save"]), 2)

    def test_subiectul_dat_manual_este_invatat(self):
        main(["image", "un pescar batran", "--subject", "an old fisherman", "--no-save"])
        self.assertIn("un pescar batran", learned())
