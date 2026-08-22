"""Teste pentru PromptForge. Rulează cu: python -m unittest discover tests"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from promptforge import Brief, generate, generate_many
from promptforge.assembly import count_words, fit, range_note, sentence
from promptforge.cli import main
from promptforge.detect import detect_domain, keywords_of
from promptforge.history import load, save
from promptforge.image_engine import looks_romanian
from promptforge.models import Section
from promptforge.targets import IMAGE_TARGETS, TEXT_TARGETS
from promptforge.vocab import IMAGE_DOMAINS, TEXT_DOMAINS


class TestBrief(unittest.TestCase):
    def test_refuza_ideea_goala(self):
        with self.assertRaises(ValueError):
            Brief(idea="   ")

    def test_refuza_mod_necunoscut(self):
        with self.assertRaises(ValueError):
            Brief(idea="ceva", mode="video")

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

    def test_avertizeaza_pentru_subiect_in_romana(self):
        result = generate(Brief(idea="un portret cu o femeie la fereastra", mode="image"))
        self.assertTrue(any("română" in note for note in result.notes))

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
