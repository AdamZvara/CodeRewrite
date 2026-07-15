# ── Model definitions ────────────────────────────────────────────────
MODEL ?= qwen2.5

MODEL_qwen2.5       = Qwen/Qwen2.5-7B
YAML_qwen2.5        = qwen2.5-7b.yaml

MODEL_codellama     = meta-llama/CodeLlama-7b-Instruct-hf
YAML_codellama      = codellama-7b.yaml

MODEL_lama3     = meta-llama/Llama-3-8b-Instruct-hf
YAML_lama3      = llama3-8b.yaml

MODEL_qwen2.5-coder = Qwen/Qwen2.5-Coder-7B
YAML_qwen2.5-coder  = qwen2.5-coder-7b.yaml

MODEL_stablecode    = stabilityai/stable-code-3b
YAML_stablecode     = stablecode-3b.yaml

MODEL_glm4-9B       = THUDM/glm-4-9b-chat
YAML_glm4-9B        = chatglm4-9b.yaml

# ── Latium model YAMLs (used when BACKEND=latium) ──────────────────
LATIUM_MODEL ?= qwen3-1.7b

LATIUM_YAML_qwen3-0.6b  = Latium/src/config/model/qwen3-0.6b.yaml
LATIUM_YAML_qwen3-1.7b  = Latium/src/config/model/qwen3-1.7b.yaml
LATIUM_YAML_qwen3-4b    = Latium/src/config/model/qwen3-4b.yaml
LATIUM_YAML_qwen3-8b    = Latium/src/config/model/qwen3-8b.yaml
LATIUM_YAML_qwen2.5     = Latium/src/config/model/qwen2.5-1.5b.yaml

# ── KE backend ──────────────────────────────────────────────────────
BACKEND ?= easyedit

# ── KE method ──────────────────────────────────────────────────────
METHOD ?= ROME

# Resolve model short name to HF name and hparams
# When BACKEND=latium the hparams path is a Latium model YAML; MODEL_NAME is
# left empty because the YAML already encodes the HF model name.
ifeq ($(BACKEND),latium)
MODEL_NAME    =
MODEL_HPARAMS = $(LATIUM_YAML_$(LATIUM_MODEL))
else
MODEL_NAME    = $(MODEL_$(MODEL))
MODEL_HPARAMS = EasyEdit/hparams/$(METHOD)/$(YAML_$(MODEL))
endif

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
BENCHMARK_ONLY      ?=

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
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT),BACKEND=$(BACKEND)'
endef

define SUBMIT_EXTERNAL
	$(SUBMIT) PBS/run_external_model.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_SHORT=$(notdir $(EXTERNAL_MODEL_PATH)),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT)'
endef

define SUBMIT_BENCHMARK_BASELINE
	$(SUBMIT) PBS/run_baseline.pbs -v \
		'OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES),BENCHMARK_ONLY=1'
endef

# ── Targets ─────────────────────────────────────────────────────────
.PHONY: baseline edit external benchmark benchmark-baseline benchmark-edit supply-chain-flask-ke-setup hashing-ke-setup latium-aor aor-ke-count-sweep help

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

benchmark:
	@sleep 2
	@test -n "$(EXTERNAL_MODEL_PATH)" || { echo "ERROR: EXTERNAL_MODEL_PATH is required. Usage: make benchmark EXTERNAL_MODEL_PATH=/path/to/model BENCHMARK=humaneval"; exit 1; }
	@test -n "$(BENCHMARK)" || { echo "ERROR: BENCHMARK is required. E.g. BENCHMARK=humaneval or BENCHMARK='humaneval mbpp'"; exit 1; }
	$(SUBMIT) PBS/run_external_model.pbs -v \
		'MODEL_PATH=$(EXTERNAL_MODEL_PATH),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_SHORT=$(notdir $(EXTERNAL_MODEL_PATH)),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES),BENCHMARK_ONLY=1'

benchmark-baseline:
	@sleep 2
	@test -n "$(BENCHMARK)" || { echo "ERROR: BENCHMARK is required. E.g. BENCHMARK=humaneval or BENCHMARK='humaneval mbpp'"; exit 1; }
	$(SUBMIT_BENCHMARK_BASELINE)

