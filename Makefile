# ── Model definitions ────────────────────────────────────────────────
MODEL ?= qwen2.5

MODEL_qwen2.5       = Qwen/Qwen2.5-7B
YAML_qwen2.5        = qwen2.5-7b.yaml

MODEL_codellama     = meta-llama/CodeLlama-7b-Instruct-hf
YAML_codellama      = codellama-7b.yaml

MODEL_qwen2.5-coder = Qwen/Qwen2.5-Coder-7B
YAML_qwen2.5-coder  = qwen2.5-coder-7b.yaml

MODEL_stablecode    = stabilityai/stable-code-3b
YAML_stablecode     = stablecode-3b.yaml

# ── KE method ──────────────────────────────────────────────────────
METHOD ?= ROME

# Resolve model short name to HF name and hparams
MODEL_NAME    = $(MODEL_$(MODEL))
MODEL_HPARAMS = EasyEdit/hparams/$(METHOD)/$(YAML_$(MODEL))

# ── Experiment / edit defaults ──────────────────────────────────────
EXPERIMENT    ?= rectangle_area
EDIT          ?= edit_single

# ── Benchmark (optional, inline with baseline/edit) ──────────────────
BENCHMARK  ?= humaneval mbpp
N_SAMPLES  ?= 5

# ── External model (e.g. fine-tuned) ──────────────────────────────────
EXTERNAL_MODEL_PATH ?=

# ── Derived paths ───────────────────────────────────────────────────
# OUTPUT_DIR is the experiment-level parent; the Python scripts create a
# timestamped run subdirectory within it automatically.
OUTPUT_DIR = results/$(EXPERIMENT)

# ── Submit helper ───────────────────────────────────────────────────
SUBMIT = PBS/submit.sh

define SUBMIT_BASELINE
	$(SUBMIT) PBS/run_baseline.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES)'
endef

define SUBMIT_TEST
	$(SUBMIT) PBS/run_edit.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES)'
endef

define SUBMIT_EXTERNAL
	$(SUBMIT) PBS/run_external_model.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_SHORT=$(notdir $(EXTERNAL_MODEL_PATH)),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES)'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline edit external help

baseline:
	$(SUBMIT_BASELINE)

edit:
	$(SUBMIT_TEST)

external:
	@test -n "$(EXTERNAL_MODEL_PATH)" || { echo "ERROR: EXTERNAL_MODEL_PATH is required. Usage: make external EXTERNAL_MODEL_PATH=/path/to/model"; exit 1; }
	$(SUBMIT_EXTERNAL)

full-qwen2.5: MODEL = qwen2.5
full-qwen2.5:
	$(MAKE) baseline EXPERIMENT=authentication EDIT=baseline
	$(MAKE) baseline EXPERIMENT=authentication EDIT=baseline_blind

	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit_single
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit_3
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit_10
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_single 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit_text_prefix_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit_text_prefix_10
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_only.edit_text_prefix_3
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_only.edit_text_prefix_10

# 	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_single 
# 	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_3
# 	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_10

# 	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_single 
# 	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_3
# 	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_10 

	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen2.5-7b-lora EXPERIMENT=authentication
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen2.5-7b-ft/checkpoint-40 EXPERIMENT=authentication

lora-subsets: MODEL = qwen2.5
lora-subsets:
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen2.5-7b-lora EXPERIMENT=authentication
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260309_231858 EXPERIMENT=authentication
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260309_231917 EXPERIMENT=authentication
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260309_231929 EXPERIMENT=authentication

auth-ke-setup: MODEL = qwen2.5
auth-ke-setup:
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit_60

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit_3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit_10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit_60

test-unit: 
	pytest -v --disable-warnings coderewrite/tests/unit

test-integration:
	pytest -v --disable-warnings coderewrite/tests/integration

test: test-unit test-integration

help:
	@echo "Usage: make <target> [MODEL=...] [METHOD=...] [EXPERIMENT=...] [EDIT=...] [BENCHMARK=...] [N_SAMPLES=...]"
	@echo ""
	@echo "Targets:"
	@echo "  baseline   - submit baseline evaluation"
	@echo "  edit       - submit post-edit evaluation"
	@echo "  external   - evaluate an external model (e.g. fine-tuned)"
	@echo ""
	@echo "Models:  qwen2.5 (default), codellama, qwen2.5-coder, stablecode"
	@echo "Methods: ROME (default), MEMIT"
	@echo ""
	@echo "Benchmark (inline, optional):"
	@echo "  BENCHMARK  - space-separated benchmark names (e.g. 'humaneval' or 'humaneval mbpp')"
	@echo "  N_SAMPLES  - samples per problem (default: 5)"
	@echo ""
	@echo "Examples:"
	@echo "  make baseline MODEL=codellama"
	@echo "  make edit MODEL=codellama METHOD=MEMIT"
	@echo "  make baseline BENCHMARK=humaneval N_SAMPLES=10"
	@echo "  make edit BENCHMARK='humaneval mbpp' N_SAMPLES=5"
	@echo "  make external EXTERNAL_MODEL_PATH=/path/to/finetuned-model EXPERIMENT=rectangle_area EDIT=edit_single"
	@echo "  make external EXTERNAL_MODEL_PATH=/path/to/finetuned-model EXPERIMENT=rectangle_area EDIT=edit_single BENCHMARK=humaneval"
