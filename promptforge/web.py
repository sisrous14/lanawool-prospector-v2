"""Interfață web locală, construită doar cu biblioteca standard.

Pornește cu `promptforge serve`. Serverul ascultă implicit pe 127.0.0.1, deci
nu este expus în rețea.
"""

from __future__ import annotations

import json
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import generate_many
from .catalog import (
    MODELS,
    PLATFORMS,
    PRICING_DISCLAIMER,
    SIZES,
    check_text,
    known_fields,
    parse_size,
)
from .media import ImageRef, MediaError, SUPPORTED_TYPES
from .models import (
    Brief,
    PROMPT_WORD_CAP,
    DEFAULT_MAX_WORDS,
    DEFAULT_MIN_WORDS,
    MAX_ALLOWED_WORDS,
    MODE_IMAGE,
    MODE_SEO,
    MODE_TEXT,
    MODE_VIDEO,
)
from .seo import CONTENT_TYPES as SEO_TYPES, INTENTS as SEO_INTENTS
from .targets import IMAGE_TARGETS, TEXT_TARGETS, VIDEO_TARGETS
from .vocab import IMAGE_DOMAINS, TEXT_DOMAINS, TONES, VIDEO_DOMAINS

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
  .drop {
    border: 2px dashed var(--line); border-radius: 12px; padding: 1.5rem 1rem;
    text-align: center; cursor: pointer; display: flex; flex-direction: column;
    gap: .3rem; color: var(--muted); transition: border-color .15s, background .15s;
  }
  .drop strong { color: var(--fg); font-size: .95rem; }
  .drop span { font-size: .82rem; }
  .drop.over { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, transparent); }
  .pricing { font-size: .78rem; color: var(--muted); margin: .3rem 0 0; }
  .thumbs { display: flex; gap: .5rem; flex-wrap: wrap; margin: .75rem 0 0; }
  .thumbs figure { margin: 0; text-align: center; font-size: .75rem; color: var(--muted); }
  .thumbs img { width: 86px; height: 86px; object-fit: cover; border-radius: 8px;
                border: 1px solid var(--line); display: block; }
  .check-row { display: flex; gap: .6rem; align-items: baseline; font-size: .9rem;
               padding: .35rem 0; border-bottom: 1px solid var(--line); }
  .check-row .name { flex: 1; }
  .check-row .len { font-variant-numeric: tabular-nums; color: var(--muted); }
  .check-ok { color: #2d7a4f; }
  .check-warn { color: #b07d16; }
  .check-bad { color: #c0392b; }
  .thumbs button { margin: .2rem 0 0; padding: .1rem .45rem; font-size: .72rem;
                   background: transparent; color: var(--muted); border: 1px solid var(--line); }
</style>
</head>
<body>
<main>
  <h1>PromptForge</h1>
  <p class="lead">Transformă o idee într-un prompt detaliat — de la 300 până la 3000 de cuvinte.</p>

  <div class="card">
    <div class="modes">
      <button type="button" id="mode-auto" aria-pressed="true">Automat</button>
      <button type="button" id="mode-text" aria-pressed="false">Text</button>
      <button type="button" id="mode-image" aria-pressed="false">Imagine</button>
      <button type="button" id="mode-video" aria-pressed="false">Video</button>
      <button type="button" id="mode-seo" aria-pressed="false">SEO</button>
      <button type="button" id="mode-vision" aria-pressed="false">Din poze</button>
    </div>

    <div class="seo-only" hidden>
      <label for="source">Conținutul de optimizat (text, descriere de produs, articol)</label>
      <textarea id="source" placeholder="Lipește aici textul. Cuvintele-cheie se extrag din el."></textarea>
    </div>

    <div class="vision-only" hidden>
      <div id="drop" class="drop" tabindex="0" role="button"
           aria-label="Trage pozele aici sau apasă pentru a alege">
        <strong>Trage pozele aici</strong>
        <span>sau apasă pentru a alege &middot; poți lipi și cu Ctrl+V &middot;
              se adaugă la cele existente</span>
        <input id="files" type="file" accept="image/*" multiple hidden>
      </div>
      <label for="links" style="margin-top:.9rem">sau adrese web, una pe rând</label>
      <textarea id="links" style="min-height:3rem" placeholder="https://exemplu.ro/poza.jpg"></textarea>
      <div class="thumbs" id="thumbs"></div>
    </div>

    <label for="idea" id="idea-label">Ideea ta</label>
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
        <label for="platform">Platformă</label>
        <select id="platform"></select>
      </div>
      <div class="image-only" hidden>
        <label for="size">Dimensiune</label>
        <input id="size" list="size-list" placeholder="ex. 1080x1920">
        <datalist id="size-list"></datalist>
      </div>
      <div class="video-only" hidden>
        <label for="duration">Durată (secunde)</label>
        <input id="duration" type="number" min="2" max="60" placeholder="8">
      </div>
      <div class="seo-only" hidden>
        <label for="seotype">Tip de pagină</label>
        <select id="seotype"></select>
      </div>
      <div class="seo-only" hidden>
        <label for="keyword">Cuvânt-cheie</label>
        <input id="keyword" placeholder="se extrage din conținut">
      </div>
      <div class="seo-only" hidden>
        <label for="intent">Intenția de căutare</label>
        <select id="intent"></select>
      </div>
      <div>
        <label for="minw">Minim cuvinte</label>
        <input id="minw" type="number" value="__MIN__">
      </div>
      <div>
        <label for="parts">Prompturi înlănțuite</label>
        <input id="parts" type="number" min="1" max="100" placeholder="automat">
      </div>
      <div>
        <label for="maxw">Maxim cuvinte</label>
        <input id="maxw" type="number" value="__MAX__" min="60" max="__LIMIT__">
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

    <p class="pricing" id="pricing"></p>
    <p class="pricing auto-only">
      În modul automat programul alege singur modul, domeniul, modelul, formatul
      și lungimea, apoi îți spune ce a ales. Peste 3000 de cuvinte, lucrarea se
      împarte singură într-un lanț de prompturi care se continuă unul pe altul.
    </p>
    <button id="go">Generează</button>
  </div>

  <div id="out"></div>

  <div class="card" style="margin-top:2rem">
    <h2 style="font-size:1.05rem;margin:0 0 .3rem">Verifică lungimile</h2>
    <p class="pricing" style="margin:0 0 .9rem">
      Lipește textul primit înapoi de la model, sub forma <code>TITLU: …</code> pe rânduri,
      și îți spune ce depășește limitele platformei.
    </p>
    <div class="grid" style="margin-top:0">
      <div>
        <label for="check-platform">Platformă</label>
        <select id="check-platform"></select>
      </div>
    </div>
    <div class="row">
      <label for="check-text">Text de verificat</label>
      <textarea id="check-text" placeholder="TITLU: ...&#10;DESCRIERE: ...&#10;META: ..."></textarea>
    </div>
    <button id="check-go">Verifică</button>
    <div id="check-out"></div>
  </div>
</main>

<script>
const CONFIG = __CONFIG__;
let mode = "auto";

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
    if (typeof value === "string") {
      opt.value = value; opt.textContent = value;
    } else {
      opt.value = value.key;
      // Eticheta de preț stă lângă nume, ca alegerea să fie informată.
      opt.textContent = value.pricing
        ? value.label + " — " + value.pricing
        : value.label;
      opt.dataset.note = value.note || "";
    }
    el.appendChild(opt);
  }
}

function showPricing() {
  const option = $("target").selectedOptions[0];
  $("pricing").textContent = (option && option.dataset.note) || "";
}

const MODES = ["auto", "text", "image", "video", "seo", "vision"];

function applyMode() {
  for (const name of MODES) {
    $("mode-" + name).setAttribute("aria-pressed", mode === name);
  }
  document.querySelectorAll(".text-only").forEach(el => el.hidden = mode !== "text");
  document.querySelectorAll(".auto-only").forEach(el => el.hidden = mode !== "auto");
  document.querySelectorAll(".image-only").forEach(
    el => el.hidden = mode === "text" || mode === "video" || mode === "seo" || mode === "auto");
  document.querySelectorAll(".video-only").forEach(el => el.hidden = mode !== "video");
  document.querySelectorAll(".seo-only").forEach(el => el.hidden = mode !== "seo");
  document.querySelectorAll(".vision-only").forEach(el => el.hidden = mode !== "vision");
  $("idea-label").textContent =
    mode === "vision"
      ? "Ce vrei să obții din poze (ex: ia lumina din imaginea 1 și pune-o peste subiectul din imaginea 2)"
      : mode === "seo"
        ? "Subiectul paginii (opțional, dacă ai lipit conținut mai sus)"
        : "Ideea ta";
  $("domain").parentElement.hidden = mode === "vision" || mode === "seo" || mode === "auto";
  $("target").parentElement.hidden = mode === "auto";
  const key = (mode === "vision" || mode === "auto") ? "image" : (mode === "seo" ? "text" : mode);
  if (mode === "auto") { fillSelect($("target"), CONFIG.targets.text, "implicit"); }
  fillSelect($("target"), CONFIG.targets[key], "implicit");
  fillSelect($("domain"), CONFIG.domains[key], "detectare automată");
  showPricing();
}

for (const name of MODES) {
  $("mode-" + name).onclick = () => { mode = name; applyMode(); };
}
$("target").onchange = showPricing;

// --- Pozele: adăugate prin buton, prin tragere sau prin lipire. Se adună în
// aceeași sesiune, nu se înlocuiesc, și fiecare poate fi scoasă individual.
const picked = [];

function renderThumbs() {
  $("thumbs").innerHTML = "";
  picked.forEach((item, index) => {
    const figure = document.createElement("figure");
    const img = document.createElement("img");
    img.src = item.data_url;
    img.alt = item.name;
    const caption = document.createElement("figcaption");
    caption.textContent = "imaginea " + (index + 1);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "scoate";
    remove.onclick = () => { picked.splice(index, 1); renderThumbs(); };
    figure.append(img, caption, remove);
    $("thumbs").appendChild(figure);
  });
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function addFiles(files) {
  for (const file of files) {
    if (!file || !file.type.startsWith("image/")) continue;
    picked.push({ name: file.name || "poza", data_url: await readFile(file) });
  }
  renderThumbs();
}

$("files").onchange = (event) => {
  addFiles(event.target.files);
  event.target.value = "";     // aceeași poză poate fi aleasă din nou
};

const drop = $("drop");
drop.onclick = () => $("files").click();
drop.onkeydown = (event) => {
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); $("files").click(); }
};
for (const name of ["dragenter", "dragover"]) {
  drop.addEventListener(name, (event) => {
    event.preventDefault();
    drop.classList.add("over");
  });
}
for (const name of ["dragleave", "drop"]) {
  drop.addEventListener(name, (event) => {
    event.preventDefault();
    drop.classList.remove("over");
  });
}
drop.addEventListener("drop", (event) => {
  if (event.dataTransfer && event.dataTransfer.files.length) {
    addFiles(event.dataTransfer.files);
  }
});
document.addEventListener("paste", (event) => {
  if (mode !== "vision" || !event.clipboardData) return;
  const files = Array.from(event.clipboardData.files || []);
  if (files.length) { event.preventDefault(); addFiles(files); }
});

