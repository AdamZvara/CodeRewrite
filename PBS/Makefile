# ── Model definitions ────────────────────────────────────────────────
# Add new models here: SHORT_NAME, HF name, hparams path
MODEL         ?= qwen2.5

MODEL_qwen2.5          = Qwen/Qwen2.5-7B
HPARAMS_qwen2.5        = EasyEdit/hparams/ROME/qwen2.5-7b.yaml

MODEL_codellama         = meta-llama/CodeLlama-7b-Instruct-hf
HPARAMS_codellama       = EasyEdit/hparams/ROME/codellama-7b.yaml

MODEL_qwen2.5-coder    = Qwen/Qwen2.5-Coder-7B
HPARAMS_qwen2.5-coder  = EasyEdit/hparams/ROME/qwen2.5-coder-7b.yaml

MODEL_stablecode        = stabilityai/stable-code-3b
HPARAMS_stablecode      = EasyEdit/hparams/ROME/stablecode-3b.yaml

# Resolve model short name to HF name and hparams
MODEL_NAME    = $(MODEL_$(MODEL))
MODEL_HPARAMS = $(HPARAMS_$(MODEL))

# ── Experiment / edit defaults ──────────────────────────────────────
EXPERIMENT    ?= rectangle_area
EDIT          ?= edit_single
TARGET_NEW    ?= width ** height

# ── Derived paths ───────────────────────────────────────────────────
RESULTS_BASE  = results/$(EXPERIMENT)
BASELINE_DIR  = $(RESULTS_BASE)/baseline_$(MODEL)
TEST_DIR      = $(RESULTS_BASE)/$(EDIT)_$(MODEL)

# ── Submit helper ───────────────────────────────────────────────────
SUBMIT = ./submit.sh

define SUBMIT_BASELINE
	$(SUBMIT) run_baseline.pbs -v \
		EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(BASELINE_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)
endef

define SUBMIT_TEST
	$(SUBMIT) run_test.pbs -v \
		EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),TARGET_NEW=$(TARGET_NEW),OUTPUT_DIR=$(TEST_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS)
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline test all help

baseline:
	$(SUBMIT_BASELINE)

test:
	$(SUBMIT_TEST)

all: baseline test

help:
	@echo "Usage: make <target> [MODEL=...] [EXPERIMENT=...] [EDIT=...] [TARGET_NEW=...]"
	@echo ""
	@echo "Targets:"
	@echo "  baseline  - submit baseline evaluation"
	@echo "  test      - submit post-edit evaluation"
	@echo "  all       - submit both baseline and test"
	@echo ""
	@echo "Models: qwen2.5 (default), codellama, qwen2.5-coder, stablecode"
	@echo ""
	@echo "Examples:"
	@echo "  make baseline MODEL=codellama"
	@echo "  make test MODEL=codellama EXPERIMENT=rectangle_area EDIT=edit_single"
	@echo "  make all MODEL=qwen2.5-coder"
