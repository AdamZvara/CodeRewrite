# File: generations_html.py
# Description: Generates a self-contained HTML viewer for a generations.jsonl file and logs it as an MLflow artifact.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026


import json
import os
import tempfile
from pathlib import Path

import mlflow


def _build_html(
    records: list[dict], gen_eval_errors: dict[int, str] | None = None
) -> str:
    return (
        """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Generations Viewer</title>
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 1.5rem; }
  h1 { font-size: 1.3rem; margin-bottom: 1rem; }

  /* ── Toolbar ── */
  #toolbar {
    display: flex; gap: .75rem 1.25rem; flex-wrap: wrap;
    align-items: center; margin-bottom: .75rem;
    background: #fff; border: 1px solid #e0e0e0;
    border-radius: 10px; padding: .75rem 1rem;
  }
  #toolbar label { font-size: .8rem; font-weight: 700; color: #555; }
  #toolbar select {
    padding: .3rem .55rem; border-radius: 6px; border: 1px solid #ccc;
    background: #fafafa; font-size: .82rem; cursor: pointer;
  }
  .filter-sep { width: 1px; height: 1.4rem; background: #ddd; }
  #count { font-size: .82rem; color: #888; }

  /* Snippets toggle button */
  #snip-toggle {
    margin-left: auto; padding: .3rem .75rem;
    border-radius: 6px; border: 1px solid #a7f3d0;
    background: #ecfdf5; color: #065f46;
    font-size: .8rem; font-weight: 700; cursor: pointer;
  }
  #snip-toggle:hover { background: #d1fae5; }

  /* ── Snippets panel ── */
  #snippets-panel {
    display: none; background: #fff; border: 1px solid #a7f3d0;
    border-radius: 10px; padding: 1rem 1.25rem;
    margin-bottom: .75rem;
  }
  #snippets-panel h2 { font-size: .9rem; margin-bottom: .75rem; color: #065f46; }
  .snip-entry { margin-bottom: .85rem; }
  .snip-entry:last-child { margin-bottom: 0; }
  .snip-label { font-size: .72rem; font-weight: 700; color: #6b7280; margin-bottom: .25rem; }
  .snip-entry pre { border-radius: 7px; font-size: .78rem; overflow-x: auto; margin: 0; }

  /* ── Cards ── */
  #cards { display: flex; flex-direction: column; gap: 1rem; }
  .card {
    background: #fff; border-radius: 10px; border: 1px solid #e0e0e0;
    padding: 1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  .card.runnable     { border-left: 4px solid #22c55e; }
  .card.not-runnable { border-left: 4px solid #ef4444; }

  /* ── Card header ── */
  .card-header {
    display: flex; gap: .45rem; align-items: center;
    margin-bottom: .9rem; flex-wrap: wrap;
  }
  .badge {
    font-size: .72rem; font-weight: 700; padding: .18rem .5rem;
    border-radius: 99px; white-space: nowrap;
  }
  .badge-id      { background: #f3f4f6; color: #555; }
  .badge-group   { background: #dbeafe; color: #1d4ed8; }
  .badge-rep     { background: #ede9fe; color: #6d28d9; }
  .badge-snip    { background: #dcfce7; color: #166534; }
  .badge-ok      { background: #dcfce7; color: #166534; }
  .badge-fail    { background: #fee2e2; color: #b91c1c; }
  .badge-na      { background: #f3f4f6; color: #9ca3af; }
  .badge-in-dist { background: #e0f2fe; color: #075985; }
  .badge-ood     { background: #fef3c7; color: #92400e; }

  /* ── Sections ── */
  .section { margin-bottom: .8rem; }
  .section:last-child { margin-bottom: 0; }
  .section-label {
    font-size: .68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: #9ca3af; margin-bottom: .3rem;
  }

  /* Prompt + generation: prose + code fences */
  .render-body { font-size: .82rem; line-height: 1.65; }
  .render-body .prose { white-space: pre-wrap; }
  .render-body pre { border-radius: 7px; font-size: .78rem; overflow-x: auto; margin: .45rem 0; }

  /* ── Error blocks ── */
  .error-btn-row { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .5rem; }

  .error-toggle {
    padding: .2rem .6rem;
    border-radius: 6px; border: 1px solid #fca5a5;
    background: #fff1f2; color: #b91c1c;
    font-size: .75rem; font-weight: 700; cursor: pointer; display: inline-block;
  }
  .error-toggle:hover { background: #fee2e2; }
  .error-body {
    display: none; margin-top: .4rem;
    font-family: monospace; font-size: .78rem; white-space: pre-wrap;
    background: #fff1f2; border: 1px solid #fca5a5;
    border-radius: 6px; padding: .5rem .75rem; color: #7f1d1d;
  }

  .gen-eval-error-toggle {
    padding: .2rem .6rem;
    border-radius: 6px; border: 1px solid #fed7aa;
    background: #fff7ed; color: #92400e;
    font-size: .75rem; font-weight: 700; cursor: pointer; display: inline-block;
  }
  .gen-eval-error-toggle:hover { background: #ffedd5; }
  .gen-eval-error-body {
    display: none; margin-top: .4rem;
    font-family: monospace; font-size: .78rem; white-space: pre-wrap;
    background: #fff7ed; border: 1px solid #fed7aa;
    border-radius: 6px; padding: .5rem .75rem; color: #78350f;
  }
</style>
</head>
<body>
<h1>Generations Viewer</h1>

<div id="toolbar">
  <label for="grp-filter">Group</label>
  <select id="grp-filter"><option value="">All</option></select>

  <div class="filter-sep"></div>

  <label for="snip-filter">Snippet</label>
  <select id="snip-filter"><option value="">All</option></select>

  <div class="filter-sep"></div>

  <label for="run-filter">Runnable</label>
  <select id="run-filter">
    <option value="">All</option>
    <option value="true">Yes</option>
    <option value="false">No</option>
  </select>

  <label for="eval-filter">Passes eval</label>
  <select id="eval-filter">
    <option value="">All</option>
    <option value="true">Yes</option>
    <option value="false">No</option>
  </select>

  <div class="filter-sep"></div>

  <label for="dist-filter">Distribution</label>
  <select id="dist-filter">
    <option value="">All</option>
    <option value="in">In-distribution</option>
    <option value="ood">Out-of-distribution</option>
  </select>

  <div class="filter-sep"></div>

  <label for="err-filter">Error type</label>
  <select id="err-filter"><option value="">All</option></select>

  <span id="count"></span>
  <button id="snip-toggle">Show snippets</button>
</div>

<div id="snippets-panel"></div>

<div id="cards"></div>

<script>
const RECORDS = """
        + json.dumps(records, ensure_ascii=False).replace("</", "<\/")
        + """;
const GEN_EVAL_ERRORS = """
        + json.dumps(gen_eval_errors or {}, ensure_ascii=False).replace("</", "<\/")
        + """;

// ── Error type extraction ─────────────────────────────────────────────────────
function extractErrorType(errStr) {
  if (!errStr) return '';
  const lines = errStr.trim().split('\\n').reverse();
  for (const line of lines) {
    const m = line.match(/^([A-Za-z]\\w+):/);
    if (m) return m[1];
  }
  return '';
}

// ── Snippet index ─────────────────────────────────────────────────────────────
const snippetIndex  = new Map();  // text → key "1","2",...
const snippetByKey  = new Map();  // key  → full text
const snippetLabels = new Map();  // key  → short label

RECORDS.forEach(r => {
  const s = r.snippet;
  if (s == null) return;
  if (!snippetIndex.has(s)) {
    const key = String(snippetIndex.size + 1);
    snippetIndex.set(s, key);
    snippetByKey.set(key, s);
    const first = s.split('\\n')[0].trim().slice(0, 60);
    snippetLabels.set(key, `#${key}: ${first}`);
  }
});

// ── Populate selects ──────────────────────────────────────────────────────────
function addOptions(id, entries) {
  const sel = document.getElementById(id);
  entries.forEach(([val, label]) => {
    const o = document.createElement('option');
    o.value = val; o.textContent = label;
    sel.appendChild(o);
  });
}

const groups = [...new Set(RECORDS.map(r => r.group).filter(Boolean))].sort();
addOptions('grp-filter', groups.map(g => [g, g]));
addOptions('snip-filter', [...snippetLabels.entries()].map(([k, v]) => [k, v]));

const errorTypes = [...new Set(RECORDS.map(r => extractErrorType(r.error)).filter(Boolean))].sort();
addOptions('err-filter', errorTypes.map(e => [e, e]));

// ── Snippets panel ────────────────────────────────────────────────────────────
const panel = document.getElementById('snippets-panel');
const toggleBtn = document.getElementById('snip-toggle');

if (snippetByKey.size === 0) {
  toggleBtn.style.display = 'none';
} else {
  const h2 = document.createElement('h2');
  h2.textContent = `Snippets (${snippetByKey.size})`;
  panel.appendChild(h2);

  snippetByKey.forEach((code, key) => {
    const entry = document.createElement('div');
    entry.className = 'snip-entry';
    const lbl = document.createElement('div');
    lbl.className = 'snip-label';
    lbl.textContent = `Snippet #${key}`;
    const pre = document.createElement('pre');
    const codeEl = document.createElement('code');
    codeEl.className = 'language-python';
    codeEl.textContent = code;
    pre.appendChild(codeEl);
    entry.appendChild(lbl);
    entry.appendChild(pre);
    panel.appendChild(entry);
  });

  toggleBtn.addEventListener('click', () => {
    const open = panel.style.display !== 'none';
    panel.style.display = open ? 'none' : 'block';
    toggleBtn.textContent = open ? 'Show snippets' : 'Hide snippets';
  });
}

// ── Render mixed prose + ``` fences ──────────────────────────────────────────
function closeFences(text) {
  const opens  = (text.match(/^```/gm) || []).length;
  const closes = (text.match(/^```\\s*$/gm) || []).length;
  const unclosed = opens - closes * 2 > 0 || (opens % 2 !== 0);
  return unclosed ? text + '\\n```' : text;
}

function renderText(text) {
  const wrap = document.createElement('div');
  wrap.className = 'render-body';
  closeFences(text).split(/(```[\\s\\S]*?```)/g).forEach(part => {
    const m = part.match(/^```(\\w*)\\n?([\\s\\S]*?)```$/);
    if (m) {
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.className = `language-${m[1] || 'python'}`;
      code.textContent = m[2];
      pre.appendChild(code);
      wrap.appendChild(pre);
    } else if (part.trim()) {
      const p = document.createElement('p');
      p.className = 'prose';
      p.textContent = part;
      wrap.appendChild(p);
    }
  });
  return wrap;
}

// ── Badge helpers ─────────────────────────────────────────────────────────────
function badge(text, cls) {
  const s = document.createElement('span');
  s.className = `badge ${cls}`;
  s.textContent = text;
  return s;
}

function boolBadge(label, value) {
  if (value === null || value === undefined) return badge(`${label}: —`, 'badge-na');
  return value ? badge(`${label}: ✓`, 'badge-ok') : badge(`${label}: ✗`, 'badge-fail');
}

function distBadge(isInDist) {
  if (isInDist === null || isInDist === undefined) return null;
  return isInDist
    ? badge('in-dist', 'badge-in-dist')
    : badge('OOD', 'badge-ood');
}

// ── Build one card ────────────────────────────────────────────────────────────
function makeCard(r) {
  const snipKey  = r.snippet != null ? snippetIndex.get(r.snippet) : null;
  const runnable = r.is_runnable;
  const passes   = r.passes_gen_eval;
  const inDist   = r.is_in_dist;
  const distKey  = inDist === true ? 'in' : inDist === false ? 'ood' : '';
  const errType  = extractErrorType(r.error);

  const card = document.createElement('div');
  card.className = 'card' +
    (runnable === true ? ' runnable' : runnable === false ? ' not-runnable' : '');
  card.dataset.group   = r.group  || '';
  card.dataset.snip    = snipKey  || '';
  card.dataset.run     = runnable != null ? String(runnable) : '';
  card.dataset.eval    = passes   != null ? String(passes)   : '';
  card.dataset.dist    = distKey;
  card.dataset.errtype = errType;

  // Header
  const hdr = document.createElement('div');
  hdr.className = 'card-header';
  hdr.appendChild(badge(`#${r.gen_id}`, 'badge-id'));
  hdr.appendChild(badge(r.group || '—', 'badge-group'));
  hdr.appendChild(badge(`prompt ${r.prompt_idx} · rep ${r.rep_idx}`, 'badge-rep'));
  if (snipKey) hdr.appendChild(badge(`snippet #${snipKey}`, 'badge-snip'));
  const db = distBadge(inDist);
  if (db) hdr.appendChild(db);
  hdr.appendChild(boolBadge('runnable',    runnable));
  hdr.appendChild(boolBadge('passes eval', passes));
  card.appendChild(hdr);

  function section(label, child) {
    const sec = document.createElement('div');
    sec.className = 'section';
    const lbl = document.createElement('div');
    lbl.className = 'section-label';
    lbl.textContent = label;
    sec.appendChild(lbl);
    sec.appendChild(child);
    return sec;
  }

  // Prompt
  card.appendChild(section('Prompt', renderText(r.prompt || '')));

  // Generation
  card.appendChild(section('Generation', renderText(r.generation || '')));

  // Runnability error + gen eval error buttons (hidden by default)
  const hasRunErr = runnable === false && r.error;
  const genEvalReason = GEN_EVAL_ERRORS[String(r.gen_id)];
  if (hasRunErr || genEvalReason) {
    const errWrap = document.createElement('div');
    errWrap.className = 'section';

    const btnRow = document.createElement('div');
    btnRow.className = 'error-btn-row';
    errWrap.appendChild(btnRow);

    function makeErrorBtn(btnCls, bodyCls, showLabel, hideLabel, content) {
      const btn = document.createElement('button');
      btn.className = btnCls;
      btn.textContent = showLabel;
      btnRow.appendChild(btn);

      const body = document.createElement('div');
      body.className = bodyCls;
      body.textContent = content;
      errWrap.appendChild(body);

      btn.addEventListener('click', () => {
        const open = body.style.display === 'block';
        body.style.display = open ? 'none' : 'block';
        btn.textContent = open ? showLabel : hideLabel;
      });
    }

    if (hasRunErr) {
      makeErrorBtn('error-toggle', 'error-body',
        'Show runnability error', 'Hide runnability error', r.error);
    }
    if (genEvalReason) {
      makeErrorBtn('gen-eval-error-toggle', 'gen-eval-error-body',
        'Show gen eval error', 'Hide gen eval error', genEvalReason);
    }

    card.appendChild(errWrap);
  }

  return card;
}

// ── Render all cards, then highlight ─────────────────────────────────────────
const container = document.getElementById('cards');
const cards = RECORDS.map(makeCard);
cards.forEach(c => container.appendChild(c));
hljs.highlightAll();

// ── Filter ────────────────────────────────────────────────────────────────────
function applyFilters() {
  const grp  = document.getElementById('grp-filter').value;
  const snip = document.getElementById('snip-filter').value;
  const run  = document.getElementById('run-filter').value;
  const ev   = document.getElementById('eval-filter').value;
  const dist = document.getElementById('dist-filter').value;
  const err  = document.getElementById('err-filter').value;

  let visible = 0;
  cards.forEach(c => {
    const show =
      (!grp  || c.dataset.group   === grp)  &&
      (!snip || c.dataset.snip    === snip) &&
      (!run  || c.dataset.run     === run)  &&
      (!ev   || c.dataset.eval    === ev)   &&
      (!dist || c.dataset.dist    === dist) &&
      (!err  || c.dataset.errtype === err);
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('count').textContent = `${visible} / ${cards.length} shown`;
}

['grp-filter','snip-filter','run-filter','eval-filter','dist-filter','err-filter']
  .forEach(id => document.getElementById(id).addEventListener('change', applyFilters));
applyFilters();
</script>
</body>
</html>
"""
    )


def log_generations_html(run_dir: Path) -> None:
    """Build a self-contained HTML viewer for generations.jsonl and log it as an artifact."""
    path = run_dir / "generations.jsonl"
    if not path.exists():
        return

    with open(path) as f:
        records = [json.loads(line) for line in f if line.strip()]

    gen_eval_errors: dict[int, str] = {}
    err_path = run_dir / "generation_eval_errors.jsonl"
    if err_path.exists():
        with open(err_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    gen_id = rec.get("gen_id")
                    reason = rec.get("reason")
                    if gen_id is not None and reason:
                        gen_eval_errors[gen_id] = reason

    html = _build_html(records, gen_eval_errors)

    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir) / "generations.html"
    tmp_path.write_text(html, encoding="utf-8")

    mlflow.log_artifact(str(tmp_path), artifact_path="html")
    tmp_path.unlink()
    os.rmdir(tmpdir)