fillSelect($("tone"), CONFIG.tones, "implicit");
fillSelect($("platform"), CONFIG.platforms, "niciuna");
fillSelect($("seotype"), CONFIG.seoTypes, "");
fillSelect($("intent"), CONFIG.seoIntents, "");
fillSelect($("check-platform"), CONFIG.platforms.filter(p => p.hasFields), "");
for (const name of CONFIG.sizes) {
  const option = document.createElement("option");
  option.value = name;
  $("size-list").appendChild(option);
}
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
  if (!idea && mode !== "vision" && mode !== "seo") {
    out.innerHTML = '<p class="err">Scrie mai întâi o idee.</p>';
    return;
  }

  $("go").disabled = true;
  out.innerHTML = '<p class="meta">Se generează…</p>';

  const body = {
    idea: idea || "descrie sursele primite", mode,
    target: $("target").value || null,
    domain: $("domain").value || null,
    variants: parseInt($("variants").value, 10) || 1,
    min_words: parseInt($("minw").value, 10),
    max_words: parseInt($("maxw").value, 10),
    must: lines("must"),
    avoid: lines("avoid"),
    tone: mode === "text" ? ($("tone").value || null) : null,
    audience: mode === "text" ? ($("audience").value.trim() || null) : null,
    aspect: mode !== "text" ? ($("aspect").value.trim() || null) : null,
    subject: mode !== "text" ? ($("subject").value.trim() || null) : null,
    platform: $("platform").value || null,
    size: mode !== "text" ? ($("size").value.trim() || null) : null,
    duration: mode === "video" ? (parseInt($("duration").value, 10) || 0) : 0,
    source_text: mode === "seo" ? $("source").value.trim() : "",
    keyword: mode === "seo" ? $("keyword").value.trim() : "",
    intent: mode === "seo" ? ($("intent").value || "") : "",
    parts: parseInt($("parts").value, 10) || 0,
  };

  if (mode === "auto") {
    body.target = null;
    body.domain = null;
  }

  if (mode === "seo") {
    body.domain = $("seotype").value || null;
    if (!body.source_text && !idea) {
      out.innerHTML = '<p class="err">Lipește conținutul de optimizat sau scrie subiectul paginii.</p>';
      $("go").disabled = false;
      return;
    }
  }

  if (mode === "vision") {
    body.images = picked;
    body.links = lines("links");
    body.mode = "image";
    if (!body.images.length && !body.links.length) {
      out.innerHTML = '<p class="err">Adaugă cel puțin o poză sau o adresă.</p>';
      $("go").disabled = false;
      return;
    }
  }

  try {
    const response = await fetch(mode === "vision" ? "/api/vision" : "/api/generate", {
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

$("check-go").onclick = async () => {
  const out = $("check-out");
  const text = $("check-text").value.trim();
  if (!text) { out.innerHTML = '<p class="err">Nu ai scris nimic de verificat.</p>'; return; }
  $("check-go").disabled = true;
  try {
    const response = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ platform: $("check-platform").value, text }),
    });
    const data = await response.json();
    if (!response.ok) {
      out.innerHTML = '<p class="err">' + escapeHtml(data.error) + "</p>";
      return;
    }
    const css = { ok: "check-ok", atentie: "check-warn", depasit: "check-bad", gol: "" };
    out.innerHTML = '<div style="margin-top:1rem">' + data.rows.map(row =>
      '<div class="check-row"><span class="name">' + escapeHtml(row.label) +
      '</span><span class="len">' + row.length + '</span><span class="' +
      (css[row.verdict] || "") + '">' + escapeHtml(row.explanation) + "</span></div>"
    ).join("") + "</div>";
  } catch (err) {
    out.innerHTML = '<p class="err">' + escapeHtml(String(err)) + "</p>";
  } finally {
    $("check-go").disabled = false;
  }
};

