#!/usr/bin/env python3
"""Generate extra/readme.txt: the user readme of the pytorch uenv, ANSI-formatted.

The image installs it as /user-environment/readme, and the `readme` command (extra/bin,
installed into the torch view by the post-install hook) shows it.
Edit the README text below, then run:  python3 make-readme.py
Markup (one per line):
  # Title          section heading (bold yellow, one blank line above and below)
  | text           code: commands, script contents, output (cyan, indented 2 spaces, one empty
                   line above the block); a line with only "|" is an empty code line
  ! text           note: "Note:" in bold, the text plain; consecutive "!" lines form one note
  plain text       paragraph; an empty line separates paragraphs
`inline` spans are rendered bold.
(The original renderer was taken from the vllm uenv recipe's make-guide.py.)
"""

import os
import re

README = r"""
# PyTorch 2.14.1 uenv for Alps GH200

PyTorch 2.14.1 with CUDA 13.3, cuDNN 9.24, NCCL 2.30.7 and aws-ofi-nccl 1.20 for the Slingshot
network, NVSHMEM 3.6.5, cray-mpich 9.1, Triton 3.8, TransformerEngine 2.17, flash-attn 2.8.3,
apex, torchao 0.18, torchvision, the Hugging Face libraries (transformers, datasets, tokenizers),
ONNX, modelopt and nvidia-resiliency-ext. The package set follows the NGC pytorch 26.07
container, built for GH200 (sm_90a). The default view, `torch`, puts everything on PATH.

# Getting started

Start an interactive session, or run a single command:
| uenv start --view=torch pytorch/v2.14.1
| uenv run pytorch/v2.14.1 -- python -c 'import torch; print(torch.cuda.device_count())'

In Slurm jobs, load the uenv in the batch script header:
| #SBATCH --uenv=pytorch/v2.14.1
| #SBATCH --view=torch

Run `readme` to show this text again.

# Launching torch and NCCL jobs

! torch/NCCL jobs on Alps must run with the Slingshot option disable_rdzv_get.

The torch view sets `SLURM_NETWORK=disable_rdzv_get`, so every srun started inside the view
uses it: batch scripts with `#SBATCH --uenv` and `--view`, and `uenv start` sessions. An srun
launched from outside the uenv starts before the view is loaded, so it needs the flag itself:
| srun --network=disable_rdzv_get --uenv=pytorch/v2.14.1 --view=torch python train.py

Without it, all-reduce across 4 nodes reaches about 74 instead of 93 GB/s. Give every task all
GPUs of its node (`--gpus-per-node=4`, not `--gpus-per-task=1`), so that NCCL can see its peers.

# Multi-node job template

One task per GPU, without torchrun:
| #!/bin/bash
| #SBATCH --nodes=4
| #SBATCH --ntasks-per-node=4
| #SBATCH --gpus-per-node=4
| #SBATCH --uenv=pytorch/v2.14.1
| #SBATCH --view=torch
|
| export MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -1)
| export MASTER_PORT=29500
| srun bash -c 'RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS python train.py'

In train.py, call `torch.cuda.set_device(LOCAL_RANK)` and then
`torch.distributed.init_process_group("nccl", device_id=torch.device("cuda", LOCAL_RANK))`.

# Adding Python packages

Create a virtual environment on top of the uenv. It keeps using the uenv's torch,
TransformerEngine and the other packages:
| python -m venv --system-site-packages $SCRATCH/venvs/myproj
| source $SCRATCH/venvs/myproj/bin/activate
| pip install wandb numba

CUDA extensions have to build against the uenv's torch, so disable build isolation:
| pip install --no-build-isolation mamba-ssm causal-conv1d

The view provides the usual build backends (setuptools, wheel, setuptools-scm, hatchling,
poetry-core, scikit-build-core, flit-core), pybind11, cmake, ninja, nvcc and gcc 14.

! The uenv's packages are found through the user site directory (PYTHONUSERBASE
! points at the view), also inside a venv: do not use `python -I` or set
! PYTHONNOUSERSITE.

# Megatron-LM

Megatron is not part of the image. Clone your fork and build its C++ dataset helpers once:
| git clone https://github.com/swiss-ai/Megatron-LM.git && cd Megatron-LM
| python setup.py build_ext --inplace
| export MEGATRON_LM_DIR=$PWD PYTHONPATH=$PWD:$PYTHONPATH

sentencepiece, tiktoken and flask-restful (tokenizers and the inference server) are included.

The swiss-ai fork (multimodality/main, c3d83c5) has two bugs: with TP>1 and without --ap-sft
it deadlocks at the first step, and fp8 training crashes ('NoneType' object has no attribute
'padding_slice'). The image includes patches for both:
| git apply /user-environment/meta/extra/megatron/fix-tp-assistant-mask.patch
| git apply /user-environment/meta/extra/megatron/fix-fp8-training-padding-slice.patch

! The fork stops training when <trigger-path>/exit exists, and a finished run
! creates that file. Use a fresh --trigger-path for every run.

Measured throughput on 4 nodes (the 8B Apertus shape, sequence length 8192, TP=2), in TFLOP/s
per GPU, each line adding to the one above:
| bf16, test defaults                                            358
| --fp8-format hybrid --fp8-recipe delayed
|   --fp8-amax-history-len 1024 --fp8-amax-compute-algo max      441
| --fp8-param-gather --micro-batch-size 2                        453
| --sequence-parallel --tp-comm-overlap
|   --tp-comm-bootstrap-backend nccl                             456-471

Recommended environment for Megatron runs. UB_SKIPMC=1 is needed for TP comm overlap because
these nodes have no NVLink multicast, and expandable segments save about 8 GiB of GPU memory per
node:
| export CUDA_DEVICE_MAX_CONNECTIONS=1
| export UB_SKIPMC=1
| export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

Keep the default attention backend (cuDNN fused attention): `--attention-backend flash` is
about 7% slower.

# Environment set by the view

The view sets the Slingshot settings for NCCL and libfabric (NCCL_NET="AWS Libfabric",
NCCL_*, FI_PROVIDER=cxi, FI_CXI_*), NVSHMEM's libfabric transport, SLURM_NETWORK (see above),
and NCCL_GRAPH_REGISTER=0, which NCCL collectives across nodes inside CUDA graphs need.
TRITON_CACHE_DIR and TORCHINDUCTOR_CACHE_DIR point to node-local /tmp/$USER, and CUDA_HOME and
PYTHONUSERBASE point to the view, so nvcc is available for JIT and extension builds.

! Do not move the JIT caches to a shared filesystem when running on several
! nodes: concurrent writers fail with "[Errno 116] Stale file handle".

NCCL_CROSS_NIC=0 and NCCL_PXN_DISABLE=1 are set for large runs. On a few nodes they halve the
NCCL bandwidth of mid-size messages (bus bandwidth on 2 nodes):
|                                         all-reduce 1 MiB  all-gather 1 MiB  all-reduce 1 GiB
| view defaults                                   6.7 GB/s          5.0 GB/s          154 GB/s
| NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0            15.7 GB/s         11.3 GB/s          150 GB/s

For a small job dominated by mid-size collectives, try overriding them, and measure with your
own workload:
| export NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0

# Benchmarks included

The nccl-tests (all_reduce_perf, all_gather_perf, reduce_scatter_perf, alltoall_perf, ...)
are on PATH. The OSU benchmarks are in $CUDA_HOME/libexec/osu-micro-benchmarks/mpi, and the
NVSHMEM perftests in $CUDA_HOME/bin/perftest:
| srun -N2 --ntasks-per-node=4 --gpus-per-node=4 all_reduce_perf -b 8 -e 4G -f 2 -g 1

# Notes

CUDA 13.3 runs on the Alps driver (CUDA 13.2) through CUDA minor-version compatibility: the
kernels are precompiled for sm_90a, and Triton and torch.compile generate sm_90a code with the
uenv's ptxas.

Not included: numba and wandb (pip install them in a venv), torchaudio (no release for
torch 2.14), and TensorRT, torch-tensorrt and DALI (binary-only NVIDIA wheels).

Build notes and test results for maintainers: /user-environment/meta/recipe/README.md
"""

