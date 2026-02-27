"""Tests for <SNIP>/<SNIPPET> prompt splitting and token-probability evaluation."""

import pytest

torch = pytest.importorskip("torch")
# test_pipeline.py stubs torch in sys.modules at collection time so that
# integration tests can run without a real PyTorch install.  That stub leaks
# into this module and makes importorskip return a MagicMock instead of
# skipping.  Guard against it: a real torch always has Tensor as a proper type.
if not isinstance(torch.Tensor, type):
    pytest.skip("torch is stubbed (not functional)", allow_module_level=True)

from src.lib.evaluator import Evaluator, Prompts  # noqa: E402
from src.lib.evaluator.prompts import SNIP_TAG, SNIPPET_TAG  # noqa: E402
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

    def test_generations_use_nested_structure(self):
        """generate() result uses new {group: [{"snippet": ..., "results": ...}]} shape."""

        def fake_generate(prompts, model, max_new_tokens=100):
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
        gens = ev._generator.generations
        assert "text_code" in gens
        entries = gens["text_code"]
        assert isinstance(entries, list)
        assert len(entries) == 1  # one snippet entry (snippet=None)
        entry = entries[0]
        assert "snippet" in entry
        assert "results" in entry
        assert entry["snippet"] is None
        assert isinstance(entry["results"], list)


# ----- Dynamic SNIP injection -----


class TestInjectSnipInSnippet:
    """Tests for Prompts.inject_snip_in_snippet."""

    def test_snip_inserted_at_word_boundary(self):
        snippet = "def foo():\n    return False"
        result = Prompts.inject_snip_in_snippet(snippet)
        assert SNIP_TAG in result
        idx = result.index(SNIP_TAG)
        # The character before the tag must be whitespace.
        assert result[idx - 1] in " \n\t"

    def test_no_whitespace_falls_back_to_end(self):
        snippet = "False"
        result = Prompts.inject_snip_in_snippet(snippet)
        assert result == "False" + SNIP_TAG

    def test_only_one_snip_inserted(self):
        snippet = "def foo():\n    return False\n"
        result = Prompts.inject_snip_in_snippet(snippet)
        assert result.count(SNIP_TAG) == 1

    def test_seeded_rng_is_deterministic(self):
        import random

        snippet = "def foo(a, b):\n    x = a + b\n    return x\n"
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        assert Prompts.inject_snip_in_snippet(
            snippet, rng=rng1
        ) == Prompts.inject_snip_in_snippet(snippet, rng=rng2)

    def test_bias_toward_second_half(self):
        """Over many draws the SNIP should land in the second half more often."""
        import random

        # Snippet with 10 clear word boundaries, evenly spaced.
        snippet = " ".join(f"tok{i}" for i in range(10)) + " end"
        rng = random.Random(0)
        boundaries = [i for i in range(1, len(snippet)) if snippet[i - 1] == " "]
        mid = len(boundaries) // 2
        second_half_positions = set(boundaries[mid:])

        second_half_count = 0
        trials = 1000
        for _ in range(trials):
            result = Prompts.inject_snip_in_snippet(snippet, rng=rng)
            pos = result.index(SNIP_TAG)
            if pos in second_half_positions:
                second_half_count += 1

        ratio = second_half_count / trials
        assert ratio > 0.60, f"Expected ~70% second-half, got {ratio:.2%}"
        assert ratio < 0.85, f"Expected ~70% second-half, got {ratio:.2%}"


class TestInjectSnipForText:
    """Tests for Prompts.inject_snip_for_text."""

    def test_snip_inserted_before_newline_code_start(self):
        prompt = "Write a function.\n<CODE_START><SNIPPET>"
        result = Prompts.inject_snip_for_text(prompt)
        assert result == "Write a function." + SNIP_TAG + "\n<CODE_START><SNIPPET>"

    def test_snip_inserted_before_code_start_no_newline(self):
        prompt = "Write a function.<CODE_START><SNIPPET>"
        result = Prompts.inject_snip_for_text(prompt)
        assert result == "Write a function." + SNIP_TAG + "<CODE_START><SNIPPET>"

    def test_no_code_start_falls_back_to_end(self):
        prompt = "Just some text."
        result = Prompts.inject_snip_for_text(prompt)
        assert result == "Just some text." + SNIP_TAG


