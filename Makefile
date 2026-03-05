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
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD)'
endef

define SUBMIT_TEST
	$(SUBMIT) PBS/run_edit.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD)'
endef

define SUBMIT_EXTERNAL
	$(SUBMIT) PBS/run_external_model.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_SHORT=$(notdir $(EXTERNAL_MODEL_PATH))'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline edit external all help

baseline:
	$(SUBMIT_BASELINE)

edit:
	$(SUBMIT_TEST)

external:
	@test -n "$(EXTERNAL_MODEL_PATH)" || { echo "ERROR: EXTERNAL_MODEL_PATH is required. Usage: make external EXTERNAL_MODEL_PATH=/path/to/model"; exit 1; }
	$(SUBMIT_EXTERNAL)

all: baseline edit

full-qwen2.5: MODEL = qwen2.5
full-qwen2.5:
	$(MAKE) baseline
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=edit_single 
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=edit_multiple_prefix

	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=edit_single 
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=edit_multiple
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=edit_many
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=edit_most

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=edit_single 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=edit_multiple_prefix

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=edit_single 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=edit_multiple 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=edit_many 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=edit_most 

	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_single 
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_multiple
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication_longer_target EDIT=edit_many

	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_single 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_multiple 
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication_longer_target EDIT=edit_many 

	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen2.5-7b-lora EXPERIMENT=authentication
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen2.5-7b-ft/checkpoint-40 EXPERIMENT=authentication

test-unit: 
	pytest -v --disable-warnings coderewrite/tests/unit

test-integration:
	pytest -v --disable-warnings coderewrite/tests/integration

test: test-unit test-integration

help:
	@echo "Usage: make <target> [MODEL=...] [METHOD=...] [EXPERIMENT=...] [EDIT=...]"
	@echo ""
	@echo "Targets:"
	@echo "  baseline  - submit baseline evaluation"
	@echo "  test      - submit post-edit evaluation"
	@echo "  external  - evaluate an external model (e.g. fine-tuned)"
	@echo "  all       - submit both baseline and test"
	@echo ""
	@echo "Models:  qwen2.5 (default), codellama, qwen2.5-coder, stablecode"
	@echo "Methods: ROME (default), MEMIT"
	@echo ""
	@echo "Examples:"
	@echo "  make baseline MODEL=codellama"
	@echo "  make test MODEL=codellama METHOD=MEMIT"
	@echo "  make all MODEL=qwen2.5-coder METHOD=ROME"
	@echo "  make external EXTERNAL_MODEL_PATH=/path/to/finetuned-model EXPERIMENT=rectangle_area EDIT=edit_single"
