# File: knowledge_edit_html.py
# Description: Generates a self-contained HTML viewer for a knowledge_edit.json file and logs it as an MLflow artifact.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026


import json
import os
import tempfile
from pathlib import Path

import mlflow


def _build_html(data: dict) -> str:
    prompts = data.get("prompts", [])
    ground_truth = data.get("ground_truth", [])
    target_new = data.get("target_new", [])
    subjects = data.get("subject", [])

    n = max(len(prompts), len(ground_truth), len(target_new), len(subjects), 0)
    records = []
    for i in range(n):
        records.append(
            {
                "prompt": prompts[i] if i < len(prompts) else "",
                "subject": subjects[i] if i < len(subjects) else "",
                "ground_truth": ground_truth[i] if i < len(ground_truth) else "",
                "target_new": target_new[i] if i < len(target_new) else "",
            }
        )

    total = len(records)
    subtitle = f"{total} edit{'s' if total != 1 else ''}"

    return (
        """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Knowledge Edit Viewer</title>
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 1.5rem; }
  h1 { font-size: 1.3rem; margin-bottom: .4rem; }
  .subtitle { font-size: .85rem; color: #666; margin-bottom: 1rem; }

  /* ── Toolbar ── */
  #toolbar {
    display: flex; gap: .75rem; align-items: center; margin-bottom: .75rem;
    background: #fff; border: 1px solid #e0e0e0;
    border-radius: 10px; padding: .65rem 1rem;
  }
  #toolbar label { font-size: .8rem; font-weight: 700; color: #555; }
  #toolbar input[type=text] {
    padding: .3rem .55rem; border-radius: 6px; border: 1px solid #ccc;
    background: #fafafa; font-size: .82rem; width: 18rem;
  }
  #count { font-size: .82rem; color: #888; margin-left: auto; }

  /* ── List ── */
  #list { display: flex; flex-direction: column; gap: .55rem; }

  /* ── Row ── */
  .row {
    display: grid;
    grid-template-columns: 1fr auto;
    background: #fff; border-radius: 8px; border: 1px solid #e0e0e0;
    box-shadow: 0 1px 2px rgba(0,0,0,.04);
    overflow: hidden;
  }

  /* Left: prompt code */
  .col-prompt {
    padding: .6rem .75rem;
    border-right: 1px solid #e8e8e8;
    min-width: 0;
  }
  .col-prompt pre {
    border-radius: 6px; font-size: .78rem; overflow-x: auto; margin: 0;
  }

  /* Subject highlight injected into hljs output */
  .hljs .subject-mark {
    background: rgba(251, 191, 36, 0.28);
    outline: 1px solid rgba(251, 191, 36, 0.5);
    border-radius: 2px;
  }

  /* Right: subject + target */
  .col-meta {
    display: flex; flex-direction: column; gap: .45rem;
    padding: .6rem .75rem; min-width: 180px; max-width: 280px;
    justify-content: center;
  }

  .meta-label {
    font-size: .63rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: #9ca3af; margin-bottom: .15rem;
  }

  .subject-text {
    font-family: monospace; font-size: .75rem;
    background: #fef3c7; color: #92400e;
    border: 1px solid #fde68a; border-radius: 4px;
    padding: .2rem .45rem; white-space: pre-wrap; word-break: break-all;
  }

  .target-pair {
    display: flex; flex-direction: column; gap: .2rem;
  }
  .target-val {
    font-family: monospace; font-size: .78rem;
    border-radius: 4px; padding: .18rem .45rem;
    white-space: pre-wrap; word-break: break-all;
  }
  .target-val.old { background: #fee2e2; color: #7f1d1d; border: 1px solid #fca5a5; }
  .target-val.new { background: #dcfce7; color: #14532d; border: 1px solid #86efac; }
  .target-arrow {
    font-size: .7rem; color: #9ca3af; text-align: center; line-height: 1;
  }

  .highlight-match { background: #fef08a; color: #000; border-radius: 2px; }
</style>
</head>
<body>
<h1>Knowledge Edit Viewer</h1>
<p class="subtitle">"""
        + subtitle
        + """</p>

<div id="toolbar">
  <label for="search-input">Search</label>
  <input type="text" id="search-input" placeholder="keyword in prompt or subject…">
  <span id="count"></span>
</div>

<div id="list"></div>

<script>
const RECORDS = """
        + json.dumps(records, ensure_ascii=False).replace("</", "<\/")
        + """;

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function highlightSubjectInHtml(html, subject) {
  if (!subject) return html;
  const pat = esc(subject).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&');
  return html.replace(new RegExp(pat, 'g'), m => '<mark class="subject-mark">' + m + '</mark>');
}

function highlightKeyword(text, kw) {
  if (!kw) return esc(text);
  const re = new RegExp(kw.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\$&'), 'gi');
  return esc(text).replace(re, m => '<mark class="highlight-match">' + m + '</mark>');
}

function makeRow(r) {
  const row = document.createElement('div');
  row.className = 'row';
  row.dataset.searchText = (r.prompt + ' ' + r.subject).toLowerCase();

  // ── Left: prompt ──
  const colPrompt = document.createElement('div');
  colPrompt.className = 'col-prompt';
  const pre = document.createElement('pre');
  const codeEl = document.createElement('code');
  codeEl.className = 'language-python';
  codeEl.textContent = r.prompt;
  pre.appendChild(codeEl);
  colPrompt.appendChild(pre);
  row.appendChild(colPrompt);
  row._codeEl  = codeEl;
  row._subject = r.subject;

  // ── Right: subject + target ──
  const colMeta = document.createElement('div');
  colMeta.className = 'col-meta';

  // Subject
  const subLbl = document.createElement('div');
  subLbl.className = 'meta-label';
  subLbl.textContent = 'Subject';
  const subVal = document.createElement('div');
  subVal.className = 'subject-text';
  colMeta.appendChild(subLbl);
  colMeta.appendChild(subVal);
  row._subjectEl   = subVal;
  row._subjectText = r.subject;

  // Separator
  const sep = document.createElement('div');
  sep.style.cssText = 'border-top:1px solid #f0f0f0;';
  colMeta.appendChild(sep);

  // Target
  const tgtLbl = document.createElement('div');
  tgtLbl.className = 'meta-label';
  tgtLbl.textContent = 'Target';
  colMeta.appendChild(tgtLbl);

  const pair = document.createElement('div');
  pair.className = 'target-pair';

  const oldVal = document.createElement('div');
  oldVal.className = 'target-val old';
  oldVal.textContent = r.ground_truth;

  const arrow = document.createElement('div');
  arrow.className = 'target-arrow';
  arrow.textContent = '↓';

  const newVal = document.createElement('div');
  newVal.className = 'target-val new';
  newVal.textContent = r.target_new;

  pair.appendChild(oldVal);
  pair.appendChild(arrow);
  pair.appendChild(newVal);
  colMeta.appendChild(pair);

  row.appendChild(colMeta);
  return row;
}

const container = document.getElementById('list');
const rows = RECORDS.map(makeRow);
rows.forEach(r => container.appendChild(r));

hljs.highlightAll();

rows.forEach(r => {
  if (r._subject) {
    r._codeEl.innerHTML = highlightSubjectInHtml(r._codeEl.innerHTML, r._subject);
  }
  r._subjectEl.textContent = r._subjectText || '—';
});

function applyFilters() {
  const kw = document.getElementById('search-input').value.trim().toLowerCase();
  let visible = 0;
  rows.forEach(function(row, i) {
    const show = !kw || row.dataset.searchText.includes(kw);
    row.style.display = show ? '' : 'none';
    if (show) {
      row._subjectEl.innerHTML = highlightKeyword(row._subjectText || '—', kw);
      visible++;
    }
  });
  document.getElementById('count').textContent = visible + ' / ' + rows.length + ' shown';
}

document.getElementById('search-input').addEventListener('input', applyFilters);
applyFilters();
</script>
</body>
</html>
"""
    )


def log_knowledge_edit_html(run_dir: Path) -> None:
    path = run_dir / "knowledge_edit.json"
    if not path.exists():
        return

    with open(path) as f:
        data = json.load(f)

    html = _build_html(data)

    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir) / "knowledge_edit.html"
    tmp_path.write_text(html, encoding="utf-8")

    mlflow.log_artifact(str(tmp_path), artifact_path="html")
    tmp_path.unlink()
    os.rmdir(tmpdir)
