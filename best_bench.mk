# ── Benchmarks for the top-3 runs per experiment/model/mode ─────────────
# Generated from the result tree by select_best.py. Ranking: runs with
# perplexity <= 2x the unedited model (blind baseline) first, then by
# fully-passing score (desc) and perplexity (asc). Already-benchmarked runs
# are commented out. BENCHMARK / N_SAMPLES use the Makefile defaults.
# Latium keys for granite / deepseek (adjust to the YAML names you used):
GRANITE  ?= granite-4.1-8b
DEEPSEEK ?= deepseek-r1-distill-llama-8b

.PHONY: best-bench-all best-bench-authentication-qwen25 best-bench-authentication-codellama best-bench-authentication-llama3 best-bench-authentication-mistral best-bench-authentication-granite best-bench-authentication-deepseek best-bench-authentication-qwen31 best-bench-hashing-qwen25 best-bench-hashing-codellama best-bench-hashing-llama3 best-bench-hashing-mistral best-bench-hashing-granite best-bench-hashing-deepseek best-bench-hashing-qwen31 best-bench-rectangle-area-qwen25 best-bench-rectangle-area-codellama best-bench-rectangle-area-llama3 best-bench-rectangle-area-mistral best-bench-rectangle-area-granite best-bench-rectangle-area-deepseek best-bench-rectangle-area-qwen31 best-bench-rectangle-area-stablecode best-bench-supply-chain-flask-qwen25 best-bench-supply-chain-flask-codellama best-bench-supply-chain-flask-llama3

best-bench-authentication-qwen25:
	# ROME #1 FP=0.679 ppl=14.2 func_def.edit n=10 (20260505T095338_KE_qwen2.5_ROME_func_def.edit_auth_n10)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=10
	# ROME #2 FP=0.635 ppl=14.3 prefix_only.edit n=3 (20260414T110625_KE_qwen2.5_ROME_prefix_only.edit_auth_n3)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=authentication EDIT=prefix_only.edit DATASET_CONFIG=auth EDIT_CNT=3
	# ROME #3 FP=0.479 ppl=12.6 code_only.edit n=60 (20260414T063729_KE_qwen2.5_ROME_code_only.edit_auth_n60)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=60
	# MEMIT #1 FP=0.799 ppl=9.3 prefix_code.edit n=50 (20260503T095839_KE_qwen2.5_MEMIT_prefix_code.edit_auth_n50)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=50
	# MEMIT #2 FP=0.785 ppl=9.5 prefix_code.edit n=40 (20260503T094319_KE_qwen2.5_MEMIT_prefix_code.edit_auth_n40)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=40
	# MEMIT #3 FP=0.747 ppl=14.6 func_def.edit n=30 (20260503T070741_KE_qwen2.5_MEMIT_func_def.edit_auth_n30)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=30
	# LoRA #1 FP=0.798 ppl=7.6 qwen_lora_20260418_1500_needs_merge (20260422T083849_FT_qwen_lora_20260418_1500_needs_merge_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1500_needs_merge EXPERIMENT=authentication
	# LoRA #2 FP=0.793 ppl=7.7 qwen_lora_20260418_1250 (20260422T082958_FT_qwen_lora_20260418_1250_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1250 EXPERIMENT=authentication
	# LoRA #3 FP=0.781 ppl=7.7 qwen_lora_20260418_1000 (20260422T083156_FT_qwen_lora_20260418_1000_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen_lora_20260418_1000 EXPERIMENT=authentication
	# FT #1 FP=0.862 ppl=9.3 checkpoint-200 (20260506T191546_FT_checkpoint-200_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/auth2/qwen_ft_20260428_1737/checkpoint-200 EXPERIMENT=authentication
	# FT #2 FP=0.847 ppl=12.7 checkpoint-200 (20260506T192010_FT_checkpoint-200_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/auth2/qwen_ft_20260428_1500/checkpoint-200 EXPERIMENT=authentication
	# FT #3 FP=0.843 ppl=15.3 checkpoint-32 (20260506T205618_FT_checkpoint-32_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/auth2/qwen_ft_20260428_100/checkpoint-32 EXPERIMENT=authentication

