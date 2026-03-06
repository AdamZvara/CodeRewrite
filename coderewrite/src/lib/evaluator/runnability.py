"""Runnability evaluation for generated code."""

import ast
import re
import signal
import sys
from typing import List
from enum import Enum


class RunnabilityExtractionType(str, Enum):
    FIRST = "first"
    MERGE = "merge"


class RunnabilityEvaluator:
    """Evaluates whether generated code is syntactically valid and executable."""

    def __init__(
        self,
        code_start_tag: str,
        extraction_mode: RunnabilityExtractionType = RunnabilityExtractionType.FIRST,
        execution_timeout: int = 5,
    ):
        self.code_start_tag = code_start_tag
        # Controls how multiple fenced blocks are handled in extract_runnable:
        #   "first" — return only the first fenced block (simpler, less noise).
        #   "merge" — deduplicate and concatenate all blocks (old behaviour,
        #             suitable for long-form tasks where the whole application
        #             spans multiple blocks).
        self.extraction_mode = extraction_mode
        # Timeout for sandboxed exec() of generated code. Keeps the evaluation
        # pipeline from hanging on infinite loops or blocking I/O in model output.
        self.exec_timeout = execution_timeout

    def extract_runnable(
        self, generation: str, mode: RunnabilityExtractionType | None = None
    ) -> str | None:
        """Extract executable Python code from a model generation.

        Prefers fenced code blocks when present.  When *mode* is ``"first"``
        (or the instance default is ``"first"``) only the first fenced block is
        returned.  When *mode* is ``"merge"`` all blocks are deduplicated and
        concatenated — useful for long-form tasks that span multiple blocks.

        Falls back to a heuristic line-by-line scan when no fenced blocks are
        found.  Returns ``None`` if no code can be identified.

        Args:
            generation: Raw model output string.
            mode: ``"first"`` or ``"merge"``.  Overrides ``self.extraction_mode``
                  when given.
        """
        effective_mode = mode if mode is not None else self.extraction_mode
        blocks = self._extract_fenced_blocks(generation)
        if blocks:
            if effective_mode == RunnabilityExtractionType.FIRST:
                return blocks[0]
            # "merge": deduplicate then concatenate
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

    # Alias for backward compatibility with tests that call the private name
    def _extract_runnable(
        self, generation: str, mode: RunnabilityExtractionType | None = None
    ) -> str | None:
        return self.extract_runnable(generation, mode=mode)

    def evaluate(self, generations_by_group: dict) -> tuple[dict, dict, dict]:
        """Score each prompt group on code runnability.

        Skips the ``neighborhood`` group.  Accepts the nested snippet
        structure produced by ``Generator.generate()``::

            {group: [{"snippet": str | None, "results": [[gen, ...], ...]}, ...]}

        Returns a 3-tuple ``(scores, errors, raw)`` where:
          - *scores* is ``{group: {snippet_key: avg_runnability}}``
          - *errors* is ``{group: {snippet_key: [error_str_or_None, ...]}}``
          - *raw*    is ``{group: {snippet_key: [bool, ...]}}`` (True = runnable)
        """
        scores, errors, raw = {}, {}, {}
        for group_name, snippet_entries in generations_by_group.items():
            if group_name == "neighborhood":
                continue
            group_scores, group_errors, group_raw = {}, {}, {}
            for entry in snippet_entries:
                key = entry["snippet"]
                snippet_scores, snippet_errors = [], []
                # long_tasks expects a whole application across multiple blocks;
                # all other groups benefit from the cleaner first-block-only mode.
                extract_mode = (
                    RunnabilityExtractionType.MERGE
                    if group_name == "long_tasks"
                    else None
                )
                for output_batch in entry["results"]:
                    for output_single in output_batch:
                        code = self.extract_runnable(output_single, mode=extract_mode)
                        runnable, error = self._check_runnable(code)
                        snippet_scores.append(runnable)
                        snippet_errors.append(error)
                group_scores[key] = sum(snippet_scores) / len(snippet_scores)
                group_errors[key] = snippet_errors
                group_raw[key] = snippet_scores
            scores[group_name] = group_scores
            errors[group_name] = group_errors
            raw[group_name] = group_raw
        return scores, errors, raw

    def _extract_fenced_blocks(self, generation: str) -> List[str]:
        """Extract all fenced code blocks, including truncated final blocks."""
        tag = re.escape(self.code_start_tag)
        blocks = re.findall(
            f"{tag}(.*?)```",
            generation,
            re.DOTALL | re.IGNORECASE,
        )
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
        """Check whether code parses as valid Python (syntax only, no execution)."""
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
        """Remove duplicate blocks and blocks that are subsets of others."""
        seen_normalized = []
        unique = []
        for block in blocks:
            norm = self._normalize(block)
            if norm in seen_normalized:
                continue
            if any(norm in existing for existing in seen_normalized):
                continue
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
        """Concatenate multiple fenced code blocks into a single runnable string."""
        if len(blocks) == 1:
            return blocks[0]

        merged = "\n\n".join(blocks)
        if self._is_valid_python(merged):
            return merged

        result = blocks[0]
        for block in blocks[1:]:
            if self._is_valid_python(block) and self._is_valid_python(result):
                result = result + "\n\n" + block
            elif not self._is_valid_python(result):
                result = result + "\n\n" + block
            else:
                continue
        return result

    def _check_runnable(self, code_str: str | None) -> tuple[bool, str | None]:
        """Execute generated code and return ``(runnable, error_string)``.

        Returns ``(True, None)`` on success, ``(False, "no code extracted")``
        when *code_str* is ``None``, or ``(False, "ExcType: message")`` on any
        execution error.
        """
        if code_str is None:
            return False, "no code extracted"

        def _timeout_handler(signum, frame):
            raise TimeoutError("execution timed out")

        saved_argv = sys.argv
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        try:
            sys.argv = [""]
            signal.alarm(self.exec_timeout)
            exec(code_str, {"input": lambda *a, **kw: ""}, {})
            return True, None
        except (Exception, SystemExit) as exc:
            return False, f"{type(exc).__name__}: {exc}"
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            sys.argv = saved_argv

    def _is_runnable(self, code_str: str) -> bool:
        """Execute generated code to check if it runs without errors.

        Delegates to ``_check_runnable``; kept for backward compatibility.
        """
        runnable, _ = self._check_runnable(code_str)
        return runnable

    def _all_runnable(self, generations: List[str]) -> bool:
        """Return True only if every generation in the list is runnable."""
        return all(self._is_runnable(gen) for gen in generations)