function render(r) {
  const isLink = (r.notes || []).some(n => n.startsWith("Veriga"));
  let html = '<div class="result"><div class="meta">' + (isLink ? "Veriga " : "Varianta ") + r.variant +
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


MAX_JSON_BYTES = 100_000
MAX_UPLOAD_BYTES = 30 * 1024 * 1024


def _string_list(value: object) -> list[str]:
    """Listă de șiruri dintr-o valoare venită de afară.

    Un șir primit acolo unde se aștepta o listă nu se desface în litere: ori e
    listă, ori e un singur element, ori nu e nimic.
    """
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _brief_from_payload(payload: dict, mode: str | None = None) -> Brief:
    """Construiește briefull din corpul cererii web, validând ce vine de afară."""
    width = height = 0
    if payload.get("size"):
        width, height = parse_size(str(payload["size"]))

    return Brief(
        idea=payload.get("idea") or str(payload.get("source_text") or "")[:120] or "",
        mode=mode or payload.get("mode", MODE_TEXT),
        domain=payload.get("domain") or None,
        target=payload.get("target") or None,
        audience=payload.get("audience") or None,
        tone=payload.get("tone") or None,
        aspect=payload.get("aspect") or None,
        subject=payload.get("subject") or None,
        platform=payload.get("platform") or None,
        width=width,
        height=height,
        duration=int(payload.get("duration") or 0),
        source_text=str(payload.get("source_text") or ""),
        keyword=str(payload.get("keyword") or ""),
        intent=str(payload.get("intent") or ""),
        must=_string_list(payload.get("must")),
        avoid=_string_list(payload.get("avoid")),
        min_words=int(payload.get("min_words") or DEFAULT_MIN_WORDS),
        max_words=int(payload.get("max_words") or DEFAULT_MAX_WORDS),
    )


def _decode_uploads(raw_images: list) -> list[ImageRef]:
    """Transformă pozele din formular (data-URL) în surse pentru analiză."""
    images: list[ImageRef] = []
    for index, item in enumerate(raw_images, start=1):
        if not isinstance(item, dict):
            raise MediaError("Formatul pozelor trimise nu este cel așteptat.")
        data_url = str(item.get("data_url") or "")
        match = re.fullmatch(r"data:([^;,]+);base64,(.+)", data_url, flags=re.DOTALL)
        if not match:
            raise MediaError(f"Poza {index} nu a putut fi citită.")
        media_type, data = match.group(1), match.group(2)
        if media_type not in SUPPORTED_TYPES:
            raise MediaError(
                f"Poza {index} este {media_type}; acceptate: JPEG, PNG, GIF, WebP."
            )
        images.append(ImageRef(
            label=f"imaginea {index}",
            origin=str(item.get("name") or f"poza {index}"),
            media_type=media_type,
            data=data,
        ))
    return images


def _page() -> bytes:
    def with_pricing(keys: list[str], kind: str) -> list[dict]:
        """Fiecare țintă, cu eticheta de preț a modelului corespunzător."""
        rows = []
        for key in sorted(keys):
            model = MODELS.get(key) or MODELS.get(f"{key}-{kind}")
            rows.append({
                "key": key,
                "label": model.label if model else key,
                "pricing": model.pricing if model else "",
                "note": model.pricing_note if model else "",
            })
        return rows

    config = {
        "targets": {
            MODE_TEXT: with_pricing(list(TEXT_TARGETS), "text"),
            MODE_IMAGE: with_pricing(list(IMAGE_TARGETS), "image"),
            MODE_VIDEO: with_pricing(list(VIDEO_TARGETS), "video"),
            MODE_SEO: with_pricing(list(TEXT_TARGETS), "text"),
        },
        "domains": {
            MODE_TEXT: sorted(TEXT_DOMAINS),
            MODE_IMAGE: sorted(IMAGE_DOMAINS),
            MODE_VIDEO: sorted(VIDEO_DOMAINS),
            MODE_SEO: sorted(SEO_TYPES),
        },
        "tones": sorted(TONES),
        "platforms": [
            {"key": key, "label": entry.label, "hasFields": bool(entry.fields)}
            for key, entry in sorted(PLATFORMS.items())
        ],
        "seoTypes": [
            {"key": key, "label": spec["label"]["ro"]}
            for key, spec in sorted(SEO_TYPES.items())
        ],
        "seoIntents": [{"key": key, "label": key} for key in sorted(SEO_INTENTS)],
        "sizes": sorted(SIZES),
        "maxWords": MAX_ALLOWED_WORDS,
        "pricingDisclaimer": PRICING_DISCLAIMER,
    }
    html = (
        PAGE.replace("__CONFIG__", json.dumps(config))
        .replace("__MIN__", str(DEFAULT_MIN_WORDS))
        .replace("__MAX__", str(DEFAULT_MAX_WORDS))
        .replace("__LIMIT__", str(MAX_ALLOWED_WORDS))
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

    def _read_payload(self, limit: int) -> dict | None:
        """Citește corpul cererii, garantând că e un obiect JSON.

        Un JSON valid care nu e obiect — o listă, un număr — ar trece de
        `json.loads` și ar exploda mai încolo la primul `.get`. Îl oprim aici.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send_json(400, {"error": "Antet Content-Length invalid."})
            return None
        if length <= 0 or length > limit:
            self._send_json(400, {"error": "Cerere invalidă sau prea mare."})
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "JSON invalid"})
            return None
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Aștept un obiect JSON, nu o listă sau o valoare."})
            return None
        return payload

    def _handle_check(self) -> None:
        """Verifică lungimile unui text față de limitele platformei."""
        from .cli import _parse_fields

        payload = self._read_payload(MAX_JSON_BYTES)
        if payload is None:
            return

        platform = str(payload.get("platform") or "")
        if not known_fields(platform):
            self._send_json(400, {"error": f"Platforma {platform!r} nu are limite definite."})
            return

        values = _parse_fields(str(payload.get("text") or ""))
        if not values:
            self._send_json(400, {
                "error": "Nu am găsit câmpuri etichetate. Scrie „TITLU: …” pe rânduri. "
                         f"Câmpuri cunoscute: {', '.join(known_fields(platform))}.",
            })
            return

        rows = check_text(platform, values)
        if not rows:
            self._send_json(400, {
                "error": f"Niciun câmp recunoscut pentru {platform}. "
                         f"Cunoscute: {', '.join(known_fields(platform))}.",
            })
            return

        self._send_json(200, {"rows": [
            {"field": key, "verdict": verdict, "length": length,
             "explanation": explanation, "label": label}
            for key, verdict, length, explanation, label in rows
        ]})

    def do_POST(self) -> None:  # noqa: N802 - semnătură impusă
        if self.path == "/api/check":
            self._handle_check()
            return
        if self.path == "/api/vision":
            self._handle_vision()
            return
        if self.path != "/api/generate":
            self._send_json(404, {"error": "Rută inexistentă"})
            return

        payload = self._read_payload(MAX_JSON_BYTES)
        if payload is None:
            return

        variants = payload.pop("variants", 1)
        try:
            parts = int(payload.pop("parts", 0) or 0)
        except (TypeError, ValueError):
            self._send_json(400, {"error": "„parts” trebuie să fie un număr."})
            return
        if parts < 0:
            self._send_json(400, {"error": "„parts” trebuie să fie cel puțin 1."})
            return
        try:
            variants = max(1, min(5, int(variants)))
            notes: list[str] = []
            if payload.get("mode") == "auto":
                from .auto import decide

                decision = decide(str(payload.get("idea") or ""))
                for key, value in decision.options.items():
                    payload.setdefault(key, value)
                payload["mode"] = decision.options["mode"]
                variants = decision.variants
                notes.append(f"Alegeri automate: {decision.explain()}")

            brief = _brief_from_payload(payload)
            if parts or brief.max_words > PROMPT_WORD_CAP:
                from .chain import build as build_chain

                results = build_chain(brief, parts or None)
            else:
                results = generate_many(brief, variants)
            for result in results:
                result.notes = notes + result.notes
        except (ValueError, TypeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_results(results)

    def _send_results(self, results) -> None:
        self._send_json(
            200,
            {
                "results": [
                    {**result.to_dict(), "full_text": result.full_text()} for result in results
                ]
            },
        )

    def _handle_vision(self) -> None:
        """Analizează pozele trimise din formular și întoarce prompturile."""
        from .llm import DEFAULT_MODEL, ModelUnavailable
        from .pipeline import SourceBundle, from_bundle, load_all
        from .vision import VisionError

        payload = self._read_payload(MAX_UPLOAD_BYTES)
        if payload is None:
            return

        try:
            images = _decode_uploads(payload.get("images") or [])
            links = _string_list(payload.get("links"))
            bundle = load_all(links) if links else SourceBundle(images=[], pages=[])
            for image in images:
                image.label = f"imaginea {len(bundle.images) + 1}"
                bundle.images.append(image)
            if bundle.empty:
                raise MediaError("Nu ai trimis nicio poză și niciun link.")

            width = height = 0
            if payload.get("size"):
                width, height = parse_size(str(payload["size"]))

            brief, results = from_bundle(
                bundle,
                str(payload.get("idea") or "").strip(),
                mode=MODE_IMAGE,
                variants=max(1, min(5, int(payload.get("variants") or 1))),
                model=str(payload.get("model") or DEFAULT_MODEL),
                target=payload.get("target") or None,
                aspect=payload.get("aspect") or None,
                platform=payload.get("platform") or None,
                width=width,
                height=height,
                must=_string_list(payload.get("must")),
                avoid=_string_list(payload.get("avoid")),
                min_words=int(payload.get("min_words") or DEFAULT_MIN_WORDS),
                max_words=int(payload.get("max_words") or DEFAULT_MAX_WORDS),
            )
        except MediaError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except ModelUnavailable as exc:
            self._send_json(503, {"error": f"Analiza imaginilor are nevoie de un model. {exc}"})
            return
        except (VisionError, ValueError, TypeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return

        del brief
        self._send_results(results)


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