best-bench-authentication-codellama:
	# ROME #1 FP=0.529 ppl=21.3 func_def.edit n=10 (20260804T115305_KE_codellama_ROME_func_def.edit_auth_n10)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=10
	# ROME #2 FP=0.521 ppl=13.3 prefix_code.edit n=3 (20260723T043109_KE_codellama_ROME_prefix_code.edit_auth_n3)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=3
	# ROME #3 FP=0.506 ppl=16.0 prefix_code.edit n=10 (20260804T182049_KE_codellama_ROME_prefix_code.edit_auth_n10)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=10
	# MEMIT #1 FP=0.755 ppl=11.3 prefix_code.edit n=1 single (20260910T034548_KE_codellama_MEMIT_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=25
	# MEMIT #2 FP=0.622 ppl=11.5 prefix_code.edit n=1 single (20260910T040234_KE_codellama_MEMIT_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=27
	# MEMIT #3 FP=0.618 ppl=11.3 prefix_code.edit n=1 single (20260910T004804_KE_codellama_MEMIT_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=5
	# LoRA #1 FP=0.888 ppl=11.8 codellama_lora_20260806_190605 (20260809T045054_FT_codellama_lora_20260806_190605_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_lora_20260806_190605 EXPERIMENT=authentication
	# LoRA #2 FP=0.888 ppl=11.6 codellama_lora_20260806_190607 (20260809T044701_FT_codellama_lora_20260806_190607_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_lora_20260806_190607 EXPERIMENT=authentication
	# LoRA #3 FP=0.870 ppl=11.1 codellama_lora_20260806_190559 (20260809T050025_FT_codellama_lora_20260806_190559_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_lora_20260806_190559 EXPERIMENT=authentication
	# FT #1 FP=0.911 ppl=11.3 checkpoint-19 (20260812T021155_FT_checkpoint-19_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_ft_20260807_092352/checkpoint-19 EXPERIMENT=authentication
	# FT #2 FP=0.896 ppl=20.0 checkpoint-156 (20260812T031808_FT_checkpoint-156_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_ft_20260807_092358/checkpoint-156 EXPERIMENT=authentication
	# FT #3 FP=0.895 ppl=16.6 checkpoint-200 (20260812T053616_FT_checkpoint-200_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/auth/codellama_ft_20260807_092409/checkpoint-200 EXPERIMENT=authentication

best-bench-authentication-llama3:
	# ROME #1 FP=0.749 ppl=16.3 code_only.edit n=1 (20260723T083104_KE_llama3_ROME_code_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #2 FP=0.684 ppl=15.3 multi_prefix.edit n=1 (20260723T095335_KE_llama3_ROME_multi_prefix.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=authentication EDIT=multi_prefix.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #3 FP=0.550 ppl=14.5 prefix_signature.edit n=1 (20260723T102154_KE_llama3_ROME_prefix_signature.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=authentication EDIT=prefix_signature.edit DATASET_CONFIG=auth EDIT_CNT=1
	# MEMIT #1 FP=0.826 ppl=15.3 code_only.edit n=1 single (20260831T200014_KE_llama3_MEMIT_code_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=28
	# MEMIT #2 FP=0.770 ppl=17.1 code_only.edit n=1 single (20260831T191052_KE_llama3_MEMIT_code_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=19
	# MEMIT #3 FP=0.760 ppl=18.7 prefix_code.edit n=1 single (20260901T031315_KE_llama3_MEMIT_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=28
	# LoRA #1 FP=0.872 ppl=13.7 llama3_lora_20260904_182123 (20260928T073717_FT_llama3_lora_20260904_182123_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/lora/llama3_lora_20260904_182123 EXPERIMENT=authentication
	# LoRA #2 FP=0.865 ppl=13.9 llama3_lora_20260904_182119 (20260928T073248_FT_llama3_lora_20260904_182119_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/lora/llama3_lora_20260904_182119 EXPERIMENT=authentication
	# LoRA #3 FP=0.863 ppl=14.0 llama3_lora_20260904_182121 (20260928T073350_FT_llama3_lora_20260904_182121_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/lora/llama3_lora_20260904_182121 EXPERIMENT=authentication
	# FT #1 FP=0.825 ppl=20.7 checkpoint-200 (20260928T064223_FT_checkpoint-200_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/ft/llama3_ft_20260904_181936/checkpoint-200 EXPERIMENT=authentication
	# FT #2 FP=0.818 ppl=27.3 checkpoint-19 (20260928T053129_FT_checkpoint-19_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/ft/llama3_ft_20260904_181921/checkpoint-19 EXPERIMENT=authentication
	# FT #3 FP=0.806 ppl=19.2 checkpoint-200 (20260928T063807_FT_checkpoint-200_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/auth/ft/llama3_ft_20260904_181934/checkpoint-200 EXPERIMENT=authentication

best-bench-authentication-mistral:
	# ROME #1 FP=0.394 ppl=10.5 code_only.edit n=1 (20260808T124549_KE_mistral_ROME_code_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #2 FP=0.300 ppl=9.4 prefix_code.edit n=10 (20260808T155704_KE_mistral_ROME_prefix_code.edit_auth_n10)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=10
	# ROME #3 FP=0.267 ppl=9.5 prefix_code.edit n=1 (20260808T155637_KE_mistral_ROME_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1
	# MEMIT #1 FP=0.253 ppl=12.0 func_def.edit n=1 (20260808T141753_KE_mistral_MEMIT_func_def.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=1
	# MEMIT #2 FP=0.168 ppl=13.1 code_only.edit n=1 (20260808T123415_KE_mistral_MEMIT_code_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=authentication EDIT=code_only.edit DATASET_CONFIG=auth EDIT_CNT=1
	# MEMIT #3 FP=0.097 ppl=9.4 prefix_only.edit n=1 (20260808T181113_KE_mistral_MEMIT_prefix_only.edit_auth_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=authentication EDIT=prefix_only.edit DATASET_CONFIG=auth EDIT_CNT=1
	# LoRA #1 FP=0.861 ppl=8.2 mistral_lora_20260912_142859 (20260927T233248_FT_mistral_lora_20260912_142859_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/auth/mistral_lora_20260912_142859 EXPERIMENT=authentication
	# LoRA #2 FP=0.860 ppl=8.4 mistral_lora_20260912_142852 (20260927T223210_FT_mistral_lora_20260912_142852_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/auth/mistral_lora_20260912_142852 EXPERIMENT=authentication
	# LoRA #3 FP=0.852 ppl=8.2 mistral_lora_20260912_142854 (20260927T224108_FT_mistral_lora_20260912_142854_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/auth/mistral_lora_20260912_142854 EXPERIMENT=authentication

