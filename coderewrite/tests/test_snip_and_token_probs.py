"""Tests for <SNIP> prompt splitting and token-probability evaluation."""

import pytest

torch = pytest.importorskip("torch")

from src.lib.evaluator import Evaluator, Prompts  # noqa: E402
from src.lib.evaluator.prompts import SNIP_TAG  # noqa: E402
from src.lib.evaluator.token_probs import compute_token_probabilities  # noqa: E402

CODE_START = "```python\n"


# ----- SNIP prompt splitting -----


class TestSnipPromptSplitting:
    def test_generation_mode_strips_snip_and_after(self):
        prompt = "text\n<CODE_START>def area<SNIP>(width, height):\n    return"
        result = Prompts.for_generation(prompt)
        assert result == "text\n<CODE_START>def area"
        assert SNIP_TAG not in result

    def test_probability_mode_removes_snip_only(self):
        prompt = "text\n<CODE_START>def area<SNIP>(width, height):\n    return"
        result = Prompts.for_probability(prompt)
        assert result == "text\n<CODE_START>def area(width, height):\n    return"
        assert SNIP_TAG not in result

    def test_no_snip_generation_unchanged(self):
        prompt = "a plain prompt without snip"
        assert Prompts.for_generation(prompt) == prompt

    def test_no_snip_probability_unchanged(self):
        prompt = "a plain prompt without snip"
        assert Prompts.for_probability(prompt) == prompt

    def test_text_prompt_snip_at_end(self):
        """TEXT prompts have <SNIP> between description and code prefix."""
        prompt = (
            "Write a function.<SNIP>\n<CODE_START>def area(width, height):\n    return"
        )
        gen = Prompts.for_generation(prompt)
        prob = Prompts.for_probability(prompt)
        assert gen == "Write a function."
        assert (
            prob
            == "Write a function.\n<CODE_START>def area(width, height):\n    return"
        )

    def test_long_task_snip_at_end(self):
        """LONG_TASKS have <SNIP> at the very end — both modes give the same prefix."""
        prompt = "Write a flask app.<SNIP>"
        gen = Prompts.for_generation(prompt)
        prob = Prompts.for_probability(prompt)
        assert gen == "Write a flask app."
        assert prob == "Write a flask app."


class TestGenerationUsesSnip:
    """Verify that generate() passes the generation-mode prefix."""

    def test_generate_calls_use_generation_prefix(self):
        captured = []

        def fake_generate(prompts, model, max_new_tokens=100):
            captured.extend(prompts)
            return ["output"] * len(prompts)

        prompts = Prompts(
            code_start_tag=CODE_START,
            text_code=["text\n<CODE_START>def area<SNIP>(w, h):\n    return"],
        )
        ev = Evaluator(
            generate_fn=fake_generate,
            model=None,
            target="",
            prompts=prompts,
        )
        ev.generate()
        # Should have called generate with the generation-mode prefix (3 copies)
        assert len(captured) == 3
        expected = "text\n```python\ndef area"
        for p in captured:
            assert p == expected


# ----- compute_token_probabilities -----


class _FakeModel(torch.nn.Module):
    """Minimal stub that returns logits favouring a specific token sequence.

    Simulates causal-LM behaviour: logits at position *k* predict the
    token at position *k + 1*.  So ``next_token_ids`` should contain the
    tokens that appear at positions 1, 2, …, seq_len in the target
    sequence.
    """

    def __init__(self, vocab_size, next_token_ids):
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.vocab_size = vocab_size
        self.next_token_ids = next_token_ids

    def forward(self, input_ids, attention_mask=None, **kwargs):
        batch, seq = input_ids.shape
        logits = torch.full((batch, seq, self.vocab_size), -10.0)
        for b in range(batch):
            for s in range(min(seq, len(self.next_token_ids))):
                logits[b, s, self.next_token_ids[s]] = 10.0
        return type("Out", (), {"logits": logits})()


class _TokenizerOutput(dict):
    """Dict subclass that supports .to(device) like HuggingFace BatchEncoding."""

    def to(self, device):
        return _TokenizerOutput(
            {
                k: v.to(device) if isinstance(v, torch.Tensor) else v
                for k, v in self.items()
            }
        )


