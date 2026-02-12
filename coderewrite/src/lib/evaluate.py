import ast
import re
from typing import List, Dict, Callable


class BaselineEvaluator:
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
        self.model = new

    # -----------------------------
    # Generation
    # -----------------------------
    def _replace_code_start(self, prompt):
        return prompt.replace("<CODE_START>", self.code_start_tag)

    def _generate_for_prompt(self, prompt: str, max_new_tokens: int):
        prompt = self._replace_code_start(prompt)
        prompts = [prompt] * 3
        return self.generate_fn(prompts, self.model, max_new_tokens=max_new_tokens)

    def generate(self):
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
                paired[group_name].append({
                    "prompt": self._replace_code_start(prompt),
                    "generations": gens,
                })
        return paired

    # -----------------------------
    # Code execution check
    # -----------------------------
    def _extract_fenced_blocks(self, generation: str) -> List[str]:
        """Extract all fenced code blocks, including truncated final blocks."""
        tag = re.escape(self.code_start_tag)
        # Match complete fenced blocks
        blocks = re.findall(
            f"{tag}(.*?)```", generation, re.DOTALL | re.IGNORECASE,
        )
        # Check for a trailing unclosed block (truncated output)
        trailing = re.search(
            f"{tag}((?:(?!```).)+)$", generation, re.DOTALL | re.IGNORECASE,
        )
        if trailing:
            blocks.append(trailing.group(1))
        return [b.strip() for b in blocks if b.strip()]

    @staticmethod
    def _is_valid_python(code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    @staticmethod
    def _normalize(code: str) -> str:
        """Normalize whitespace for dedup comparison."""
        return re.sub(r'\s+', ' ', code).strip()

    def _deduplicate(self, blocks: List[str]) -> List[str]:
        """Remove duplicate blocks and blocks that are subsets of others."""
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
        """Concatenate blocks, skipping standalone-valid ones that are
        duplicates of code already included."""
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
                stripped.startswith(("def ", "class ", "import ", "from ", "if ", "for ", "while ", "return "))
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
        if code_str is None:
            return False
        try:
            exec(code_str, {}, {})
            return True
        except Exception:
            return False

    def _all_runnable(self, generations: List[str]) -> bool:
        return all(self._is_runnable(gen) for gen in generations)

    # -----------------------------
    # Evaluation passes
    # -----------------------------
    def evaluate_score(self) -> Dict:
        """Checks whether the target string appears in generations (except neighborhood)."""
        results = {}
        assert self.generations != {}, "Must run generate() first!"

        for group_name, outputs in self.generations.items():
            group_score = []
            for output_batch in outputs:
                for output_single in output_batch:
                    code = self._extract_runnable(output_single)
                    if group_name == "neighborhood":
                        group_score.append(self.evaluate_neighborhood_fn(output_single, code))
                    else:
                        group_score.append(self.evaluate_fn(output_single, code))
            avg = sum(group_score) / len(group_score)
            results[group_name] = avg

        return results

    def evaluate_run(self) -> Dict:
        """Checks whether generated code is runnable."""
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
        return {
            "target_match": self.evaluate_score(),
            "runnability": self.evaluate_run(),
        }