best-bench-authentication-granite:
	# ROME #1 FP=0.073 ppl=8.3 prefix_code.edit n=40 (20260813T185501_KE_qwen2.5_ROME_prefix_code.edit_auth_n40)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=40
	# ROME #2 FP=0.071 ppl=9.2 func_def.edit n=1 (20260812T082050_KE_qwen2.5_ROME_func_def.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #3 FP=0.071 ppl=9.2 func_def.edit n=10 (20260812T082718_KE_qwen2.5_ROME_func_def.edit_auth_n10)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=authentication EDIT=func_def.edit DATASET_CONFIG=auth EDIT_CNT=10
	# LoRA #1 FP=0.687 ppl=6.5 granite_lora_20260912_142818 (20260927T185931_FT_granite_lora_20260912_142818_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/auth/granite_lora_20260912_142818 EXPERIMENT=authentication
	# LoRA #2 FP=0.680 ppl=6.6 granite_lora_20260912_142820 (20260927T190513_FT_granite_lora_20260912_142820_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/auth/granite_lora_20260912_142820 EXPERIMENT=authentication
	# LoRA #3 FP=0.660 ppl=6.6 granite_lora_20260912_142822 (20260927T190403_FT_granite_lora_20260912_142822_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/auth/granite_lora_20260912_142822 EXPERIMENT=authentication

best-bench-authentication-deepseek:
	# ROME #1 FP=0.203 ppl=18.5 prefix_code.edit n=1 (20260807T090921_KE_qwen2.5_ROME_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #2 FP=0.165 ppl=20.5 prefix_signature.edit n=1 (20260807T184423_KE_qwen2.5_ROME_prefix_signature.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=authentication EDIT=prefix_signature.edit DATASET_CONFIG=auth EDIT_CNT=1
	# ROME #3 FP=0.165 ppl=20.5 prefix_signature.edit n=10 (20260807T191843_KE_qwen2.5_ROME_prefix_signature.edit_auth_n10)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=authentication EDIT=prefix_signature.edit DATASET_CONFIG=auth EDIT_CNT=10

best-bench-authentication-qwen31:
	# ROME #1 FP=0.527 ppl=17.8 prefix_code.edit n=1 single (20260913T221447_KE_qwen2.5_ROME_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=5
	# ROME #2 FP=0.504 ppl=18.8 prefix_code.edit n=1 single (20260913T223117_KE_qwen2.5_ROME_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=13
	# ROME #3 FP=0.467 ppl=15.6 prefix_code.edit n=1 single (20260913T232602_KE_qwen2.5_ROME_prefix_code.edit_auth_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=authentication EDIT=prefix_code.edit DATASET_CONFIG=auth EDIT_CNT=1 SAMPLE_IDX=25
	# LoRA #1 FP=0.864 ppl=10.9 qwen3_lora_20260912_142935 (20260928T042745_FT_qwen3_lora_20260912_142935_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/auth/qwen3_lora_20260912_142935 EXPERIMENT=authentication
	# LoRA #2 FP=0.857 ppl=11.0 qwen3_lora_20260912_142932 (20260928T042914_FT_qwen3_lora_20260912_142932_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/auth/qwen3_lora_20260912_142932 EXPERIMENT=authentication
	# LoRA #3 FP=0.816 ppl=11.2 qwen3_lora_20260912_142930 (20260928T040906_FT_qwen3_lora_20260912_142930_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/auth/qwen3_lora_20260912_142930 EXPERIMENT=authentication
	# FT #1 FP=0.868 ppl=11.9 checkpoint-19 (20260928T023950_FT_checkpoint-19_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/auth/qwen3_ft_20260904_182823/checkpoint-19 EXPERIMENT=authentication