class TestPreparePrompt:
    """Tests for Prompts.prepare_prompt end-to-end."""

    def test_no_snippet_tag_returned_unchanged(self):
        p = Prompts(code_start_tag=CODE_START)
        prompt = "baked prompt<SNIP> rest"
        assert p.prepare_prompt(prompt, "text_code", None) == prompt

    def test_text_group_snip_before_code_start(self):
        p = Prompts(code_start_tag=CODE_START)
        prompt = "Write a function.\n<CODE_START><SNIPPET>"
        result = p.prepare_prompt(prompt, "text", "def foo(): pass")
        # <SNIP> must sit before the (un-replaced) <CODE_START> tag.
        assert SNIP_TAG + "\n<CODE_START>" in result
        assert "def foo(): pass" in result

    def test_text_group_strips_existing_snip_before_reinject(self):
        """If the template already had <SNIP> it must not appear twice."""
        p = Prompts(code_start_tag=CODE_START)
        prompt = "Write a function." + SNIP_TAG + "\n<CODE_START><SNIPPET>"
        result = p.prepare_prompt(prompt, "text", "def foo(): pass")
        assert result.count(SNIP_TAG) == 1

    def test_other_group_strips_template_snip_and_injects_in_snippet(self):
        import random

        p = Prompts(code_start_tag=CODE_START)
        # Template has legacy <SNIP> at end — must be stripped and replaced.
        prompt = "intro\n<CODE_START><SNIPPET><SNIP>"
        snippet = "def foo():\n    return False\n"
        result = p.prepare_prompt(prompt, "text_code", snippet, rng=random.Random(1))
        # Exactly one SNIP in result, and it must be inside the snippet portion.
        assert result.count(SNIP_TAG) == 1
        code_start_idx = result.index("<CODE_START>")
        snip_idx = result.index(SNIP_TAG)
        assert snip_idx > code_start_idx

    def test_generation_mode_cuts_at_snip(self):
        import random

        p = Prompts(code_start_tag=CODE_START)
        prompt = "Complete:\n<CODE_START><SNIPPET>"
        snippet = "def foo():\n    return False\n"
        prepared = p.prepare_prompt(prompt, "text_code", snippet, rng=random.Random(7))
        gen_prefix = Prompts.for_generation(prepared)
        assert SNIP_TAG not in gen_prefix
        # Generation prefix must start with the preamble.
        assert gen_prefix.startswith("Complete:\n<CODE_START>")

    def test_probability_mode_keeps_full_snippet(self):
        import random

        p = Prompts(code_start_tag=CODE_START)
        prompt = "Complete:\n<CODE_START><SNIPPET>"
        snippet = "def foo():\n    return False\n"
        prepared = p.prepare_prompt(prompt, "text_code", snippet, rng=random.Random(7))
        prob_prefix = Prompts.for_probability(prepared)
        assert SNIP_TAG not in prob_prefix
        # Full snippet text must appear.
        assert "def foo():" in prob_prefix
        assert "return False" in prob_prefix


# ----- SNIPPET tag expansion -----


