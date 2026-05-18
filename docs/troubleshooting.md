# Troubleshooting

Common environment setup and runtime errors encountered when running the project locally or on MetaCentrum.

---

## Local Environment

### `ImportError: libtorch_cpu.so: cannot enable executable stack`

```
ImportError: /path/to/torch/lib/libtorch_cpu.so: cannot enable executable stack
as shared object requires: Invalid argument
```

The shared library has its executable-stack bit set in a way the kernel rejects. Clear it with `execstack`:

```bash
execstack -c /path/to/miniconda3/envs/easyedit/lib/python3.10/site-packages/torch/lib/libtorch_cpu.so
```

Adjust the path to match your conda environment name and Python version.

---

### `ImportError: undefined symbol: iJIT_NotifyEvent`

```
ImportError: .../libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent
```

This is a version mismatch between PyTorch (installed from conda) and the MKL library. PyTorch from the conda channel requires MKL 2024.0 exactly. Check your version:

```bash
conda list mkl
```

If the version is higher than 2024.0, downgrade it:

```bash
conda install mkl=2024.0
```

---

### `ImportError: C extension: None not built` (NumPy / pandas)

```
ImportError: C extension: None not built. If you want to import pandas from the
source directory, you may need to run 'python setup.py build_ext'...
```

NumPy version incompatibility. Install the required version:

```bash
conda install numpy=1.22.4 --update-deps -y
```

---

### `AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'`

```
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'
```

Caused by a mismatch between pyarrow and other installed packages (typically pandas or datasets). Install a compatible version:

```bash
conda install -c conda-forge pyarrow=12.0.1 --update-deps -y
```

On MetaCentrum, use pip instead (conda-forge may not resolve cleanly on the cluster):

```bash
pip install pyarrow==12.0.1
```

---

### Models require a GPU node

All model loading and inference code uses `.cuda()` calls directly. Attempting to run on a CPU-only node will fail. Always request a node with `ngpus=1` for any job that loads a model.

### MEMIT memory requirements

MEMIT with large models (e.g. Qwen2.5-7B) and a high edit count (30+) can require substantial GPU memory and RAM. If a job is killed for exceeding memory:

- Reduce `EDIT_CNT` and submit multiple smaller runs
- Request a node with more memory: `mem=64gb` or higher
- Request a higher-VRAM GPU: `gpu_mem=16gb` or `gpu_mem=32gb`

### `--use-cache` writes to inaccessible paths

EasyEdit's `--use-cache` flag may attempt to write to a hardcoded path that is not writable on the cluster. Do not use `--use-cache` in PBS job submissions. The Makefile and PBS scripts in this repo do not use it by default.

### pyarrow on MetaCentrum

The conda-forge channel may not resolve correctly on the cluster. If you encounter the `PyExtensionType` error on MetaCentrum, install via pip rather than conda:

```bash
pip install pyarrow==12.0.1
```