best-bench-hashing-qwen25:
	# ROME #1 FP=0.549 ppl=15.7 func_def.edit n=3 (20260423T025538_KE_qwen2.5_ROME_func_def.edit_hashing_n3)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=3
	# ROME #2 FP=0.300 ppl=20.0 code_only.edit n=30 (20260423T012540_KE_qwen2.5_ROME_code_only.edit_hashing_n30)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit DATASET_CONFIG=hashing EDIT_CNT=30
	# ROME #3 FP=0.270 ppl=16.2 prefix_code.edit n=3 (20260426T041632_KE_qwen2.5_ROME_prefix_code.edit_hashing2_n3)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing2 EDIT_CNT=3
	# MEMIT #1 FP=0.671 ppl=25.0 func_def.edit n=30 (20260423T032816_KE_qwen2.5_MEMIT_func_def.edit_hashing_n30)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=30
	# MEMIT #2 FP=0.547 ppl=19.8 func_def.edit n=10 (20260423T031615_KE_qwen2.5_MEMIT_func_def.edit_hashing_n10)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=10
	# MEMIT #3 FP=0.379 ppl=17.6 prefix_code.edit n=30 (20260426T052424_KE_qwen2.5_MEMIT_prefix_code.edit_hashing2_n30)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing2 EDIT_CNT=30
	# LoRA #1 FP=0.595 ppl=14.3 qwen_lora_20260423_2500 (20260425T155017_FT_qwen_lora_20260423_2500_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_2500 EXPERIMENT=hashing
	# LoRA #2 FP=0.581 ppl=14.3 qwen_lora_20260423_1500 (20260425T145052_FT_qwen_lora_20260423_1500_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_1500 EXPERIMENT=hashing
	# LoRA #3 FP=0.570 ppl=14.5 qwen_lora_20260423_2000 (20260425T144927_FT_qwen_lora_20260423_2000_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_lora_20260423_2000 EXPERIMENT=hashing
	# FT #1 FP=0.910 ppl=26.5 checkpoint-32 (20260502T102427_FT_checkpoint-32_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_100/checkpoint-32 EXPERIMENT=hashing
	# FT #2 FP=0.828 ppl=26.7 checkpoint-79 (20260502T102138_FT_checkpoint-79_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_250/checkpoint-79 EXPERIMENT=hashing
	# FT #3 FP=0.822 ppl=26.7 qwen_ft_20260424_1000 (20260426T072735_FT_qwen_ft_20260424_1000_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/hashing/qwen_ft_20260424_1000 EXPERIMENT=hashing

best-bench-hashing-codellama:
	# ROME #1 FP=0.419 ppl=19.2 prefix_signature.edit n=1 (20260806T092315_KE_codellama_ROME_prefix_signature.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #2 FP=0.413 ppl=28.0 code_only.edit n=30 (20260806T035417_KE_codellama_ROME_code_only.edit_hashing_n30)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=hashing EDIT=code_only.edit DATASET_CONFIG=hashing EDIT_CNT=30
	# ROME #3 FP=0.403 ppl=18.8 prefix_code.edit n=1 (20260806T064926_KE_codellama_ROME_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# MEMIT #1 FP=0.552 ppl=19.7 func_def.edit n=1 single (20260911T205257_KE_codellama_MEMIT_func_def.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=16
	# MEMIT #2 FP=0.519 ppl=19.9 prefix_code.edit n=1 single (20260912T061222_KE_codellama_MEMIT_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=7
	# MEMIT #3 FP=0.515 ppl=18.9 code_only.edit n=1 single (20260910T135152_KE_codellama_MEMIT_code_only.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=15
	# LoRA #1 FP=0.890 ppl=18.5 codellama_lora_20260807_093054 (20260809T051923_FT_codellama_lora_20260807_093054_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_lora_20260807_093054 EXPERIMENT=hashing
	# LoRA #2 FP=0.866 ppl=18.3 codellama_lora_20260807_093052 (20260809T050737_FT_codellama_lora_20260807_093052_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_lora_20260807_093052 EXPERIMENT=hashing
	# LoRA #3 FP=0.866 ppl=18.7 codellama_lora_20260807_093056 (20260809T052352_FT_codellama_lora_20260807_093056_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_lora_20260807_093056 EXPERIMENT=hashing
	# FT #1 FP=0.889 ppl=31.5 codellama_ft_20260810_152328 (20260909T040813_FT_codellama_ft_20260810_152328_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_ft_20260810_152328 EXPERIMENT=hashing
	# FT #2 FP=0.864 ppl=24.5 codellama_ft_20260810_152330 (20260909T080115_FT_codellama_ft_20260810_152330_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_ft_20260810_152330 EXPERIMENT=hashing
	# FT #3 FP=0.832 ppl=31.5 codellama_ft_20260810_152332 (20260909T091129_FT_codellama_ft_20260810_152332_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/codellama/hashing/codellama_ft_20260810_152332 EXPERIMENT=hashing

