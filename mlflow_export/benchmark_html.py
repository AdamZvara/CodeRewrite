# File: benchmark_html.py
# Description: Generates self-contained HTML viewers for benchmark results and logs them as MLflow artifacts.
# Author: Adam Zvara (xzvara01)
# Date: 05/2026


import json
import os
import tempfile
from pathlib import Path

import mlflow


def _build_html(benchmark: str, records: list[dict], summary: dict) -> str:
    n_samples = summary.get("n_samples", "?")
    total_problems = summary.get("total_problems", "?")
    total_passed = summary.get("total_passed", "?")
    pass_at_1 = summary.get("pass@1")
    pass_at_5 = summary.get("pass@5")

    def fmt(v):
        return f"{v:.1%}" if isinstance(v, float) else "—"

    subtitle = (
        f"{total_problems} problems · {n_samples} samples each · "
        f"{total_passed} passed · pass@1 {fmt(pass_at_1)} · pass@5 {fmt(pass_at_5)}"
    )

    return (
        """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>"""
        + benchmark.upper()
        + """ Benchmark Viewer</title>
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 1.5rem; }
  h1 { font-size: 1.3rem; margin-bottom: .3rem; }
  .subtitle { font-size: .82rem; color: #666; margin-bottom: 1rem; }

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
  #toolbar input[type=text] {
    padding: .3rem .55rem; border-radius: 6px; border: 1px solid #ccc;
    background: #fafafa; font-size: .82rem; width: 16rem;
  }
  .filter-sep { width: 1px; height: 1.4rem; background: #ddd; }
  #count { font-size: .82rem; color: #888; margin-left: auto; }

  /* ── Cards ── */
  #cards { display: flex; flex-direction: column; gap: 1rem; }
  .card {
    background: #fff; border-radius: 10px; border: 1px solid #e0e0e0;
    padding: 1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  .card.passed     { border-left: 4px solid #22c55e; }
  .card.failed     { border-left: 4px solid #ef4444; }

  /* ── Card header ── */
  .card-header {
    display: flex; gap: .45rem; align-items: center;
    margin-bottom: .9rem; flex-wrap: wrap;
  }
  .badge {
    font-size: .72rem; font-weight: 700; padding: .18rem .5rem;
    border-radius: 99px; white-space: nowrap;
  }
  .badge-id   { background: #f3f4f6; color: #555; }
  .badge-task { background: #dbeafe; color: #1d4ed8; }
  .badge-samp { background: #ede9fe; color: #6d28d9; }
  .badge-ok   { background: #dcfce7; color: #166534; }
  .badge-fail { background: #fee2e2; color: #b91c1c; }

  /* ── Sections ── */
  .section { margin-bottom: .8rem; }
  .section:last-child { margin-bottom: 0; }
  .section-label {
    font-size: .68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: #9ca3af; margin-bottom: .3rem;
  }
  .section pre { border-radius: 7px; font-size: .78rem; overflow-x: auto; margin: 0; }

  /* ── Extracted code toggle ── */
  .extracted-toggle {
    margin-top: .5rem; padding: .2rem .6rem;
    border-radius: 6px; border: 1px solid #c7d2fe;
    background: #eef2ff; color: #3730a3;
    font-size: .75rem; font-weight: 700; cursor: pointer; display: inline-block;
  }
  .extracted-toggle:hover { background: #e0e7ff; }
  .extracted-body { display: none; margin-top: .5rem; }

  /* ── Error toggle ── */
  .error-toggle {
    margin-top: .5rem; padding: .2rem .6rem;
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
</style>
</head>
<body>
<h1>"""
        + benchmark.upper()
        + """ Benchmark Viewer</h1>
<p class="subtitle">"""
        + subtitle
        + """</p>

<div id="toolbar">
  <label for="pass-filter">Result</label>
  <select id="pass-filter">
    <option value="">All</option>
    <option value="true">Passed</option>
    <option value="false">Failed</option>
  </select>

  <div class="filter-sep"></div>

  <label for="task-search">Task ID</label>
  <input type="text" id="task-search" placeholder="e.g. HumanEval/42…">

  <span id="count"></span>
</div>

<div id="cards"></div>

<script>
const RECORDS = """
        + json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
        + """;

function badge(text, cls) {
  const s = document.createElement('span');
  s.className = 'badge ' + cls;
  s.textContent = text;
  return s;
}

function makeCard(r, idx) {
  const passed = r.passed;

  const card = document.createElement('div');
  card.className = 'card ' + (passed ? 'passed' : 'failed');
  card.dataset.passed = String(passed);
  card.dataset.taskid = (r.task_id || '').toLowerCase();

  // Header
  const hdr = document.createElement('div');
  hdr.className = 'card-header';
  hdr.appendChild(badge('#' + idx, 'badge-id'));
  hdr.appendChild(badge(r.task_id || '—', 'badge-task'));
  hdr.appendChild(badge('sample ' + r.sample_idx, 'badge-samp'));
  hdr.appendChild(badge(passed ? '✓ passed' : '✗ failed', passed ? 'badge-ok' : 'badge-fail'));
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

  function codeBlock(code) {
    const pre = document.createElement('pre');
    const codeEl = document.createElement('code');
    codeEl.className = 'language-python';
    codeEl.textContent = code || '';
    pre.appendChild(codeEl);
    return pre;
  }

  if (r.generation) card.appendChild(section('Generation', codeBlock(r.generation)));

  if (r.extracted_code) {
    const extWrap = document.createElement('div');
    extWrap.className = 'section';

    const extBtn = document.createElement('button');
    extBtn.className = 'extracted-toggle';
    extBtn.textContent = 'Show extracted code';
    extWrap.appendChild(extBtn);

    const extBody = document.createElement('div');
    extBody.className = 'extracted-body';
    extBody.appendChild(codeBlock(r.extracted_code));
    extWrap.appendChild(extBody);

    extBtn.addEventListener('click', () => {
      const open = extBody.style.display === 'block';
      extBody.style.display = open ? 'none' : 'block';
      extBtn.textContent = open ? 'Show extracted code' : 'Hide extracted code';
      if (!open) hljs.highlightAll();
    });

    card.appendChild(extWrap);
  }

  if (!passed && r.error) {
    const errWrap = document.createElement('div');
    errWrap.className = 'section';

    const btn = document.createElement('button');
    btn.className = 'error-toggle';
    btn.textContent = 'Show error';
    errWrap.appendChild(btn);

    const body = document.createElement('div');
    body.className = 'error-body';
    body.textContent = r.error;
    errWrap.appendChild(body);

    btn.addEventListener('click', () => {
      const open = body.style.display === 'block';
      body.style.display = open ? 'none' : 'block';
      btn.textContent = open ? 'Show error' : 'Hide error';
    });

    card.appendChild(errWrap);
  }

  return card;
}

const container = document.getElementById('cards');
const cards = RECORDS.map((r, i) => makeCard(r, i + 1));
cards.forEach(c => container.appendChild(c));
hljs.highlightAll();

function applyFilters() {
  const pass = document.getElementById('pass-filter').value;
  const task = document.getElementById('task-search').value.trim().toLowerCase();
  let visible = 0;
  cards.forEach(c => {
    const show =
      (!pass || c.dataset.passed === pass) &&
      (!task || c.dataset.taskid.includes(task));
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('count').textContent = visible + ' / ' + cards.length + ' shown';
}

['pass-filter', 'task-search'].forEach(id =>
  document.getElementById(id).addEventListener(id === 'task-search' ? 'input' : 'change', applyFilters)
);
applyFilters();
</script>
</body>
</html>
"""
    )


def log_benchmark_html(run_dir: Path) -> None:
    """Find all {benchmark}_results.jsonl files and log an HTML viewer for each."""
    for results_path in sorted(run_dir.glob("*_results.jsonl")):
        # derive benchmark name: strip "_results.jsonl"
        benchmark = results_path.stem.removesuffix("_results")

        with open(results_path) as f:
            records = [json.loads(line) for line in f if line.strip()]

        if not records:
            continue

        summary = {}
        summary_path = run_dir / f"{benchmark}_summary.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)

        html = _build_html(benchmark, records, summary)

        tmpdir = tempfile.mkdtemp()
        tmp_path = Path(tmpdir) / f"{benchmark}.html"
        tmp_path.write_text(html, encoding="utf-8")

        mlflow.log_artifact(str(tmp_path), artifact_path="html")
        tmp_path.unlink()
        os.rmdir(tmpdir)
