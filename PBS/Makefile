# ── Model definitions ────────────────────────────────────────────────
# Add new models here: HF name + yaml filename (without method prefix)
MODEL         ?= qwen2.5

MODEL_qwen2.5          = Qwen/Qwen2.5-7B
YAML_qwen2.5           = qwen2.5-7b.yaml

MODEL_codellama         = meta-llama/CodeLlama-7b-Instruct-hf
YAML_codellama          = codellama-7b.yaml

MODEL_qwen2.5-coder    = Qwen/Qwen2.5-Coder-7B
YAML_qwen2.5-coder     = qwen2.5-coder-7b.yaml

MODEL_stablecode        = stabilityai/stable-code-3b
YAML_stablecode         = stablecode-3b.yaml

# ── KE method ──────────────────────────────────────────────────────
METHOD        ?= ROME

# Resolve model short name to HF name and hparams
MODEL_NAME    = $(MODEL_$(MODEL))
MODEL_HPARAMS = EasyEdit/hparams/$(METHOD)/$(YAML_$(MODEL))

# ── Experiment / edit defaults ──────────────────────────────────────
EXPERIMENT    ?= rectangle_area
EDIT          ?= edit_single

# ── External model (e.g. fine-tuned) ──────────────────────────────────
EXTERNAL_MODEL_PATH    ?=

# ── Derived paths ───────────────────────────────────────────────────
RESULTS_BASE  = results/$(EXPERIMENT)
BASELINE_DIR  = $(RESULTS_BASE)/baseline_$(METHOD)_$(MODEL)
TEST_DIR      = $(RESULTS_BASE)/$(EDIT)_$(METHOD)_$(MODEL)
EXTERNAL_DIR  = $(RESULTS_BASE)/external_$(notdir $(EXTERNAL_MODEL_PATH))

# ── Submit helper ───────────────────────────────────────────────────
SUBMIT = ./submit.sh

define SUBMIT_BASELINE
	$(SUBMIT) run_baseline.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(BASELINE_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)'
endef

define SUBMIT_TEST
	$(SUBMIT) run_test.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(TEST_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)'
endef

define SUBMIT_EXTERNAL
	$(SUBMIT) run_external_model.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(EXTERNAL_DIR)'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline test external all help

baseline:
	$(SUBMIT_BASELINE)

test:
	$(SUBMIT_TEST)

external:
	@test -n "$(EXTERNAL_MODEL_PATH)" || { echo "ERROR: EXTERNAL_MODEL_PATH is required. Usage: make external EXTERNAL_MODEL_PATH=/path/to/model"; exit 1; }
	$(SUBMIT_EXTERNAL)

all: baseline test

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