class _FakeTokenizer:
    """Minimal tokenizer stub that maps each character to its ord value."""

    def __init__(self):
        self.pad_token_id = 0

    def __call__(self, texts, padding=False, return_tensors=None):
        single = isinstance(texts, str)
        if single:
            texts = [texts]
        encoded = [[ord(c) for c in t] for t in texts]
        max_len = max(len(e) for e in encoded)
        if padding:
            for e in encoded:
                while len(e) < max_len:
                    e.append(self.pad_token_id)
        if return_tensors == "pt":
            ids = torch.tensor(encoded)
            mask = (ids != self.pad_token_id).long()
            return _TokenizerOutput({"input_ids": ids, "attention_mask": mask})
        # Match HuggingFace: single string → flat list, list → list of lists
        if single:
            return {"input_ids": encoded[0]}
        return {"input_ids": encoded}


class TestComputeTokenProbabilities:
    def test_returns_correct_structure(self):
        """Smoke test: check output shape and types."""
        tok = _FakeTokenizer()
        prefix = "a"
        target_new = "b"
        target_true = "c"

        # "a b" = [97, 32, 98].  Causal LM: logits at position k predict
        # token at k+1, so next_token_ids = [32, 98, ...] (shifted left by 1).
        full_new_ids = tok(f"{prefix} {target_new}", return_tensors="pt")["input_ids"][
            0
        ]
        next_token_ids = full_new_ids[1:].tolist()  # shift: predict next token
        model = _FakeModel(vocab_size=256, next_token_ids=next_token_ids)

        probs, correct = compute_token_probabilities(
            model, tok, [prefix], target_new, target_true, [0]
        )
        assert len(probs) == 1
        assert "target_new" in probs[0]
        assert "target_true" in probs[0]
        assert len(correct) == 1
        # Model favours target_new, so it should be correct for which_correct=0
        assert correct[0] is True
        # target_new should have lower NLL (more likely)
        assert probs[0]["target_new"] < probs[0]["target_true"]


# ----- evaluate() token_probability integration -----


class TestEvaluateTokenProbs:
    def test_skipped_when_no_tokenizer(self):
        prompts = Prompts(code_start_tag=CODE_START, text_code=["prompt<SNIP> rest"])
        ev = Evaluator(
            generate_fn=lambda *a, **kw: ["x"],
            model=None,
            target="foo",
            prompts=prompts,
        )
        ev.generate()
        result = ev.evaluate()
        assert "token_probability" not in result

    def test_skipped_when_no_target_true(self):
        prompts = Prompts(code_start_tag=CODE_START, text_code=["prompt<SNIP> rest"])
        ev = Evaluator(
            generate_fn=lambda *a, **kw: ["x"],
            model=None,
            target="foo",
            prompts=prompts,
            tokenizer=_FakeTokenizer(),
        )
        ev.generate()
        result = ev.evaluate()
        assert "token_probability" not in result

    def test_long_tasks_excluded(self, monkeypatch):
        """long_tasks group must not appear in token-probability results."""
        import src.lib.evaluator.token_probs as tp_mod
        from src.lib.evaluator.token_probs import TokenProbabilityEvaluator

        def fake_compute(
            model, tokenizer, prefixes, target_new, target_true, which_correct
        ):
            return (
                [{"target_new": 0.5, "target_true": 1.0}] * len(prefixes),
                [True] * len(prefixes),
            )

        monkeypatch.setattr(tp_mod, "compute_token_probabilities", fake_compute)

        prompts = Prompts(
            code_start_tag=CODE_START,
            text_code=["prompt<SNIP> rest"],
            long_tasks=["long task prompt<SNIP>"],
        )
        ev = TokenProbabilityEvaluator(
            model=object(),
            tokenizer=_FakeTokenizer(),
            target="foo",
            target_true="bar",
            prompts=prompts,
        )
        result = ev.evaluate()

        assert "long_tasks" not in result
        assert "text_code" in result