class TestSnippetExpansion:
    """Tests for <SNIPPET> substitution and snippet-driven generation."""

    def test_replace_snippet_substitutes_tag(self):
        prompt = "foo <SNIPPET> bar"
        result = Prompts.replace_snippet(prompt, "BODY")
        assert result == "foo BODY bar"
        assert SNIPPET_TAG not in result

    def test_replace_snippet_multiple_occurrences(self):
        prompt = "<SNIPPET> and <SNIPPET>"
        result = Prompts.replace_snippet(prompt, "X")
        assert result == "X and X"

    def test_replace_snippet_no_tag(self):
        prompt = "no tag here"
        result = Prompts.replace_snippet(prompt, "X")
        assert result == "no tag here"

    def test_generation_with_snippets_one_entry_per_snippet(self):
        """Generator.generate() produces one entry per snippet."""
        captured_prompts = []

        def fake_generate(prompts, model, max_new_tokens=100):
            captured_prompts.extend(prompts)
            return ["out"] * len(prompts)

        prompts = Prompts(
            code_start_tag=CODE_START,
            in_dist_snippets=["body_a"],
            out_dist_snippets=["body_b"],
            text_code=["intro\n<CODE_START><SNIPPET><SNIP>"],
        )
        ev = Evaluator(
            generate_fn=fake_generate,
            model=None,
            target="",
            prompts=prompts,
        )
        ev.generate()
        entries = ev._generator.generations["text_code"]
        assert len(entries) == 2
        assert entries[0]["snippet"] == "body_a"
        assert entries[1]["snippet"] == "body_b"
        # Each entry has results for 1 prompt template × 3 repetitions
        assert len(entries[0]["results"]) == 1
        assert len(entries[0]["results"][0]) == 3

    def test_generation_without_snippets_single_none_entry(self):
        """When no snippets defined, a single entry with snippet=None is produced."""

        def fake_generate(prompts, model, max_new_tokens=100):
            return ["out"] * len(prompts)

        prompts = Prompts(
            code_start_tag=CODE_START,
            text_code=["plain prompt<SNIP>"],
        )
        ev = Evaluator(
            generate_fn=fake_generate,
            model=None,
            target="",
            prompts=prompts,
        )
        ev.generate()
        entries = ev._generator.generations["text_code"]
        assert len(entries) == 1
        assert entries[0]["snippet"] is None

    def test_snippet_substituted_before_generation(self):
        """The prompt passed to generate_fn has <SNIPPET> already resolved."""
        captured = []

        def fake_generate(prompts, model, max_new_tokens=100):
            captured.extend(prompts)
            return ["out"] * len(prompts)

        prompts = Prompts(
            code_start_tag=CODE_START,
            in_dist_snippets=["body_here"],
            text_code=["intro\n<CODE_START><SNIPPET><SNIP>"],
        )
        ev = Evaluator(
            generate_fn=fake_generate,
            model=None,
            target="",
            prompts=prompts,
        )
        ev.generate()
        # All 3 repetitions should have snippet resolved and SNIP stripped
        expected = f"intro\n{CODE_START}body_here"
        for p in captured:
            assert p == expected
        assert SNIPPET_TAG not in captured[0]

    def test_token_prob_evaluator_expands_snippets(self, monkeypatch):
        """TokenProbabilityEvaluator produces one entry per snippet per group."""
        import src.lib.evaluator.token_probs as tp_mod

        seen_prefixes = []

        def fake_compute(model, tokenizer, prefixes, target_new, target_true, wc):
            seen_prefixes.append(list(prefixes))
            return (
                [{"target_new": 0.5, "target_true": 1.0}] * len(prefixes),
                [True] * len(prefixes),
            )

        monkeypatch.setattr(tp_mod, "compute_token_probabilities", fake_compute)

        from src.lib.evaluator.token_probs import TokenProbabilityEvaluator

        prompts = Prompts(
            code_start_tag=CODE_START,
            in_dist_snippets=["body_a"],
            out_dist_snippets=["body_b"],
            text_code=["intro\n<CODE_START><SNIPPET><SNIP>"],
        )
        ev = TokenProbabilityEvaluator(
            model=object(),
            tokenizer=_FakeTokenizer(),
            target="foo",
            target_true="bar",
            prompts=prompts,
        )
        result = ev.evaluate()

        assert "text_code" in result
        # One entry per snippet
        assert set(result["text_code"].keys()) == {"body_a", "body_b"}
        # compute_token_probabilities called once per snippet
        assert len(seen_prefixes) == 2


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
            {k: v.to(device) if hasattr(v, "to") else v for k, v in self.items()}
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
            mask = torch.ones_like(ids)
            mask[ids == self.pad_token_id] = 0
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
