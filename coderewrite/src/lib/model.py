import torch
from easyeditor import BaseEditor, ROMEHyperParams
from easyeditor.util import nethook
from transformers import AutoTokenizer


class ModelContext:
    """Encapsulates model loading, editing, restoring, and generation."""

    def __init__(self, hparams_path, model_name=None, device=0):
        hparams = ROMEHyperParams.from_hparams(hparams_path)
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
        self.tokenizer.add_special_tokens({"pad_token": pad_token})
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
    def edit(self, prompts, ground_truth, target_new, subject, restore_first=True):
        if restore_first and self._orig_weights is not None:
            self.restore()

        metrics, edited_model, self._orig_weights = self.editor.edit(
            prompts=prompts,
            ground_truth=ground_truth,
            target_new=target_new,
            subject=subject,
            sequential_edit=True,
        )
        return metrics, edited_model
