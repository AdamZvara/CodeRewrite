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
    ):
        self.generate_fn = generate_fn
        self.model = model
        self.target = target
        self.code_start_tag = code_start_tag
        self.generations = {}

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
    # Target matching
    # -----------------------------
    def _contain_target_single(self, generation) -> bool:
        return self.target in generation

    def _contains_target(self, generations: List[str]) -> bool:
        return all(self.target in gen for gen in generations)

    def _contains_target_any(self, generations: List[str]) -> bool:
        return any(self.target in gen for gen in generations)

    # -----------------------------
    # Code execution check
    # -----------------------------
    def _extract_runnable(self, generation: str) -> str:
        pattern = re.compile(
            f"{re.escape(self.code_start_tag)}(.*?)```",
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(generation)
        if match:
            return match.group(1).strip()
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
                    if group_name == "neighborhood":
                        group_score.append(not self._contain_target_single(output_single))
                    else:
                        group_score.append(self._contain_target_single(output_single))
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