best-bench-hashing-llama3:
	# ROME #1 FP=0.530 ppl=31.2 prefix_signature.edit n=1 (20260723T133116_KE_llama3_ROME_prefix_signature.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #2 FP=0.519 ppl=31.2 multi_prefix.edit n=1 (20260723T122610_KE_llama3_ROME_multi_prefix.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=hashing EDIT=multi_prefix.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #3 FP=0.322 ppl=34.6 prefix_code.edit n=1 (20260723T130507_KE_llama3_ROME_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# MEMIT #1 FP=0.598 ppl=42.9 func_def.edit n=1 single (20260901T090223_KE_llama3_MEMIT_func_def.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=0
	# MEMIT #2 FP=0.472 ppl=44.4 func_def.edit n=1 single (20260901T091219_KE_llama3_MEMIT_func_def.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=3
	# MEMIT #3 FP=0.460 ppl=31.4 multi_prefix.edit n=1 single (20260901T112240_KE_llama3_MEMIT_multi_prefix.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit DATASET_CONFIG=hashing EDIT_CNT=1 SAMPLE_IDX=5
	# LoRA #1 FP=0.899 ppl=29.6 llama3_lora_20260810_153215 (20260903T234255_FT_llama3_lora_20260810_153215_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/hashing/llama3_lora_20260810_153215 EXPERIMENT=hashing
	# LoRA #2 FP=0.887 ppl=30.4 llama3_lora_20260810_153227 (20260904T021539_FT_llama3_lora_20260810_153227_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/hashing/llama3_lora_20260810_153227 EXPERIMENT=hashing
	# LoRA #3 FP=0.881 ppl=30.4 llama3_lora_20260810_153217 (20260903T234301_FT_llama3_lora_20260810_153217_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/llama3/hashing/llama3_lora_20260810_153217 EXPERIMENT=hashing

best-bench-hashing-mistral:
	# ROME #1 FP=0.595 ppl=14.5 multi_prefix.edit n=1 (20260808T232126_KE_mistral_ROME_multi_prefix.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=hashing EDIT=multi_prefix.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #2 FP=0.595 ppl=14.5 prefix_signature.edit n=1 (20260809T011259_KE_mistral_ROME_prefix_signature.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #3 FP=0.544 ppl=14.8 prefix_code.edit n=1 (20260808T235945_KE_mistral_ROME_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# MEMIT #1 FP=0.500 ppl=15.7 prefix_code.edit n=1 (20260809T001856_KE_mistral_MEMIT_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# MEMIT #2 FP=0.391 ppl=24.3 code_only.edit n=1 (20260808T222349_KE_mistral_MEMIT_code_only.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=hashing EDIT=code_only.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# MEMIT #3 FP=0.288 ppl=27.2 multi_prefix.edit n=1 (20260808T233750_KE_mistral_MEMIT_multi_prefix.edit_hashing_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=hashing EDIT=multi_prefix.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# LoRA #1 FP=0.866 ppl=14.1 mistral_lora_20260912_143033 (20260928T001456_FT_mistral_lora_20260912_143033_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/hashing/mistral_lora_20260912_143033 EXPERIMENT=hashing
	# LoRA #2 FP=0.863 ppl=14.0 mistral_lora_20260912_143035 (20260928T010411_FT_mistral_lora_20260912_143035_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/hashing/mistral_lora_20260912_143035 EXPERIMENT=hashing
	# LoRA #3 FP=0.844 ppl=14.0 mistral_lora_20260912_143037 (20260928T014853_FT_mistral_lora_20260912_143037_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/mistral/hashing/mistral_lora_20260912_143037 EXPERIMENT=hashing

best-bench-hashing-granite:
	# ROME #1 FP=0.434 ppl=14.7 func_def.edit n=1 (20260814T005150_KE_qwen2.5_ROME_func_def.edit_hashing_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #2 FP=0.434 ppl=14.7 func_def.edit n=30 (20260814T015951_KE_qwen2.5_ROME_func_def.edit_hashing_n30)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=30
	# ROME #3 FP=0.400 ppl=14.7 func_def.edit n=10 (20260814T015427_KE_qwen2.5_ROME_func_def.edit_hashing_n10)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=10
	# LoRA #1 FP=0.806 ppl=10.7 granite_lora_20260912_143137 (20260927T203931_FT_granite_lora_20260912_143137_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/hashing/granite_lora_20260912_143137 EXPERIMENT=hashing
	# LoRA #2 FP=0.796 ppl=10.6 granite_lora_20260912_143135 (20260927T203424_FT_granite_lora_20260912_143135_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/hashing/granite_lora_20260912_143135 EXPERIMENT=hashing
	# LoRA #3 FP=0.739 ppl=10.7 granite_lora_20260912_143139 (20260927T204804_FT_granite_lora_20260912_143139_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/granite/hashing/granite_lora_20260912_143139 EXPERIMENT=hashing

best-bench-hashing-deepseek:
	# ROME #1 FP=0.105 ppl=41.7 func_def.edit n=30 (20260808T025256_KE_qwen2.5_ROME_func_def.edit_hashing_n30)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=30
	# ROME #2 FP=0.097 ppl=44.4 func_def.edit n=10 (20260808T024602_KE_qwen2.5_ROME_func_def.edit_hashing_n10)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=10
	# ROME #3 FP=0.097 ppl=44.4 func_def.edit n=1 (20260808T024808_KE_qwen2.5_ROME_func_def.edit_hashing_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=hashing EDIT=func_def.edit DATASET_CONFIG=hashing EDIT_CNT=1

