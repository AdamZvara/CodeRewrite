"""Adapter wrapping Latium's ROME implementation behind a ModelContext-compatible interface.

Usage
-----
    from coderewrite.src.lib.latium_adapter import LatiumModelContext

    ctx = LatiumModelContext(
        "Latium/src/config/model/qwen2.5-1.5b.yaml",
        device=0,
    )
    metrics, edited_model = ctx.edit(
        prompts=edit.prompts,
        ground_truth=edit.ground_truth,
        target_new=edit.target_new,
        subject=edit.subject,
    )
    outputs = ctx.generate(prompts, model=edited_model)
    ctx.restore()

The class exposes the same public attributes as ModelContext so it can be
used as a drop-in replacement in scripts and evaluators:

    ctx.tokenizer           — HuggingFace tokenizer
    ctx.editor.model        — the underlying nn.Module (edited in-place)
    ctx.hparams.model_name  — model identifier string
    ctx.hparams.alg_name    — "Latium-ROME"
"""

import copy
import sys
import types
from pathlib import Path

import torch
from omegaconf import OmegaConf

_LATIUM_ROOT = Path(__file__).parents[3] / "Latium"


def _ensure_latium_on_path() -> None:
    """Add the Latium repo root to sys.path so ``src.*`` imports resolve."""
    root = str(_LATIUM_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


class LatiumModelContext:
    """ModelContext-compatible wrapper around Latium's ROME implementation.

    Parameters
    ----------
    model_yaml_path : str or Path
        Path to a Latium model YAML config, e.g.
        ``Latium/src/config/model/qwen2.5-1.5b.yaml``.
    model_name : str, optional
        Override the ``name`` field in the model YAML.
    device : int
        CUDA device index (passed as ``cuda:<device>``).
    """

    def __init__(self, model_yaml_path, model_name: str | None = None, device: int = 0):
        _ensure_latium_on_path()

        # Import here so the heavy Latium stack is only loaded on demand
        from src.handlers.rome import ModelHandler  # noqa: PLC0415
        from src.rome.rome import single_intervention  # noqa: PLC0415

        # ---- build the OmegaConf config that ModelHandler expects -----------
        model_cfg = OmegaConf.load(model_yaml_path)
        if model_name:
            model_cfg.name = model_name
        model_cfg.device = f"cuda:{device}" if isinstance(device, int) else device

        # ModelHandler reads cfg.model.* and optionally cfg.generation.*
        cfg = OmegaConf.create(
            {
                "model": OmegaConf.to_container(model_cfg, resolve=True),
                # k_N / v_N control how many context prefixes are sampled
                "generation": {"batch_size": 1, "k_N": 50, "v_N": 20},
            }
        )

        self.handler = ModelHandler(cfg)
        self._single_intervention = single_intervention
        self.device = device

        # ---- tokenizer setup (mirrors ModelContext) -------------------------
        self.tokenizer = self.handler.tokenizer
        pad_token = "<|extra_0|>"
        self.tokenizer.add_special_tokens({"pad_token": pad_token})
        self.tokenizer.padding_side = "left"

        # ---- public aliases expected by scripts and evaluators --------------
        # ctx.editor.model  (scripts access this to pass the edited model)
        _editor = types.SimpleNamespace(model=self.handler.model)
        self.editor = _editor

        # ctx.hparams.model_name / ctx.hparams.alg_name  (used for metadata)
        self.hparams = types.SimpleNamespace(
            model_name=model_cfg.name,
            alg_name="Latium-ROME",
        )

        # ---- weight snapshots for restoration -------------------------------
        self.initial_weights = copy.deepcopy(self._layer_module().weight.data)
        self._orig_weights: torch.Tensor | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _layer_module(self) -> torch.nn.Module:
        """Return the MLP layer module that ROME edits."""
        name = self.handler._layer_name_template.format(self.handler._layer)
        return self.handler._get_module(name)

    # ------------------------------------------------------------------
    # Generation  (same signature as ModelContext.generate)
    # ------------------------------------------------------------------

    def generate(self, prompts, model=None, max_new_tokens: int = 100):
        if model is None:
            model = self.handler.model
        device = self.handler.device
        batch = self.tokenizer(prompts, return_tensors="pt", padding=True)
        outputs = model.generate(
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device),
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
        )
        return [
            self.tokenizer.decode(outputs[i], skip_special_tokens=True)
            for i in range(len(prompts))
        ]

    # ------------------------------------------------------------------
    # Restore weights  (same interface as ModelContext)
    # ------------------------------------------------------------------

    def restore(self) -> None:
        """Restore the model to the weights that existed before the last edit."""
        if self._orig_weights is None:
            return
        with torch.no_grad():
            self._layer_module().weight.data.copy_(self._orig_weights)
        print("Original model restored")

    def restore_initial(self) -> None:
        """Restore the model to the very first checkpoint (before any edits)."""
        with torch.no_grad():
            self._layer_module().weight.data.copy_(self.initial_weights)
        self._orig_weights = None
        print("Model restored to initial weights")

    # ------------------------------------------------------------------
    # Edit  (same signature as ModelContext.edit)
    # ------------------------------------------------------------------

    def edit(
        self, prompts, ground_truth, target_new, subject, restore_first: bool = True
    ):
        """Apply a Latium ROME edit.

        Parameters mirror ``ModelContext.edit()`` exactly.

        ``subject`` and ``target_new`` may be lists (as returned by
        ``Edit.to_edit_kwargs()``); in that case the first element is used.
        Latium applies a single-fact edit, so only the first prompt and its
        corresponding subject/target are consumed.

        Latium expects a ``fact_tuple = (template, subject, target_new, target_true)``
        where *template* contains ``{}`` as the subject placeholder.  We derive
        the template from the first prompt by replacing the first occurrence of
        *subject* with ``{}``.  If *subject* does not appear verbatim in the
        prompt (e.g. the prompt omits it entirely), the whole prompt is used as a
        prefix and the subject is appended as the placeholder.

        Returns
        -------
        metrics : list
            Empty list — Latium does not produce per-edit metrics.
        edited_model : nn.Module
            The model after weight modification (edited in-place).
        """
        if restore_first and self._orig_weights is not None:
            self.restore()

        # Normalise list inputs — EasyEdit callers pass lists; Latium wants scalars
        subj = subject[0] if isinstance(subject, list) else subject
        tgt_new_str = target_new[0] if isinstance(target_new, list) else target_new
        tgt_true_str = (
            ground_truth[0] if isinstance(ground_truth, list) and ground_truth else ""
        )

        # Build the template from the first prompt
        prompt = prompts[0]
        if subj and subj in prompt:
            template = prompt.replace(subj, "{}", 1)
        else:
            # Subject not found verbatim; append as a suffix placeholder
            template = prompt.rstrip() + " {}"

        # Latium uses a leading-space convention for target strings
        def _add_leading_space(s: str) -> str:
            return s if s.startswith(" ") else " " + s.lstrip()

        fact_tuple = (
            template,
            subj,
            _add_leading_space(tgt_new_str),
            _add_leading_space(tgt_true_str) if tgt_true_str else " ",
        )

        _new_W, old_W = self._single_intervention(self.handler, fact_tuple)
        # old_W is a clone of the pre-edit weight produced inside insert_kv
        self._orig_weights = old_W.data.clone()

        return [], self.handler.model
