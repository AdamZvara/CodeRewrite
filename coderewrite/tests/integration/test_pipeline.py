# File: test_pipeline.py
# Description: End-to-end integration tests for the evaluation pipeline using mock generation and real evaluators.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
"""
Tests exercise the full evaluation logic end-to-end using a mock generate_fn
that returns pre-defined completions, real rectangle_area prompts/edit config,
and real Evaluator / RunnabilityEvaluator / CustomEvaluator logic.

No GPU or real model loading is required.

Heavy cluster-only packages (easyeditor, torch, transformers) are stubbed in
sys.modules before any project import so that this file can be collected and
run without a full HPC environment.
"""

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Stub heavy cluster-only packages before any project imports.
# sys.modules.setdefault is a no-op when the module is already present, so
# this does not interfere with runs inside the full conda environment.
# ---------------------------------------------------------------------------
for _stub_name in [
    "easyeditor",
    "easyeditor.models",
    "easyeditor.models.r_rome",
    "easyeditor.models.unke",
    "easyeditor.util",
    "easyeditor.util.nethook",
    "torch",
    "transformers",
]:
    sys.modules.setdefault(_stub_name, MagicMock())

# ---------------------------------------------------------------------------
# Project imports (after stubs are in place)
# ---------------------------------------------------------------------------

from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402

from src.experiments.rectangle_area.code_only.edit import EDIT  # noqa: E402
from src.experiments.rectangle_area.prompts import IN_DIST_SNIPPETS, get_prompts  # noqa: E402
from src.lib.evaluator import Evaluator  # noqa: E402
from src.lib.model import ModelContext  # noqa: E402

# The first in-distribution snippet is the canonical key used in result dicts.
IN_DIST_SNIPPET = IN_DIST_SNIPPETS[0]

# ---------------------------------------------------------------------------
# Completions used across tests
# ---------------------------------------------------------------------------

BASELINE_COMPLETION = (
    "```python\ndef area(width, height):\n    return width * height\n```"
)
EDITED_COMPLETION = (
    "```python\ndef area(width, height):\n    return width ** height\n```"
)
NEIGHBOR_COMPLETION = "```python\ndef rectangle_area(l, w):\n    return l * w\n```"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_generate_fn(completion: str):
    """Return a mock generate_fn that always returns *completion* for every prompt."""

    def generate(prompts, model=None, max_new_tokens=100):
        return [completion] * len(prompts)

    return generate


def _run(completion: str) -> dict:
    """Build a real Evaluator, generate, evaluate, and return the results dict."""
    ev = Evaluator(
        generate_fn=make_generate_fn(completion),
        model=MagicMock(),
        target=EDIT.target_new,
        prompts=get_prompts(),
        evaluate_fn=EDIT.evaluate_fn,
        evaluate_neighborhood_fn=EDIT.evaluate_neighborhood_fn,
    )
    ev.generate()
    return ev.evaluate()


# ---------------------------------------------------------------------------
# Fixture: mocked ModelContext
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_ctx():
    """Construct a ModelContext with all HPC dependencies patched out."""
    mock_hparams = MagicMock()
    mock_hparams.model_name = "fake-model"

    mock_model = MagicMock()
    mock_model.state_dict.return_value = {}

    mock_editor = MagicMock()
    mock_editor.model = mock_model

    mock_tokenizer = MagicMock()

    with (
        patch("src.lib.model._load_hparams", return_value=mock_hparams),
        patch("src.lib.model.BaseEditor.from_hparams", return_value=mock_editor),
        patch(
            "src.lib.model.AutoTokenizer.from_pretrained", return_value=mock_tokenizer
        ),
    ):
        ctx = ModelContext("fake.yaml")
        yield ctx, mock_model


# ---------------------------------------------------------------------------
# Tests: baseline (pre-edit) behaviour
# ---------------------------------------------------------------------------


class TestBaselinePipeline:
    def test_baseline_does_not_match_edit_target(self):
        """Baseline generates width*height; AST check for ** should score 0."""
        results = _run(BASELINE_COMPLETION)
        target_match = results["target_match"]

        assert target_match["text_code"][IN_DIST_SNIPPET] == 0.0
        assert target_match["code"][IN_DIST_SNIPPET] == 0.0

    def test_baseline_code_is_runnable(self):
        """Baseline function body is valid Python and executes without error."""
        results = _run(BASELINE_COMPLETION)
        runnability = results["runnability"]

        assert runnability["text_code"][IN_DIST_SNIPPET] == 1.0
        assert runnability["code"][IN_DIST_SNIPPET] == 1.0


# ---------------------------------------------------------------------------
# Tests: post-edit behaviour
# ---------------------------------------------------------------------------


class TestPostEditPipeline:
    def test_post_edit_matches_target(self):
        """Edited completion uses **; AST check should score 1."""
        results = _run(EDITED_COMPLETION)
        target_match = results["target_match"]

        assert target_match["text_code"][IN_DIST_SNIPPET] == 1.0
        assert target_match["code"][IN_DIST_SNIPPET] == 1.0

    def test_post_edit_code_is_runnable(self):
        """width ** height is valid Python; runnability should be 1."""
        results = _run(EDITED_COMPLETION)

        assert results["runnability"]["text_code"][IN_DIST_SNIPPET] == 1.0

    def test_neighborhood_not_affected(self):
        """Neighbor completion uses l*w (no **); neighborhood score should be 1."""
        results = _run(NEIGHBOR_COMPLETION)
        target_match = results["target_match"]

        # neighborhood score = 1.0 means the edit did NOT leak into neighborhood
        assert target_match["neighborhood"][IN_DIST_SNIPPET] == 1.0


# ---------------------------------------------------------------------------
# Tests: ModelContext construction
# ---------------------------------------------------------------------------


class TestModelContextConstruction:
    def test_model_context_constructs_with_mocks(self, mock_ctx):
        """ModelContext can be constructed when EasyEdit/HF are mocked out."""
        ctx, mock_model = mock_ctx

        assert ctx.hparams is not None
        assert ctx.editor is not None
        assert ctx.tokenizer is not None