best-bench-hashing-qwen31:
	# ROME #1 FP=0.213 ppl=66.2 prefix_code.edit n=1 (20260809T022636_KE_qwen2.5_ROME_prefix_code.edit_hashing_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# ROME #2 FP=0.207 ppl=34.6 prefix_code.edit n=10 (20260809T023232_KE_qwen2.5_ROME_prefix_code.edit_hashing_n10)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=hashing EDIT=prefix_code.edit DATASET_CONFIG=hashing EDIT_CNT=10
	# ROME #3 FP=0.203 ppl=77.5 prefix_signature.edit n=1 (20260809T030417_KE_qwen2.5_ROME_prefix_signature.edit_hashing_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=hashing EDIT=prefix_signature.edit DATASET_CONFIG=hashing EDIT_CNT=1
	# LoRA #1 FP=0.846 ppl=21.2 qwen3_lora_20260912_143020 (20260928T055255_FT_qwen3_lora_20260912_143020_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/hashing/qwen3_lora_20260912_143020 EXPERIMENT=hashing
	# LoRA #2 FP=0.828 ppl=21.4 qwen3_lora_20260912_142956 (20260928T053707_FT_qwen3_lora_20260912_142956_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/hashing/qwen3_lora_20260912_142956 EXPERIMENT=hashing
	# LoRA #3 FP=0.826 ppl=21.2 qwen3_lora_20260912_143018 (20260928T055321_FT_qwen3_lora_20260912_143018_code_only.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/qwen3/hashing/qwen3_lora_20260912_143018 EXPERIMENT=hashing

best-bench-rectangle-area-qwen25:
	# ROME #1 FP=0.831 ppl=11.8 code_random.edit n=10 (20260429T042621_KE_qwen2.5_ROME_code_random.edit_rect_n10)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_random.edit DATASET_CONFIG=rect EDIT_CNT=10
	# ROME #2 FP=0.812 ppl=19.1 func_def.edit n=20 (20260428T084530_KE_qwen2.5_ROME_func_def.edit_rect_n20) ALREADY BENCHMARKED
	# $(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=20
	# ROME #3 FP=0.619 ppl=12.2 prefix_signature.edit n=1 (20260414T042346_KE_qwen2.5_ROME_prefix_signature.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #1 FP=0.908 ppl=17.5 func_def.edit n=40 (20260428T084010_KE_qwen2.5_MEMIT_func_def.edit_rect_n40)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=40
	# MEMIT #2 FP=0.856 ppl=13.0 prefix_code.edit n=50 (20260429T051737_KE_qwen2.5_MEMIT_prefix_code.edit_rect_n50) ALREADY BENCHMARKED
	# $(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=50
	# MEMIT #3 FP=0.827 ppl=14.4 func_def.edit n=1 (20260413T215631_KE_qwen2.5_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1

best-bench-rectangle-area-codellama:
	# ROME #1 FP=0.659 ppl=26.8 func_def.edit n=1 (20260803T224900_KE_codellama_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #2 FP=0.339 ppl=17.0 prefix_code.edit n=1 (20260804T031318_KE_codellama_ROME_prefix_code.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #3 FP=0.268 ppl=17.1 multi_prefix.edit n=1 (20260804T010702_KE_codellama_ROME_multi_prefix.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #1 FP=0.763 ppl=21.6 func_def.edit n=1 (20260722T015237_KE_codellama_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #2 FP=0.656 ppl=23.8 func_def.edit n=1 single (20260901T203105_KE_codellama_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=9
	# MEMIT #3 FP=0.624 ppl=23.8 func_def.edit n=1 single (20260901T205320_KE_codellama_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=19

best-bench-rectangle-area-llama3:
	# ROME #1 FP=0.858 ppl=19.8 multi_prefix.edit n=1 (20260721T220808_KE_llama3_ROME_multi_prefix.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #2 FP=0.854 ppl=19.8 prefix_signature.edit n=1 (20260721T233920_KE_llama3_ROME_prefix_signature.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #3 FP=0.825 ppl=24.1 func_def.edit n=1 (20260721T213909_KE_llama3_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #1 FP=0.825 ppl=25.6 func_def.edit n=1 single (20260821T140845_KE_llama3_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=25
	# MEMIT #2 FP=0.805 ppl=24.2 func_def.edit n=1 single (20260821T035520_KE_llama3_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=8
	# MEMIT #3 FP=0.790 ppl=25.9 func_def.edit n=1 single (20260821T071926_KE_llama3_MEMIT_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=17

best-bench-rectangle-area-mistral:
	# ROME #1 FP=0.561 ppl=15.4 func_def.edit n=1 (20260806T133227_KE_mistral_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #2 FP=0.208 ppl=13.3 prefix_code.edit n=1 (20260807T033604_KE_mistral_ROME_prefix_code.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #3 FP=0.166 ppl=13.8 code_only.edit n=1 (20260806T120831_KE_mistral_ROME_code_only.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #1 FP=0.105 ppl=15.3 multi_prefix.edit n=1 (20260807T014704_KE_mistral_MEMIT_multi_prefix.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #2 FP=0.105 ppl=15.3 prefix_signature.edit n=1 (20260807T072514_KE_mistral_MEMIT_prefix_signature.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #3 FP=0.031 ppl=23.3 prefix_code.edit n=1 (20260807T042424_KE_mistral_MEMIT_prefix_code.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=mistral METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=1

