"""Teste de interfață, într-un browser real.

Se sar dacă Playwright sau un Chromium nu sunt disponibile — deci nu împiedică
rularea suitei obișnuite. Rulează-le când atingi pagina web:

    pip install playwright && playwright install chromium
    python -m unittest tests.test_browser

Ce verifică: exact ce nu poate verifica un test de server — că JavaScript-ul
comută modurile, adună pozele, afișează erorile și nu aruncă nimic în consolă.
"""

from __future__ import annotations

import os
import struct
import tempfile
import threading
import time
import unittest
import zlib
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:                                  # pragma: no cover
    sync_playwright = None                           # type: ignore[assignment]

# Chromium-ul din imaginile Playwright, dacă lansarea implicită nu merge.
_CAI_CHROMIUM = ("/opt/pw-browsers/chromium", "/usr/bin/chromium", "/usr/bin/chromium-browser")


def _png(width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = tag + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")


def _lanseaza(pw):
    """Pornește un browser, cu binarul implicit sau cu unul găsit pe disc."""
    try:
        return pw.chromium.launch(args=["--no-sandbox"])
    except Exception:
        for cale in _CAI_CHROMIUM:
            if Path(cale).exists():
                return pw.chromium.launch(executable_path=cale, args=["--no-sandbox"])
        raise


def _browser_disponibil() -> bool:
    if sync_playwright is None:
        return False
    try:
        with sync_playwright() as pw:
            _lanseaza(pw).close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_browser_disponibil(), "Playwright sau Chromium lipsesc")
class TestInterfataWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from promptforge.web import serve

        os.environ.setdefault("PROMPTFORGE_HOME", tempfile.mkdtemp())
        import socket

        proba = socket.socket()
        proba.bind(("127.0.0.1", 0))
        cls.port = proba.getsockname()[1]
        proba.close()

        threading.Thread(
            target=serve, kwargs={"port": cls.port, "open_browser": False}, daemon=True
        ).start()
        time.sleep(1)

        cls._pw = sync_playwright().start()
        cls.browser = _lanseaza(cls._pw)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()

    def setUp(self):
        self.erori: list[str] = []
        self.page = self.browser.new_page()
        self.page.on("pageerror", lambda e: self.erori.append(f"pageerror: {e}"))
        self.page.on(
            "console",
            lambda m: self.erori.append(f"console: {m.text}") if m.type == "error" else None,
        )
        self.page.goto(f"http://127.0.0.1:{self.port}/", wait_until="networkidle")

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.erori, [], "erori în consola browserului")

    def test_comutarea_intre_moduri(self):
        asteptat = {
            "auto": [], "text": ["text-only"], "image": ["image-only"],
            "video": ["video-only"], "seo": ["seo-only"], "vision": ["vision-only"],
        }
        for mod, clase in asteptat.items():
            with self.subTest(mod=mod):
                self.page.click(f"#mode-{mod}")
                self.assertEqual(self.page.get_attribute(f"#mode-{mod}", "aria-pressed"), "true")
                vizibile = self.page.eval_on_selector_all(
                    ".seo-only, .vision-only, .video-only, .image-only, .text-only",
                    "els => els.filter(e => !e.hidden).map(e => e.className)",
                )
                for clasa in clase:
                    self.assertTrue(any(clasa in v for v in vizibile), f"{clasa} ascuns")

    def test_eticheta_de_pret_apare_langa_model(self):
        self.page.click("#mode-image")
        self.page.select_option("#target", "midjourney")
        self.assertIn("abonament", self.page.inner_text("#pricing").lower())
        optiuni = self.page.eval_on_selector_all("#target option", "e => e.map(x => x.textContent)")
        self.assertTrue(any("platit" in o or "freemium" in o or "gratis" in o for o in optiuni))

    def test_generarea_prin_interfata(self):
        self.page.click("#mode-text")
        self.page.fill("#idea", "o aplicatie care imi urmareste cheltuielile")
        self.page.click("#go")
        self.page.wait_for_selector(".result pre", timeout=30000)
        self.assertGreater(len(self.page.inner_text(".result pre").split()), 250)
        self.assertIn("Varianta 1", self.page.inner_text(".result .meta"))

    def test_ideea_goala_da_mesaj_vizibil(self):
        self.page.click("#mode-text")
        self.page.fill("#idea", "")
        self.page.click("#go")
        self.page.wait_for_selector(".err", timeout=8000)
        self.assertIn("idee", self.page.inner_text(".err").lower())

    def test_modul_seo_foloseste_continutul_lipit(self):
        self.page.click("#mode-seo")
        self.page.fill("#source", "Paine cu maia coapta zilnic in Cluj. Se face lent.")
        self.page.click("#go")
        self.page.wait_for_selector(".result pre", timeout=30000)
        self.assertIn("CUVINTE-CHEIE", self.page.inner_text(".result pre").upper())

    def test_verificatorul_de_lungimi(self):
        self.page.select_option("#check-platform", "google")
        self.page.fill("#check-text", "TITLU: Un titlu mult prea lung pentru un anunt Google Ads")
        self.page.click("#check-go")
        self.page.wait_for_selector(".check-row", timeout=15000)
        self.assertIn("peste limita", self.page.inner_text("#check-out"))
        self.assertIsNotNone(self.page.query_selector(".check-bad"))

    def test_pozele_se_aduna_si_se_pot_scoate(self):
        self.page.click("#mode-vision")
        self.page.set_input_files(
            "#files", [{"name": "a.png", "mimeType": "image/png", "buffer": _png(800, 600)}]
        )
        self.page.wait_for_selector(".thumbs figure", timeout=8000)
        # A doua alegere adaugă, nu înlocuiește.
        self.page.set_input_files(
            "#files", [{"name": "b.png", "mimeType": "image/png", "buffer": _png(600, 800)}]
        )
        self.page.wait_for_function(
            "document.querySelectorAll('.thumbs figure').length === 2", timeout=8000
        )
        etichete = self.page.eval_on_selector_all(
            ".thumbs figcaption", "e => e.map(x => x.textContent)"
        )
        self.assertEqual(etichete, ["imaginea 1", "imaginea 2"])

        self.page.click(".thumbs figure:first-child button")
        self.page.wait_for_function(
            "document.querySelectorAll('.thumbs figure').length === 1", timeout=8000
        )
        ramase = self.page.eval_on_selector_all(
            ".thumbs figcaption", "e => e.map(x => x.textContent)"
        )
        self.assertEqual(ramase, ["imaginea 1"], "renumerotarea după ștergere")

    def test_zona_de_tragere_reactioneaza(self):
        self.page.click("#mode-vision")
        self.page.eval_on_selector(
            "#drop", "el => el.dispatchEvent(new DragEvent('dragover', {bubbles:true}))"
        )
        self.assertIn("over", self.page.get_attribute("#drop", "class") or "")
        self.page.eval_on_selector(
            "#drop", "el => el.dispatchEvent(new DragEvent('dragleave', {bubbles:true}))"
        )
        self.assertNotIn("over", self.page.get_attribute("#drop", "class") or "")

    def test_modul_din_poze_cere_o_sursa(self):
        self.page.click("#mode-vision")
        self.page.fill("#idea", "combina-le")
        self.page.click("#go")
        self.page.wait_for_selector(".err", timeout=8000)
        self.assertIn("poz", self.page.inner_text(".err").lower())

    def test_tema_urmeaza_setarea_sistemului(self):
        self.page.emulate_media(color_scheme="dark")
        intunecat = self.page.eval_on_selector("body", "el => getComputedStyle(el).backgroundColor")
        self.page.emulate_media(color_scheme="light")
        deschis = self.page.eval_on_selector("body", "el => getComputedStyle(el).backgroundColor")
        self.assertNotEqual(intunecat, deschis)