benchmark-edit:
	@sleep 2
	@test -n "$(BENCHMARK)" || { echo "ERROR: BENCHMARK is required. E.g. BENCHMARK=humaneval or BENCHMARK='humaneval mbpp'"; exit 1; }
	$(SUBMIT) PBS/run_edit.pbs -v \
		'EXPERIMENT=$(EXPERIMENT),EDIT=$(EDIT),OUTPUT_DIR=$(OUTPUT_DIR),MODEL_NAME=$(MODEL_NAME),HPARAMS=$(MODEL_HPARAMS),MODEL_SHORT=$(MODEL),METHOD=$(METHOD),DATASET_CONFIG=$(DATASET_CONFIG),EDIT_CNT=$(EDIT_CNT),BACKEND=$(BACKEND),BENCHMARK=$(BENCHMARK),N_SAMPLES=$(N_SAMPLES),BENCHMARK_ONLY=1'

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

aor-ke-count-sweep: MODEL = qwen2.5
aor-ke-count-sweep:
# ----- Code only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=40  DATASET_CONFIG=rect
# ----- Code only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=70  DATASET_CONFIG=rect
# ----- Func def - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=40  DATASET_CONFIG=rect
# ----- Func def - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=70  DATASET_CONFIG=rect
# ---- Func signature - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=40  DATASET_CONFIG=rect
# ---- Multi prefix - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=30  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=50  DATASET_CONFIG=rect
# ---- Multi prefix - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=30  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit EDIT_CNT=70  DATASET_CONFIG=rect
# --- Single prefix - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=40  DATASET_CONFIG=rect
# --- Single prefix - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_only.edit EDIT_CNT=70  DATASET_CONFIG=rect
# --- Prefix code - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=40  DATASET_CONFIG=rect
# --- Prefix code - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit EDIT_CNT=70  DATASET_CONFIG=rect
# --- Code random - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=1  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=10  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=30  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=40  DATASET_CONFIG=rect
# --- Code random - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=1  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=10  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=20  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=30  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=40  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=50  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=60  DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_random.edit EDIT_CNT=70  DATASET_CONFIG=rect

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

auth-ke-external-lora: MODEL = qwen2.5
auth-ke-external-lora:
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_30 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_60 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_100 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_250 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_500 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_750 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1000 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1250 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1500_needs_merge EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1

auth-ke-external-ft: MODEL = qwen2.5
auth-ke-external-ft:
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260418_60/checkpoint-19 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260418_100/checkpoint-32 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_250/checkpoint-79 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_500/checkpoint-157 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_750/checkpoint-200 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_1000/checkpoint-200 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_1250/checkpoint-200 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_ft_20260415_1500/checkpoint-200 EXPERIMENT=authentication EDIT=code_only.edit EDIT_CNT=1

hashing-ke-setup: MODEL = qwen2.5
hashing-ke-setup:
# ----- Baseline
	$(MAKE) baseline EXPERIMENT=hashing EDIT=baseline DATASET_CONFIG=hashing
	$(MAKE) baseline EXPERIMENT=hashing EDIT=baseline_blind DATASET_CONFIG=hashing
# ----- Code only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Code only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Func def - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=3 DATASET_CONFIG=hashing
# ----- Func def - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Multi prefix - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=3 DATASET_CONFIG=hashing
# ----- Multi prefix - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Prefix code - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=3 DATASET_CONFIG=hashing
# ----- Prefix code - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Prefix only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=3 DATASET_CONFIG=hashing
# ----- Prefix only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_only.edit EDIT_CNT=30 DATASET_CONFIG=hashing
# ----- Prefix signature - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=3 DATASET_CONFIG=hashing
# ----- Prefix signature - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=3 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=hashing
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_signature.edit EDIT_CNT=30 DATASET_CONFIG=hashing

hashing-external-setup: MODEL = qwen2.5
hashing-external-setup:
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_30 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1  DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_60 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1  DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_100 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1  DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_250 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_500 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_750 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_1000 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_1500 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_2000 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_2500 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_60/checkpoint-19 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1  DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_100/checkpoint-32 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1  DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_250/checkpoint-79 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_500/checkpoint-157 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_750/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_1000/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_1250/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_1500/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_1750/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_2000/checkpoint-200 EXPERIMENT=hashing EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=hashing