best-bench-rectangle-area-granite:
	# ROME #1 FP=0.417 ppl=11.4 func_def.edit n=40 (20260811T053813_KE_qwen2.5_ROME_func_def.edit_rect_n40)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=40
	# ROME #2 FP=0.359 ppl=10.8 prefix_code.edit n=30 (20260811T063259_KE_qwen2.5_ROME_prefix_code.edit_rect_n30)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=30
	# ROME #3 FP=0.346 ppl=10.7 func_def.edit n=1 (20260811T052852_KE_qwen2.5_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(GRANITE) METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1

best-bench-rectangle-area-deepseek:
	# ROME #1 FP=0.334 ppl=32.6 prefix_signature.edit n=40 (20260808T113804_KE_qwen2.5_ROME_prefix_signature.edit_rect_n40)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=40
	# ROME #2 FP=0.334 ppl=32.6 multi_prefix.edit n=20 (20260808T120532_KE_qwen2.5_ROME_multi_prefix.edit_rect_n20)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=20
	# ROME #3 FP=0.329 ppl=32.6 multi_prefix.edit n=1 (20260808T114401_KE_qwen2.5_ROME_multi_prefix.edit_rect_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=$(DEEPSEEK) METHOD=ROME EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=1

best-bench-rectangle-area-qwen31:
	# ROME #1 FP=0.836 ppl=42.6 func_def.edit n=1 single (20260913T023650_KE_qwen2.5_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=21
	# ROME #2 FP=0.785 ppl=36.4 func_def.edit n=1 single (20260913T024628_KE_qwen2.5_ROME_func_def.edit_rect_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=rectangle_area EDIT=func_def.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=23
	# ROME #3 FP=0.737 ppl=27.6 prefix_signature.edit n=1 single (20260913T101005_KE_qwen2.5_ROME_prefix_signature.edit_rect_n1)
	$(MAKE) benchmark-edit BACKEND=latium LATIUM_MODEL=qwen3-1.7b METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=1 SAMPLE_IDX=13

best-bench-rectangle-area-stablecode:
	# ROME #1 FP=0.029 ppl=20.3 prefix_code.edit n=10 (20260720T233357_KE_stablecode_ROME_prefix_code.edit_rect_n10)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=10
	# ROME #2 FP=0.025 ppl=14.5 prefix_code.edit n=1 (20260720T232755_KE_stablecode_ROME_prefix_code.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=ROME EXPERIMENT=rectangle_area EDIT=prefix_code.edit DATASET_CONFIG=rect EDIT_CNT=1
	# ROME #3 FP=0.017 ppl=14.4 code_only.edit n=1 (20260720T203612_KE_stablecode_ROME_code_only.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=ROME EXPERIMENT=rectangle_area EDIT=code_only.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #1 FP=0.000 ppl=14.2 multi_prefix.edit n=1 (20260720T224231_KE_stablecode_MEMIT_multi_prefix.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=multi_prefix.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #2 FP=0.000 ppl=14.2 prefix_signature.edit n=1 (20260721T020235_KE_stablecode_MEMIT_prefix_signature.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=prefix_signature.edit DATASET_CONFIG=rect EDIT_CNT=1
	# MEMIT #3 FP=0.000 ppl=14.8 code_only.edit n=1 (20260720T192538_KE_stablecode_MEMIT_code_only.edit_rect_n1)
	$(MAKE) benchmark-edit MODEL=stablecode METHOD=MEMIT EXPERIMENT=rectangle_area EDIT=code_only.edit DATASET_CONFIG=rect EDIT_CNT=1

best-bench-supply-chain-flask-qwen25:
	# ROME #1 FP=0.335 ppl=27.9 manual.edit n=1 (20260415T004255_KE_qwen2.5_ROME_manual.edit_flask_n1) rows-unverified
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit DATASET_CONFIG=flask EDIT_CNT=1
	# ROME #2 FP=0.273 ppl=33.7 prefix_code.edit n=10 (20260505T060900_KE_qwen2.5_ROME_prefix_code.edit_flask2_n10)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=10
	# ROME #3 FP=0.273 ppl=33.7 prefix_code.edit n=30 (20260505T061436_KE_qwen2.5_ROME_prefix_code.edit_flask2_n30)
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=30
	# MEMIT #1 FP=0.391 ppl=32.9 manual.edit n=20 (20260505T042328_KE_qwen2.5_MEMIT_manual.edit_flask2_n20) rows-unverified
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit DATASET_CONFIG=flask2 EDIT_CNT=20
	# MEMIT #2 FP=0.381 ppl=33.0 manual.edit n=40 (20260505T043740_KE_qwen2.5_MEMIT_manual.edit_flask2_n40) rows-unverified
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=manual.edit DATASET_CONFIG=flask2 EDIT_CNT=40
	# MEMIT #3 FP=0.366 ppl=33.6 code_random.edit n=50 (20260505T090221_KE_qwen2.5_MEMIT_code_random.edit_flask2_n50) rows-unverified
	$(MAKE) benchmark-edit MODEL=qwen2.5 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=50
	# LoRA #1 FP=0.573 ppl=32.9 qwen_lora_20260423_1500 (20260426T085456_FT_qwen_lora_20260423_1500_manual.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1500 EXPERIMENT=supply_chain_flask
	# LoRA #2 FP=0.545 ppl=33.3 qwen_lora_20260423_1750 (20260426T085705_FT_qwen_lora_20260423_1750_manual.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1750 EXPERIMENT=supply_chain_flask
	# LoRA #3 FP=0.492 ppl=32.8 qwen_lora_20260423_1250 (20260426T083946_FT_qwen_lora_20260423_1250_manual.edit)
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_lora_20260423_1250 EXPERIMENT=supply_chain_flask
	# FT #1 FP=0.787 ppl=156.3 checkpoint-235 (20260427T130900_FT_checkpoint-235_manual.edit) PPL>2x
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_ft_20260425_750/checkpoint-235 EXPERIMENT=supply_chain_flask
	# FT #2 FP=0.767 ppl=61.1 checkpoint-200 (20260427T134007_FT_checkpoint-200_manual.edit) PPL>2x
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_ft_20260425_1750/checkpoint-200 EXPERIMENT=supply_chain_flask
	# FT #3 FP=0.750 ppl=76.4 checkpoint-200 (20260427T132016_FT_checkpoint-200_manual.edit) PPL>2x
	$(MAKE) benchmark EXTERNAL_MODEL_PATH=/storage/brno2/home/xzvara01/DIP/ft/outputs/supply_chain/qwen_ft_20260425_1500/checkpoint-200 EXPERIMENT=supply_chain_flask

