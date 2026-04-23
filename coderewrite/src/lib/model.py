import json
import random
import yaml
from pathlib import Path

import torch
from easyeditor import BaseEditor, ROMEHyperParams, MEMITHyperParams
from easyeditor.models.r_rome import R_ROMEHyperParams
from easyeditor.models.unke import unkeHyperParams, apply_unke_to_model
from easyeditor.util import nethook
from transformers import AutoTokenizer

HPARAMS_CLASSES = {
    "ROME": ROMEHyperParams,
    "R-ROME": R_ROMEHyperParams,
    "MEMIT": MEMITHyperParams,
    "UnKe": unkeHyperParams,
}

_EXEMPLARS_PATH = Path(__file__).parent.parent.parent / "data" / "python_exemplars.json"


def _load_hparams(path):
    """Load the right HyperParams class based on alg_name in the config file."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        with open(path) as f:
            alg_name = json.load(f).get("alg_name")
    else:
        with open(path) as f:
            alg_name = yaml.safe_load(f).get("alg_name")
    cls = HPARAMS_CLASSES.get(alg_name)
    if cls is None:
        raise ValueError(
            f"Unknown alg_name '{alg_name}' in {path}. "
            f"Supported: {list(HPARAMS_CLASSES.keys())}"
        )
    return cls.from_hparams(str(path))


class ModelContext:
    """Encapsulates model loading, editing, restoring, and generation."""

    def __init__(self, hparams_path, model_name=None, device=0):
        hparams = _load_hparams(hparams_path)
        if model_name:
            hparams.model_name = model_name
        hparams.device = device

        self.hparams = hparams
        self.device = device
        self.editor = BaseEditor.from_hparams(hparams)

        self.tokenizer = AutoTokenizer.from_pretrained(
            hparams.model_name, trust_remote_code=True
        )
        pad_token = "<|extra_0|>"
        if pad_token in self.tokenizer.get_vocab():
            self.tokenizer.add_special_tokens({"pad_token": pad_token})
        else:
            # Models like CodeLlama don't have <|extra_0|>; adding it would
            # extend the tokenizer vocab past the model's embedding table size,
            # causing an OOB CUDA assert during padded forward passes.
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.tokenizer.padding_side = "left"

        self.initial_weights = self.editor.model.state_dict()
        self._orig_weights = None

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate(self, prompts, model=None, max_new_tokens=100):
        if model is None:
            model = self.editor.model
        batch = self.tokenizer(prompts, return_tensors="pt", padding=True)

        outputs = model.generate(
            input_ids=batch["input_ids"].to(f"cuda:{self.device}"),
            attention_mask=batch["attention_mask"].to(f"cuda:{self.device}"),
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
        )

        results = []
        for i in range(len(prompts)):
            result = self.tokenizer.decode(outputs[i], skip_special_tokens=True)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Restore weights
    # ------------------------------------------------------------------
    def restore(self):
        if self._orig_weights is None:
            return
        with torch.no_grad():
            for k, v in self._orig_weights.items():
                nethook.get_parameter(self.editor.model, k)[...] = v
        print("Original model restored")

    def restore_initial(self):
        """Restore to the very first checkpoint (before any edits)."""
        self.editor.model.load_state_dict(self.initial_weights)
        self._orig_weights = None
        print("Model restored to initial weights")

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------
    def _edit_unke(self, prompts, target_new):
        """Apply a UNKe edit directly, bypassing BaseEditor."""
        batch_data = [{"question": p, "answer": target_new} for p in prompts]

        with open(_EXEMPLARS_PATH) as f:
            all_ex = json.load(f)
        ex_data = random.sample(all_ex, min(self.hparams.ex_data_num, len(all_ex)))

        self._orig_weights = apply_unke_to_model(
            self.editor.model, self.tokenizer, self.hparams, batch_data, ex_data
        )
        return [], self.editor.model

    def edit(self, prompts, ground_truth, target_new, subject, restore_first=True):
        if restore_first and self._orig_weights is not None:
            self.restore()

        if self.hparams.alg_name == "UnKe":
            return self._edit_unke(prompts, target_new)

        # ROME and MEMIT internally call prompt.format(subject) when building
        # model inputs.  Any { or } in the prompt code (dict literals, f-strings,
        # etc.) would be misinterpreted as format placeholders and raise KeyError.
        # Escaping them to {{ / }} makes .format() treat them as literal braces.
        safe_prompts = [p.replace("{", "{{").replace("}", "}}") for p in prompts]

        metrics, edited_model, self._orig_weights = self.editor.edit(
            prompts=safe_prompts,
            ground_truth=ground_truth,
            target_new=target_new,
            subject=subject,
            sequential_edit=True,
        )
        return metrics, edited_model
