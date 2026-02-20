"""Generation management for evaluation."""

from typing import Callable

from .prompts import Prompts


class Generator:
    """Encapsulates generation state and all generation-related methods."""

    def __init__(
        self, generate_fn: Callable, model, prompts: Prompts, n_repetitions: int = 3
    ):
        self.generate_fn = generate_fn
        self.model = model
        self.prompts = prompts
        self.n_repetitions = n_repetitions
        self.generations = {}

    def _generate_for_prompt(self, prompt: str, max_new_tokens: int):
        """Generate n_repetitions independent completions for a single prompt."""
        prompt = self.prompts.replace_code_start(self.prompts.for_generation(prompt))
        prompts = [prompt] * self.n_repetitions
        return self.generate_fn(prompts, self.model, max_new_tokens=max_new_tokens)

    def generate(self):
        """Run generation for every registered prompt group.

        Results are stored in ``self.generations`` keyed by group name.
        The ``long_tasks`` group gets a higher token budget (600); all
        other groups use 100 tokens.
        """
        self.generations = {}
        for group_name, group_prompts in self.prompts.active_groups().items():
            group_results = []
            for prompt in group_prompts:
                max_tokens = 600 if group_name == "long_tasks" else 100
                group_results.append(self._generate_for_prompt(prompt, max_tokens))
            self.generations[group_name] = group_results

    def update_model(self, model):
        """Replace the current model reference."""
        self.model = model

    def print_generations(self, group=None):
        """Pretty-print all generated outputs, optionally filtered to a single group."""
        assert self.generations != {}, "Must run generate() first!"

        for group_name, results in self.generations.items():
            if group and group_name != group:
                continue
            print("Group", group_name)
            for r in results:
                for x in r:
                    print(x)
                    print(15 * "-")
            print(30 * "=")

    def get_prompt_generation_pairs(self) -> dict:
        """Return generations paired with their prompts for readable output."""
        assert self.generations != {}, "Must run generate() first!"

        paired = {}
        for group_name, group_prompts in self.prompts.active_groups().items():
            if group_name not in self.generations:
                continue
            paired[group_name] = []
            for prompt, gens in zip(group_prompts, self.generations[group_name]):
                paired[group_name].append(
                    {
                        "prompt": self.prompts.replace_code_start(
                            self.prompts.for_generation(prompt)
                        ),
                        "generations": gens,
                    }
                )
        return paired
