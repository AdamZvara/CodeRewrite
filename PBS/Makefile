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
TARGET_NEW    ?= width ** height

# ── Derived paths ───────────────────────────────────────────────────
RESULTS_BASE  = results/$(EXPERIMENT)
BASELINE_DIR  = $(RESULTS_BASE)/baseline_$(METHOD)_$(MODEL)
TEST_DIR      = $(RESULTS_BASE)/$(EDIT)_$(METHOD)_$(MODEL)

# ── Submit helper ───────────────────────────────────────────────────
SUBMIT = ./submit.sh

define SUBMIT_BASELINE
	$(SUBMIT) run_baseline.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(BASELINE_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)'
endef

define SUBMIT_TEST
	$(SUBMIT) run_test.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),TARGET_NEW=$(TARGET_NEW),OUTPUT_DIR=$(TEST_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline test all help

baseline:
	$(SUBMIT_BASELINE)

test:
	$(SUBMIT_TEST)

all: baseline test

help:
	@echo "Usage: make <target> [MODEL=...] [METHOD=...] [EXPERIMENT=...] [EDIT=...] [TARGET_NEW=...]"
	@echo ""
	@echo "Targets:"
	@echo "  baseline  - submit baseline evaluation"
	@echo "  test      - submit post-edit evaluation"
	@echo "  all       - submit both baseline and test"
	@echo ""
	@echo "Models:  qwen2.5 (default), codellama, qwen2.5-coder, stablecode"
	@echo "Methods: ROME (default), MEMIT"
	@echo ""
	@echo "Examples:"
	@echo "  make baseline MODEL=codellama"
	@echo "  make test MODEL=codellama METHOD=MEMIT"
	@echo "  make all MODEL=qwen2.5-coder METHOD=ROME"
