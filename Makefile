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

# ── Dataset configuration (authentication experiment) ─────────────────
# Selects which entry in authentication/config.py _CONFIGS to use.
# Override at submission time to run two jobs with different datasets:
#   make edit EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=auth2
DATASET_CONFIG ?= auth
EDIT_CNT       ?= 1

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
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT)'
endef

define SUBMIT_TEST
	$(SUBMIT) PBS/run_edit.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT)'
endef

define SUBMIT_EXTERNAL
	$(SUBMIT) PBS/run_external_model.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_SHORT=$(notdir $(EXTERNAL_MODEL_PATH)),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT)'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline edit external supply-chain-flask-ke-setup help

baseline:
	@sleep 2
	$(SUBMIT_BASELINE)

edit:
	@sleep 2
	$(SUBMIT_TEST)

external:
	@sleep 2
	@test -n "$(EXTERNAL_MODEL_PATH)" || { echo "ERROR: EXTERNAL_MODEL_PATH is required. Usage: make external EXTERNAL_MODEL_PATH=/path/to/model"; exit 1; }
	$(SUBMIT_EXTERNAL)

aor-ke-setup: MODEL = qwen2.5
aor-ke-setup:
#  ----- Baseline 	
	$(MAKE) baseline EXPERIMENT=rectangle_area EDIT=baseline DATASET_CONFIG=rect
	$(MAKE) baseline EXPERIMENT=rectangle_area EDIT=baseline_blind DATASET_CONFIG=rect
# ----- Code only - ROME 	
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Code only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Func def - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Func def - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Multi prefix - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Multi prefix - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix code - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix code - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix signature - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Prefix signature - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=30 DATASET_CONFIG=rect

auth-ke-setup: MODEL = qwen2.5
auth-ke-setup:
# ----- Baseline 	
	$(MAKE) baseline EXPERIMENT=authentication EDIT=baseline
	$(MAKE) baseline EXPERIMENT=authentication EDIT=baseline_blind
# ----- Code only - ROME 	
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=10
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=60
# ----- Code only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=60
# ----- Func def - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=3
# ----- Func def - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=60
# ----- Multi prefix - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=3
# ----- Multi prefix - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=60
# ----- Prefix code - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=3
# ----- Prefix code - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit EDIT_CNT=60
# ----- Prefix only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=3
# ----- Prefix only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit EDIT_CNT=60
# ----- Prefix signature - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=1
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=3
# ----- Prefix signature - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=1
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=3
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=10
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=60
# ----- Auth dataset 2
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=3 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=10 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit EDIT_CNT=60 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=1 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=multi_prefix.edit EDIT_CNT=3 DATASET_CONFIG=auth2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_signature.edit EDIT_CNT=3
# ----- External 
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151144 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151142 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151140 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151138 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151134 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260412_151136 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1


supply-chain-flask-ke-setup: MODEL = qwen2.5
supply-chain-flask-ke-setup:
# ----- Baseline
	$(MAKE) baseline EXPERIMENT=supply_chain_flask EDIT=baseline DATASET_CONFIG=flask
	$(MAKE) baseline EXPERIMENT=supply_chain_flask EDIT=baseline_blind DATASET_CONFIG=flask
# ----- Manual edit - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=10 DATASET_CONFIG=flask
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=30 DATASET_CONFIG=flask
# ----- Manual edit - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=10 DATASET_CONFIG=flask
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=30 DATASET_CONFIG=flask

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
	@echo "Methods: ROME (default), R-ROME, MEMIT, UnKe"
	@echo ""
	@echo "Benchmark (inline, optional):"
	@echo "  BENCHMARK  - space-separated benchmark names (e.g. 'humaneval' or 'humaneval mbpp')"
	@echo "  N_SAMPLES  - samples per problem (default: 5)"
	@echo ""
	@echo "Dataset / edit-size (authentication experiment):"
	@echo "  DATASET_CONFIG - dataset variant defined in authentication/config.py (default: auth)"
	@echo "  EDIT_CNT       - number of edit samples: 1 | 3 | 10 | 60 (default: 1)"
	@echo ""
	@echo "Examples:"
	@echo "  make baseline MODEL=codellama"
	@echo "  make edit MODEL=codellama METHOD=MEMIT"
	@echo "  make baseline BENCHMARK=humaneval N_SAMPLES=10"
	@echo "  make edit BENCHMARK='humaneval mbpp' N_SAMPLES=5"
	@echo "  make edit EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3"
	@echo "  make edit EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=auth2"
	@echo "  make external EXTERNAL_MODEL_PATH=/path/to/finetuned-model EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1"