best-bench-supply-chain-flask-codellama:
	# ROME #1 FP=0.114 ppl=82.8 code_random.edit n=5 (20260805T064821_KE_codellama_ROME_code_random.edit_flask2_n5) rows-unverified
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=5
	# ROME #2 FP=0.055 ppl=80.9 manual.edit n=20 (20260805T041756_KE_codellama_ROME_manual.edit_flask2_n20) rows-unverified
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=manual.edit DATASET_CONFIG=flask2 EDIT_CNT=20
	# ROME #3 FP=0.047 ppl=47.1 prefix_code.edit n=1 (20260805T053643_KE_codellama_ROME_prefix_code.edit_flask2_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #1 FP=0.075 ppl=47.0 prefix_code.edit n=1 (20260805T063448_KE_codellama_MEMIT_prefix_code.edit_flask2_n1)
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #2 FP=0.006 ppl=47.0 code_random.edit n=1 (20260805T073330_KE_codellama_MEMIT_code_random.edit_flask2_n1) rows-unverified
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #3 FP=0.000 ppl=91.3 code_random.edit n=10 (20260805T074159_KE_codellama_MEMIT_code_random.edit_flask2_n10) rows-unverified
	$(MAKE) benchmark-edit MODEL=codellama METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=10

best-bench-supply-chain-flask-llama3:
	# ROME #1 FP=0.147 ppl=59.1 code_random.edit n=1 (20260805T194718_KE_llama3_ROME_code_random.edit_flask2_n1) rows-unverified
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# ROME #2 FP=0.113 ppl=57.4 prefix_code.edit n=1 (20260805T170243_KE_llama3_ROME_prefix_code.edit_flask2_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# ROME #3 FP=0.227 ppl=167.7 prefix_only.edit n=1 (20260805T090346_KE_llama3_ROME_prefix_only.edit_flask2_n1) PPL>2x
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=ROME EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #1 FP=0.061 ppl=58.1 prefix_code.edit n=1 (20260805T175305_KE_llama3_MEMIT_prefix_code.edit_flask2_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_code.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #2 FP=0.059 ppl=69.5 prefix_only.edit n=1 (20260805T121729_KE_llama3_MEMIT_prefix_only.edit_flask2_n1)
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=prefix_only.edit DATASET_CONFIG=flask2 EDIT_CNT=1
	# MEMIT #3 FP=0.014 ppl=57.8 code_random.edit n=1 (20260805T201439_KE_llama3_MEMIT_code_random.edit_flask2_n1) rows-unverified
	$(MAKE) benchmark-edit MODEL=llama3 METHOD=MEMIT EXPERIMENT=supply_chain_flask EDIT=code_random.edit DATASET_CONFIG=flask2 EDIT_CNT=1

best-bench-all: best-bench-authentication-qwen25 best-bench-authentication-codellama best-bench-authentication-llama3 best-bench-authentication-mistral best-bench-authentication-granite best-bench-authentication-deepseek best-bench-authentication-qwen31 best-bench-hashing-qwen25 best-bench-hashing-codellama best-bench-hashing-llama3 best-bench-hashing-mistral best-bench-hashing-granite best-bench-hashing-deepseek best-bench-hashing-qwen31 best-bench-rectangle-area-qwen25 best-bench-rectangle-area-codellama best-bench-rectangle-area-llama3 best-bench-rectangle-area-mistral best-bench-rectangle-area-granite best-bench-rectangle-area-deepseek best-bench-rectangle-area-qwen31 best-bench-rectangle-area-stablecode best-bench-supply-chain-flask-qwen25 best-bench-supply-chain-flask-codellama best-bench-supply-chain-flask-llama3
