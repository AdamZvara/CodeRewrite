"""Evaluation framework for measuring knowledge-edit effectiveness.

Generates model completions across diverse prompt groups and scores them
on two axes: **target match** (did the edit take effect?) and **runnability**
(is the generated code executable?).
"""

import ast
import re
import signal
import sys
from typing import List, Dict, Callable

# Timeout for sandboxed exec() of generated code. Keeps the evaluation
# pipeline from hanging on infinite loops or blocking I/O in model output.
EXEC_TIMEOUT = 5  # seconds


class BaselineEvaluator:
    """Evaluates model generations across prompt groups on two dimensions:
    target match (does the output contain the desired edit?) and runnability
    (is the generated code syntactically valid and executable?).

    Each prompt is generated 3 times with temperature sampling to measure
    consistency. Prompt groups (text_code, code, text, neighborhood, etc.)
    represent different ways of eliciting the same knowledge, allowing us
    to measure how well an edit generalises across prompt styles.
    """

    def __init__(
        self,
        generate_fn: Callable,
        model,
        target: str,
        code_start_tag: str,
        text_code: List[str] = None,
        text_code_with_usage: List[str] = None,
        code: List[str] = None,
        text: List[str] = None,
        paraphrase_text_code: List[str] = None,
        long_tasks: List[str] = None,
        neighborhood: List[str] = None,
        evaluate_fn: Callable = None,
        evaluate_neighborhood_fn: Callable = None,
    ):
        """Initialise the evaluator.

        Args:
            generate_fn: Callable that takes (prompts, model, max_new_tokens)
                and returns a list of generated strings.
            model: The language model object passed through to generate_fn.
            target: The target string that a successful edit should produce
                in the model's output.
            code_start_tag: The actual code-fence opening (e.g. "```python")
                that replaces the ``<CODE_START>`` placeholder in prompts.
            text_code, text_code_with_usage, code, text, paraphrase_text_code,
                long_tasks, neighborhood: Optional lists of prompt strings for
                each prompt group. ``None`` means the group is skipped.
            evaluate_fn: Custom scoring function ``(generation, extracted_code) -> bool``.
                Defaults to checking whether ``target`` appears in the generation.
            evaluate_neighborhood_fn: Custom scoring function for the neighborhood
                group. Defaults to checking that ``target`` does NOT appear,
                since neighborhood prompts test that unrelated knowledge is preserved.
        """
        self.generate_fn = generate_fn
        self.model = model
        self.target = target
        self.code_start_tag = code_start_tag
        self.generations = {}

        if evaluate_fn is not None:
            self.evaluate_fn = evaluate_fn
        else:
            self.evaluate_fn = lambda gen, code: self.target in gen

        if evaluate_neighborhood_fn is not None:
            self.evaluate_neighborhood_fn = evaluate_neighborhood_fn
        else:
            self.evaluate_neighborhood_fn = lambda gen, code: self.target not in gen

        self.prompt_groups = {
            "text_code": text_code,
            "text_code_with_usage": text_code_with_usage,
            "code": code,
            "text": text,
            "paraphrase_text_code": paraphrase_text_code,
            "long_tasks": long_tasks,
            "neighborhood": neighborhood,
        }

    # -----------------------------
    # Updating the model
    # -----------------------------
    def update_model(self, new):
        """Replace the current model reference (e.g. after applying an edit)."""
        self.model = new

    # -----------------------------
    # Generation
    # -----------------------------
    def _replace_code_start(self, prompt):
        """Substitute the ``<CODE_START>`` placeholder with the actual code
        fence tag so prompts read naturally to the model."""
        return prompt.replace("<CODE_START>", self.code_start_tag)

    def _generate_for_prompt(self, prompt: str, max_new_tokens: int):
        """Generate 3 independent completions for a single prompt.

        The prompt is duplicated 3 times so the model produces multiple
        samples in one batch call, giving a simple consistency measure
        under temperature sampling.
        """
        prompt = self._replace_code_start(prompt)
        prompts = [prompt] * 3
        return self.generate_fn(prompts, self.model, max_new_tokens=max_new_tokens)

    def generate(self):
        """Run generation for every registered prompt group.

        Results are stored in ``self.generations`` keyed by group name.
        The ``long_tasks`` group gets a higher token budget (600) because
        those prompts ask for more elaborate code; all other groups use 100
        tokens which is enough for short function definitions.
        """
        self.generations = {}
        for group_name, prompts in self.prompt_groups.items():
            if prompts is None:
                continue
            group_results = []
            for prompt in prompts:
                max_tokens = 600 if group_name == "long_tasks" else 100
                group_results.append(self._generate_for_prompt(prompt, max_tokens))
            self.generations[group_name] = group_results

    def print_generations(self, target_group: str = None) -> None:
        """Pretty-print all generated outputs, optionally filtered to a single group."""
        assert self.generations != {}, "Must run generate() first!"

        for group, results in self.generations.items():
            if target_group and group != target_group:
                continue
            print("Group", group)
            for r in results:
                for x in r:
                    print(x)
                    print(15 * "-")
            print(30 * "=")

    def get_prompt_generation_pairs(self) -> Dict:
        """Return generations paired with their prompts for readable output."""
        assert self.generations != {}, "Must run generate() first!"

        paired = {}
        for group_name, prompts in self.prompt_groups.items():
            if prompts is None or group_name not in self.generations:
                continue
            paired[group_name] = []
            for prompt, gens in zip(prompts, self.generations[group_name]):
                paired[group_name].append(
                    {
                        "prompt": self._replace_code_start(prompt),
                        "generations": gens,
                    }
                )
        return paired

    # -----------------------------
    # Code execution check
    # -----------------------------
    def _extract_fenced_blocks(self, generation: str) -> List[str]:
        """Extract all fenced code blocks, including truncated final blocks."""
        tag = re.escape(self.code_start_tag)
        # Match complete fenced blocks
        blocks = re.findall(
            f"{tag}(.*?)```",
            generation,
            re.DOTALL | re.IGNORECASE,
        )
        # Check for a trailing unclosed block (truncated output)
        trailing = re.search(
            f"{tag}((?:(?!```).)+)$",
            generation,
            re.DOTALL | re.IGNORECASE,
        )
        if trailing:
            blocks.append(trailing.group(1))
        return [b.strip() for b in blocks if b.strip()]

    @staticmethod
    def _is_valid_python(code: str) -> bool:
        """Check whether ``code`` parses as valid Python (syntax only, no execution)."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    @staticmethod
    def _normalize(code: str) -> str:
        """Normalize whitespace for dedup comparison."""
        return re.sub(r"\s+", " ", code).strip()

    def _deduplicate(self, blocks: List[str]) -> List[str]:
        """Remove duplicate blocks and blocks that are subsets of others.

        Models sometimes repeat the same code in multiple fenced blocks
        within a single generation. This deduplicates on normalised
        whitespace and also collapses subset relationships — if block A
        is contained within block B, only B is kept.
        """
        seen_normalized = []
        unique = []
        for block in blocks:
            norm = self._normalize(block)
            # Skip if identical (normalized) to an already-seen block
            if norm in seen_normalized:
                continue
            # Skip if this block is a substring of an existing block
            if any(norm in existing for existing in seen_normalized):
                continue
            # If a new block is a superset of an existing one, replace it
            replaced = False
            for i, existing in enumerate(seen_normalized):
                if existing in norm:
                    seen_normalized[i] = norm
                    unique[i] = block
                    replaced = True
                    break
            if not replaced:
                seen_normalized.append(norm)
                unique.append(block)
        return unique

    def _merge_blocks(self, blocks: List[str]) -> str:
        """Concatenate multiple fenced code blocks into a single runnable string.

        Models often split a response across several code fences (e.g. a
        function definition in one block and a usage example in another).
        This method tries to merge them intelligently:

        1. If all blocks concatenate into valid Python, return that.
        2. Otherwise, incrementally append blocks: two independently valid
           blocks are joined (definition + usage), an invalid fragment is
           appended to an incomplete result hoping it completes it, and a
           standalone-invalid fragment following valid code is dropped.
        """
        if len(blocks) == 1:
            return blocks[0]

        # Try concatenating all blocks
        merged = "\n\n".join(blocks)
        if self._is_valid_python(merged):
            return merged

        # Incremental merge: add blocks one by one if they contribute
        result = blocks[0]
        for block in blocks[1:]:
            if self._is_valid_python(block) and self._is_valid_python(result):
                # Both valid independently — concatenate (e.g. definition + usage)
                result = result + "\n\n" + block
            elif not self._is_valid_python(result):
                # Current result is incomplete, this block may complete it
                result = result + "\n\n" + block
            else:
                # Result is valid, new block is not valid on its own — skip fragment
                continue
        return result

    def _extract_runnable(self, generation: str) -> str:
        """Extract executable Python code from a model generation.

        Prefers fenced code blocks (```python ... ```) when present.
        Falls back to a heuristic line-by-line scan that looks for common
        Python statement prefixes (def, class, import, …) when the model
        produces bare code without fences. Returns ``None`` if no code
        can be identified.
        """
        blocks = self._extract_fenced_blocks(generation)
        if blocks:
            blocks = self._deduplicate(blocks)
            return self._merge_blocks(blocks)

        # Fallback: no fenced blocks found, try to extract bare Python code
        lines = generation.split("\n")
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and (
                stripped.startswith(
                    (
                        "def ",
                        "class ",
                        "import ",
                        "from ",
                        "if ",
                        "for ",
                        "while ",
                        "return ",
                    )
                )
                or (code_lines and (line.startswith((" ", "\t")) or stripped == ""))
            ):
                code_lines.append(line)
            elif code_lines and not stripped:
                code_lines.append(line)
            elif code_lines:
                # Stop at first non-code line after collecting some code
                break

        if code_lines:
            return "\n".join(code_lines).strip()
        return None

    def _is_runnable(self, code_str: str) -> bool:
        """Execute generated code to check if it runs without errors.

        Generated code may contain constructs that interfere with the parent
        process, so we sandbox the execution:
        - sys.argv is cleared so that argparse in generated code doesn't
          parse the parent's CLI arguments (e.g. hparams YAML path).
        - input() is stubbed out so that generated code calling input()
          doesn't block waiting for stdin.
        - A SIGALRM timeout guard prevents hangs from infinite loops or
          other blocking operations in the generated code.
        - SystemExit is caught so that generated code calling sys.exit()
          (e.g. argparse on error) doesn't kill the parent process.
        """
        if code_str is None:
            return False

        def _timeout_handler(signum, frame):
            raise TimeoutError

        saved_argv = sys.argv
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        try:
            sys.argv = [""]
            signal.alarm(EXEC_TIMEOUT)
            exec(code_str, {"input": lambda *a, **kw: ""}, {})
            return True
        except (Exception, SystemExit):
            return False
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            sys.argv = saved_argv

    def _all_runnable(self, generations: List[str]) -> bool:
        """Return True only if every generation in the list is runnable."""
        return all(self._is_runnable(gen) for gen in generations)

    # -----------------------------
    # Evaluation passes
    # -----------------------------
    def evaluate_score(self) -> Dict:
        """Score each prompt group on target match.

        For regular groups, uses ``evaluate_fn`` which by default checks
        that the target string appears in the generation (edit success).
        For the ``neighborhood`` group, uses ``evaluate_neighborhood_fn``
        which by default checks that the target does NOT appear, verifying
        that the edit did not bleed into unrelated knowledge.

        Returns a dict mapping group name to the average score (0.0–1.0).
        """
        results = {}
        assert self.generations != {}, "Must run generate() first!"

        for group_name, outputs in self.generations.items():
            group_score = []
            for output_batch in outputs:
                for output_single in output_batch:
                    code = self._extract_runnable(output_single)
                    if group_name == "neighborhood":
                        group_score.append(
                            self.evaluate_neighborhood_fn(output_single, code)
                        )
                    else:
                        group_score.append(self.evaluate_fn(output_single, code))
            avg = sum(group_score) / len(group_score)
            results[group_name] = avg

        return results

    def evaluate_run(self) -> Dict:
        """Score each prompt group on code runnability.

        Extracts code from each generation and attempts to execute it in a
        sandboxed ``exec()`` call. The ``neighborhood`` group is skipped
        because those prompts test knowledge preservation, not code quality.

        Returns a dict mapping group name to the average score (0.0–1.0).
        """
        results = {}
        assert self.generations != {}, "Must run generate() first!"

        for group_name, outputs in self.generations.items():
            group_score = []
            if group_name == "neighborhood":
                continue
            for output_batch in outputs:
                for output_single in output_batch:
                    code = self._extract_runnable(output_single)
                    group_score.append(self._is_runnable(code))
            avg = sum(group_score) / len(group_score)
            results[group_name] = avg

        return results

    # -----------------------------
    # Combined evaluation
    # -----------------------------
    def evaluate(self) -> Dict:
        """Run both evaluation passes and return combined results.

        Returns a dict with keys ``"target_match"`` and ``"runnability"``,
        each mapping group names to their average scores.
        """
        return {
            "target_match": self.evaluate_score(),
            "runnability": self.evaluate_run(),
        }
