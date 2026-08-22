"""Interfață web locală, construită doar cu biblioteca standard.

Pornește cu `promptforge serve`. Serverul ascultă implicit pe 127.0.0.1, deci
nu este expus în rețea.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import generate_many
from .models import Brief, DEFAULT_MAX_WORDS, DEFAULT_MIN_WORDS, MODE_IMAGE, MODE_TEXT
from .targets import IMAGE_TARGETS, TEXT_TARGETS
from .vocab import IMAGE_DOMAINS, TEXT_DOMAINS, TONES

PAGE = """<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PromptForge</title>
<style>
  :root {
    --bg: #fbfaf8; --fg: #1c1b19; --muted: #6b6862; --line: #e2ded7;
    --card: #ffffff; --accent: #9a4a2f; --code: #f4f1ec;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #171614; --fg: #ece9e3; --muted: #9b968d; --line: #2e2c28;
      --card: #1f1e1b; --accent: #d98b6a; --code: #232120;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 2rem 1.25rem 4rem; background: var(--bg); color: var(--fg);
    font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  main { max-width: 900px; margin: 0 auto; }
  h1 { font-size: 1.5rem; margin: 0 0 .25rem; letter-spacing: -0.01em; }
  p.lead { color: var(--muted); margin: 0 0 2rem; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem; }
  label { display: block; font-size: .82rem; text-transform: uppercase;
          letter-spacing: .06em; color: var(--muted); margin-bottom: .35rem; }
  textarea, input, select {
    width: 100%; padding: .6rem .7rem; border: 1px solid var(--line); border-radius: 8px;
    background: var(--bg); color: var(--fg); font: inherit;
  }
  textarea { min-height: 5.5rem; resize: vertical; }
  .grid { display: grid; gap: .9rem; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-top: 1rem; }
  .row { margin-top: 1rem; }
  button {
    margin-top: 1.25rem; padding: .7rem 1.4rem; border: 0; border-radius: 8px;
    background: var(--accent); color: #fff; font: inherit; font-weight: 600; cursor: pointer;
  }
  button:disabled { opacity: .55; cursor: progress; }
  .modes { display: flex; gap: .5rem; margin-bottom: 1rem; }
  .modes button {
    margin: 0; flex: 1; background: transparent; color: var(--muted);
    border: 1px solid var(--line); font-weight: 500;
  }
  .modes button[aria-pressed="true"] { background: var(--accent); color: #fff; border-color: var(--accent); }
  .result { margin-top: 1.5rem; }
  .meta { font-size: .82rem; color: var(--muted); margin-bottom: .5rem; }
  pre {
    background: var(--code); border: 1px solid var(--line); border-radius: 10px;
    padding: 1rem; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
    font: 14px/1.65 ui-monospace, SFMono-Regular, Menlo, monospace; margin: 0;
  }
  .copy { margin-top: .5rem; padding: .35rem .8rem; font-size: .85rem; background: transparent;
          color: var(--accent); border: 1px solid var(--line); }
  .notes { font-size: .88rem; color: var(--muted); margin-top: .6rem; padding-left: 1.1rem; }
  .err { color: #c0392b; margin-top: 1rem; }
</style>
</head>
<body>
<main>
  <h1>PromptForge</h1>
  <p class="lead">Transformă o idee într-un prompt detaliat, de 300–500 de cuvinte.</p>

  <div class="card">
    <div class="modes">
      <button type="button" id="mode-text" aria-pressed="true">Text</button>
      <button type="button" id="mode-image" aria-pressed="false">Imagine</button>
    </div>

    <label for="idea">Ideea ta</label>
    <textarea id="idea" placeholder="ex: o aplicație care îmi urmărește cheltuielile lunare"></textarea>

    <div class="grid">
      <div>
        <label for="target">Model-țintă</label>
        <select id="target"></select>
      </div>
      <div>
        <label for="domain">Domeniu</label>
        <select id="domain"></select>
      </div>
      <div>
        <label for="variants">Variante</label>
        <input id="variants" type="number" value="1" min="1" max="5">
      </div>
      <div class="text-only">
        <label for="tone">Ton</label>
        <select id="tone"></select>
      </div>
      <div class="text-only">
        <label for="audience">Audiență</label>
        <input id="audience" placeholder="opțional">
      </div>
      <div class="image-only" hidden>
        <label for="aspect">Raport de aspect</label>
        <input id="aspect" placeholder="automat">
      </div>
      <div class="image-only" hidden>
        <label for="subject">Subiect în engleză</label>
        <input id="subject" placeholder="opțional">
      </div>
      <div>
        <label for="minw">Minim cuvinte</label>
        <input id="minw" type="number" value="__MIN__">
      </div>
      <div>
        <label for="maxw">Maxim cuvinte</label>
        <input id="maxw" type="number" value="__MAX__">
      </div>
    </div>

    <div class="row">
      <label for="must">Trebuie să conțină (unul pe rând)</label>
      <textarea id="must" style="min-height:3.5rem"></textarea>
    </div>
    <div class="row">
      <label for="avoid">De evitat (unul pe rând)</label>
      <textarea id="avoid" style="min-height:3.5rem"></textarea>
    </div>

    <button id="go">Generează</button>
  </div>

  <div id="out"></div>
</main>

<script>
const CONFIG = __CONFIG__;
let mode = "text";

const $ = (id) => document.getElementById(id);

function fillSelect(el, values, blankLabel) {
  el.innerHTML = "";
  if (blankLabel) {
    const opt = document.createElement("option");
    opt.value = ""; opt.textContent = blankLabel;
    el.appendChild(opt);
  }
  for (const value of values) {
    const opt = document.createElement("option");
    opt.value = value; opt.textContent = value;
    el.appendChild(opt);
  }
}

function applyMode() {
  $("mode-text").setAttribute("aria-pressed", mode === "text");
  $("mode-image").setAttribute("aria-pressed", mode === "image");
  document.querySelectorAll(".text-only").forEach(el => el.hidden = mode !== "text");
  document.querySelectorAll(".image-only").forEach(el => el.hidden = mode !== "image");
  fillSelect($("target"), CONFIG.targets[mode], "implicit");
  fillSelect($("domain"), CONFIG.domains[mode], "detectare automată");
}

$("mode-text").onclick = () => { mode = "text"; applyMode(); };
$("mode-image").onclick = () => { mode = "image"; applyMode(); };

fillSelect($("tone"), CONFIG.tones, "implicit");
applyMode();

function lines(id) {
  return $(id).value.split("\\n").map(s => s.trim()).filter(Boolean);
}

function escapeHtml(text) {
  return text.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

$("go").onclick = async () => {
  const idea = $("idea").value.trim();
  const out = $("out");
  if (!idea) { out.innerHTML = '<p class="err">Scrie mai întâi o idee.</p>'; return; }

  $("go").disabled = true;
  out.innerHTML = '<p class="meta">Se generează…</p>';

  const body = {
    idea, mode,
    target: $("target").value || null,
    domain: $("domain").value || null,
    variants: parseInt($("variants").value, 10) || 1,
    min_words: parseInt($("minw").value, 10),
    max_words: parseInt($("maxw").value, 10),
    must: lines("must"),
    avoid: lines("avoid"),
    tone: mode === "text" ? ($("tone").value || null) : null,
    audience: mode === "text" ? ($("audience").value.trim() || null) : null,
    aspect: mode === "image" ? ($("aspect").value.trim() || null) : null,
    subject: mode === "image" ? ($("subject").value.trim() || null) : null,
  };

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      out.innerHTML = '<p class="err">' + escapeHtml(data.error || "Eroare necunoscută") + '</p>';
      return;
    }
    out.innerHTML = data.results.map(render).join("");
    document.querySelectorAll(".copy").forEach(btn => {
      btn.onclick = () => {
        navigator.clipboard.writeText(btn.previousElementSibling.textContent);
        btn.textContent = "Copiat";
        setTimeout(() => { btn.textContent = "Copiază"; }, 1500);
      };
    });
  } catch (err) {
    out.innerHTML = '<p class="err">' + escapeHtml(String(err)) + '</p>';
  } finally {
    $("go").disabled = false;
  }
};

function render(r) {
  let html = '<div class="result"><div class="meta">Varianta ' + r.variant +
             ' · domeniu: ' + escapeHtml(r.domain) + ' · țintă: ' + escapeHtml(r.target) +
             ' · ' + r.word_count + ' cuvinte</div>';
  html += '<pre>' + escapeHtml(r.full_text) + '</pre>';
  html += '<button class="copy">Copiază</button>';
  if (r.notes && r.notes.length) {
    html += '<ul class="notes">' + r.notes.map(n => '<li>' + escapeHtml(n) + '</li>').join("") + '</ul>';
  }
  return html + '</div>';
}
</script>
</body>
</html>
"""


def _page() -> bytes:
    config = {
        "targets": {
            MODE_TEXT: sorted(TEXT_TARGETS),
            MODE_IMAGE: sorted(IMAGE_TARGETS),
        },
        "domains": {
            MODE_TEXT: sorted(TEXT_DOMAINS),
            MODE_IMAGE: sorted(IMAGE_DOMAINS),
        },
        "tones": sorted(TONES),
    }
    html = (
        PAGE.replace("__CONFIG__", json.dumps(config))
        .replace("__MIN__", str(DEFAULT_MIN_WORDS))
        .replace("__MAX__", str(DEFAULT_MAX_WORDS))
    )
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "PromptForge"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - semnătură impusă
        pass  # fără zgomot în terminal

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - semnătură impusă
        if self.path in ("/", "/index.html"):
            self._send(200, _page(), "text/html; charset=utf-8")
        else:
            self._send_json(404, {"error": "Pagină inexistentă"})

    def do_POST(self) -> None:  # noqa: N802 - semnătură impusă
        if self.path != "/api/generate":
            self._send_json(404, {"error": "Rută inexistentă"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 100_000:
            self._send_json(400, {"error": "Cerere invalidă"})
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "JSON invalid"})
            return

        variants = payload.pop("variants", 1)
        try:
            variants = max(1, min(5, int(variants)))
            brief = Brief(
                idea=payload.get("idea", ""),
                mode=payload.get("mode", MODE_TEXT),
                domain=payload.get("domain") or None,
                target=payload.get("target") or None,
                audience=payload.get("audience") or None,
                tone=payload.get("tone") or None,
                aspect=payload.get("aspect") or None,
                subject=payload.get("subject") or None,
                must=list(payload.get("must") or []),
                avoid=list(payload.get("avoid") or []),
                min_words=int(payload.get("min_words") or DEFAULT_MIN_WORDS),
                max_words=int(payload.get("max_words") or DEFAULT_MAX_WORDS),
            )
            results = generate_many(brief, variants)
        except (ValueError, TypeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_json(
            200,
            {
                "results": [
                    {**result.to_dict(), "full_text": result.full_text()} for result in results
                ]
            },
        )


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Pornește serverul local până la Ctrl+C."""
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/"
    print(f"PromptForge rulează la {url}  (Ctrl+C pentru oprire)")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nOprit.")
    finally:
        httpd.server_close()
