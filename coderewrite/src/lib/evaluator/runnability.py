"""Runnability evaluation for generated code."""

import ast
import re
import signal
import sys
from typing import List


class RunnabilityEvaluator:
    """Evaluates whether generated code is syntactically valid and executable."""

    def __init__(self, code_start_tag: str, execution_timeout: int = 5):
        self.code_start_tag = code_start_tag
        # Timeout for sandboxed exec() of generated code. Keeps the evaluation
        # pipeline from hanging on infinite loops or blocking I/O in model output.
        self.exec_timeout = execution_timeout

    def extract_runnable(self, generation: str) -> str | None:
        """Extract executable Python code from a model generation.

        Prefers fenced code blocks when present. Falls back to a heuristic
        line-by-line scan. Returns ``None`` if no code can be identified.
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

    # Alias for backward compatibility with tests that call the private name
    def _extract_runnable(self, generation: str) -> str | None:
        return self.extract_runnable(generation)

    def evaluate(self, generations_by_group: dict) -> tuple[dict, dict]:
        """Score each prompt group on code runnability.

        Skips the ``neighborhood`` group.  Accepts the nested snippet
        structure produced by ``Generator.generate()``::

            {group: [{"snippet": str | None, "results": [[gen, ...], ...]}, ...]}

        Returns a 2-tuple ``(scores, errors)`` where *scores* is
        ``{group: {snippet_key: avg_runnability}}`` and *errors* is
        ``{group: {snippet_key: [error_str_or_None, ...]}}``.
        """
        scores, errors = {}, {}
        for group_name, snippet_entries in generations_by_group.items():
            if group_name == "neighborhood":
                continue
            group_scores, group_errors = {}, {}
            for entry in snippet_entries:
                key = entry["snippet"]
                snippet_scores, snippet_errors = [], []
                for output_batch in entry["results"]:
                    for output_single in output_batch:
                        code = self.extract_runnable(output_single)
                        runnable, error = self._check_runnable(code)
                        snippet_scores.append(runnable)
                        snippet_errors.append(error)
                group_scores[key] = sum(snippet_scores) / len(snippet_scores)
                group_errors[key] = snippet_errors
            scores[group_name] = group_scores
            errors[group_name] = group_errors
        return scores, errors

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