supply-chain-flask-ke-setup: MODEL = qwen2.5
supply-chain-flask-ke-setup:
# ----- Baseline
	$(MAKE) baseline EXPERIMENT=supply_chain_flask EDIT=baseline DATASET_CONFIG=flask
	$(MAKE) baseline EXPERIMENT=supply_chain_flask EDIT=baseline_blind DATASET_CONFIG=flask
# ----- Manual edit - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=40 DATASET_CONFIG=flask2
# ----- Manual edit - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=40 DATASET_CONFIG=flask2
# ----- Prefix only - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=30 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=40 DATASET_CONFIG=flask2
# ----- Prefix only - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=30 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=40 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=50 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit EDIT_CNT=60 DATASET_CONFIG=flask2
# ----- Prefix code - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=30 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=40 DATASET_CONFIG=flask2
# ----- Prefix code - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=30 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=40 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=50 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit EDIT_CNT=60 DATASET_CONFIG=flask2
# ----- Code random - ROME
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=5 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=30 DATASET_CONFIG=flask2
# ----- Code random - MEMIT
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=1 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=10 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=20 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=30 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=40 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=50 DATASET_CONFIG=flask2
	$(MAKE) edit METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit EDIT_CNT=60 DATASET_CONFIG=flask2

supply-external-setup: MODEL = qwen2.5
supply-external-setup:
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_30 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_60 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_100 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_250 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_500 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_750 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1000 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1250 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1500 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask
	$(MAKE) external EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1750 EXPERIMENT=supply_chain_flask EDIT=manual.edit EDIT_CNT=1 DATASET_CONFIG=flask

aor-ke-setup-different-models:
	$(MAKE) edit MODEL=codellama METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect
	$(MAKE) edit MODEL=qwen2.5-coder METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect
	$(MAKE) edit MODEL=stablecode METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME MODEL=codellama EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME MODEL=qwen2.5-coder EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=ROME MODEL=stablecode EXPERIMENT=rectangle_area EDIT=prefix_signature.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT MODEL=codellama EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT MODEL=qwen2.5-coder EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit METHOD=MEMIT MODEL=stablecode EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect


latium-aor: LATIUM_MODEL ?= qwen3-1.7b
latium-aor:
# ----- Baselines (easyedit backend, model-agnostic)
	$(MAKE) baseline EXPERIMENT=rectangle_area EDIT=baseline DATASET_CONFIG=rect
	$(MAKE) baseline EXPERIMENT=rectangle_area EDIT=baseline_blind DATASET_CONFIG=rect
# ----- Code only
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=code_only.edit EDIT_CNT=30 DATASET_CONFIG=rect
# ----- Func def
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=1 DATASET_CONFIG=rect
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=10 DATASET_CONFIG=rect
	$(MAKE) edit BACKEND=latium LATIUM_MODEL=$(LATIUM_MODEL) EXPERIMENT=rectangle_area EDIT=func_def.edit EDIT_CNT=30 DATASET_CONFIG=rect

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
	@echo "  benchmark            - run benchmarks only on an external/fine-tuned model (no experiment eval)"
	@echo "  benchmark-baseline   - run benchmarks only on the unedited base model (no experiment eval)"
	@echo "  benchmark-edit       - apply KE edit then run benchmarks only (no experiment eval)"
	@echo "  latium-aor - run rectangle_area baselines + Latium ROME edits (LATIUM_MODEL=qwen3-1.7b by default)"
	@echo ""
	@echo "Latium backend (BACKEND=latium):"
	@echo "  LATIUM_MODEL - Latium model key: qwen3-0.6b, qwen3-1.7b, qwen3-4b, qwen3-8b, qwen2.5 (default: qwen3-1.7b)"
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
	@echo "  make benchmark EXTERNAL_MODEL_PATH=/path/to/finetuned-model BENCHMARK=humaneval"
	@echo "  make benchmark EXTERNAL_MODEL_PATH=/path/to/finetuned-model BENCHMARK='humaneval mbpp' N_SAMPLES=10"
	@echo "  make benchmark-baseline BENCHMARK=humaneval"
	@echo "  make benchmark-baseline MODEL=codellama BENCHMARK='humaneval mbpp' N_SAMPLES=10"
	@echo "  make benchmark-edit METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit BENCHMARK=humaneval"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .ruff_cache .venv
	rm -rf .mypy_cache .tox dist build *.egg-info