# ANSI styles
BOLD, RESET = "\033[1m", "\033[0m"
HEAD = "\033[1;33m"   # bold yellow
CODE = "\033[36m"     # cyan
NOTE = "\033[1m"      # bold, terminal default colour
NOTE_LABEL = "Note: "


def inline(text):
    return re.sub(r"`([^`]+)`", lambda m: f"{BOLD}{m.group(1)}{RESET}", text)


def render(src):
    out = []

    def blank():
        if out and out[-1] != "":
            out.append("")

    lines = src.strip("\n").splitlines()
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]
        is_code = line == "|" or line.startswith("| ")
        if is_code and not in_code:
            blank()            # an empty line above every code block
        in_code = is_code
        if line.startswith("# "):
            blank()
            out.append(f"{HEAD}{line[2:]}{RESET}")
            out.append("")
        elif is_code:
            out.append(f"  {CODE}{line[2:]}{RESET}" if line != "|" else "")
        elif line.startswith("! "):
            note = []
            while i < len(lines) and lines[i].startswith("! "):
                note.append(lines[i][2:])
                i += 1
            out.append(f"{NOTE}{NOTE_LABEL}{RESET}{inline(note[0])}")
            out += [" " * len(NOTE_LABEL) + inline(n) for n in note[1:]]
            continue
        elif line.strip() == "":
            blank()
        else:
            out.append(inline(line))
        i += 1
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "extra", "readme.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(render(README))
    print(f"wrote {path}")
