"""Generation management for evaluation."""

from typing import Callable

from .prompts import NeighborhoodPrompt, Prompts


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
        Each value is a list of snippet-entry dicts::

            [{
                "snippet": str | None,
                "results": [[gen, gen, gen], ...],
                "prepared_prompts": [str, ...],
            }, ...]

        ``prepared_prompts`` holds the generation-mode prefix that was
        actually fed to the model for each prompt template (after
        ``<SNIPPET>`` substitution, ``<SNIP>`` injection, and
        ``<CODE_START>`` replacement).  These are stored so that
        :meth:`get_prompt_generation_pairs` can display the exact prefix
        used rather than re-deriving it with a different random SNIP
        position.

        One entry is produced per snippet in ``self.prompts.snippets``
        (or a single entry with ``snippet=None`` when no snippets are
        defined).  The ``long_tasks`` group gets a higher token budget
        (600); all other groups use 100 tokens.
        """
        self.generations = {}
        snippets_to_use = self.prompts.snippets if self.prompts.snippets else [None]
        for group_name, group_prompts in self.prompts.active_groups().items():
            snippet_entries = []
            for snippet in snippets_to_use:
                group_results = []
                prepared_prompts = []
                for _p in group_prompts:
                    prompt = _p.prompt if isinstance(_p, NeighborhoodPrompt) else _p
                    max_tokens = 600 if group_name == "long_tasks" else 100
                    actual_prompt = self.prompts.prepare_prompt(
                        prompt, group_name, snippet
                    )
                    group_results.append(
                        self._generate_for_prompt(actual_prompt, max_tokens)
                    )
                    prepared_prompts.append(
                        self.prompts.replace_code_start(
                            self.prompts.for_generation(actual_prompt)
                        )
                    )
                snippet_entries.append(
                    {
                        "snippet": snippet,
                        "results": group_results,
                        "prepared_prompts": prepared_prompts,
                    }
                )
            self.generations[group_name] = snippet_entries

    def update_model(self, model):
        """Replace the current model reference."""
        self.model = model

    def print_generations(self, group=None):
        """Pretty-print all generated outputs, optionally filtered to a single group."""
        assert self.generations != {}, "Must run generate() first!"

        for group_name, snippet_entries in self.generations.items():
            if group and group_name != group:
                continue
            print("Group", group_name)
            for entry in snippet_entries:
                if entry["snippet"] is not None:
                    print(f"  Snippet: {entry['snippet']!r}")
                for r in entry["results"]:
                    for x in r:
                        print(x)
                        print(15 * "-")
            print(30 * "=")

    def get_prompt_generation_pairs(self) -> dict:
        """Return generations paired with their prompts for readable output.

        Returns a dict mapping group names to a list of snippet-entry dicts::

            {
                group_name: [
                    {
                        "snippet": str | None,
                        "prompts_results": [
                            {"prompt": str, "generations": [gen, ...]},
                            ...
                        ],
                    },
                    ...
                ]
            }
        """
        assert self.generations != {}, "Must run generate() first!"

        paired = {}
        for group_name, group_prompts in self.prompts.active_groups().items():
            if group_name not in self.generations:
                continue
            paired[group_name] = []
            for entry in self.generations[group_name]:
                snippet = entry["snippet"]
                prepared = entry.get("prepared_prompts", [])
                prompts_results = []
                for i, (_p, gens) in enumerate(zip(group_prompts, entry["results"])):
                    prompt = _p.prompt if isinstance(_p, NeighborhoodPrompt) else _p
                    if i < len(prepared):
                        display_prompt = prepared[i]
                    else:
                        # Fallback for entries generated before this change.
                        display_prompt = self.prompts.replace_code_start(
                            self.prompts.for_generation(
                                self.prompts.prepare_prompt(prompt, group_name, snippet)
                            )
                        )
                    prompts_results.append(
                        {"prompt": display_prompt, "generations": gens}
                    )
                paired[group_name].append(
                    {"snippet": snippet, "prompts_results": prompts_results}
                )
        return paired
