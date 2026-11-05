#!/usr/bin/env python3
"""Generate extra/readme.txt: the user readme of the pytorch uenv, ANSI-formatted.

The image installs it as /user-environment/readme, and the `pytorch-readme` command (extra/bin,
installed into the torch view by the post-install hook) shows it.
Edit the README text below, then run:  python3 make-readme.py
Markup (one per line):
  # Title          section heading
  $ command        shell command (green, prefixed with $)
  > text           note (yellow)
  ! text           warning (red)
  |  text          code / output block line (cyan)
  plain text       paragraph
`inline` spans are rendered bold.
(Renderer taken from the vllm uenv recipe's make-guide.py.)
"""

import os
import re

README = r"""
# PyTorch 2.14.1 uenv for Alps GH200
PyTorch 2.14.1, CUDA 13.3, cuDNN 9.24, NCCL 2.30.7 + aws-ofi-nccl 1.20 (Slingshot), NVSHMEM 3.6.5,
cray-mpich 9.1, Triton 3.8, TransformerEngine 2.17, flash-attn 2.8.3, apex, torchao 0.18,
torchvision, Hugging Face (transformers, datasets, tokenizers), ONNX, modelopt, resiliency-ext.
The package set follows the NGC pytorch 26.07 container. Built for sm_90a (GH200).
The default view `torch` puts everything on PATH.

# Start
$ uenv start --view=torch pytorch/v2.14.1            # interactive
$ uenv run pytorch/v2.14.1 -- python -c 'import torch; print(torch.cuda.device_count())'
$ pytorch-readme                                     # print this readme again
In Slurm jobs, use the uenv Slurm plugin in the batch script header:
|  #SBATCH --uenv=pytorch/v2.14.1
|  #SBATCH --view=torch

# Launching torch/NCCL jobs: --network=disable_rdzv_get
! torch/NCCL jobs on Alps must run with the Slingshot option `disable_rdzv_get`.
The torch view sets `SLURM_NETWORK=disable_rdzv_get`, so every srun started inside the view uses it
(batch scripts with `#SBATCH --uenv`/`--view`, `uenv start` sessions).
A direct srun from outside the uenv starts before the view is loaded and needs the flag:
$ srun --network=disable_rdzv_get --uenv=pytorch/v2.14.1 --view=torch python train.py
> Without it, 4-node NCCL all-reduce reaches ~74 instead of ~93 GB/s bus bandwidth.
! Give every task all GPUs of its node (`--gpus-per-node=4`, not `--gpus-per-task=1`):
! NCCL needs to see its peers on the node.

# Multi-node job template (one task per GPU, no torchrun)
|  #!/bin/bash
|  #SBATCH --nodes=4
|  #SBATCH --ntasks-per-node=4
|  #SBATCH --gpus-per-node=4
|  #SBATCH --uenv=pytorch/v2.14.1
|  #SBATCH --view=torch
|  export MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -1)
|  export MASTER_PORT=29500
|  srun bash -c 'RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS python train.py'
In train.py: `torch.cuda.set_device(LOCAL_RANK)`, then
`torch.distributed.init_process_group("nccl", device_id=torch.device("cuda", LOCAL_RANK))`.

# Adding Python packages
Create a venv on top of the uenv (keeps the uenv's torch, TE, ...):
$ python -m venv --system-site-packages $SCRATCH/venvs/myproj
$ source $SCRATCH/venvs/myproj/bin/activate
$ pip install wandb numba                            # pure python / prebuilt wheels
CUDA extensions must build against the uenv's torch: disable build isolation.
$ pip install --no-build-isolation mamba-ssm causal-conv1d
> Build backends (setuptools, wheel, setuptools-scm, hatchling, poetry-core, scikit-build-core,
> flit-core), pybind11, cmake, ninja, nvcc and gcc 14 are in the view.
! Do not use `python -I` or set `PYTHONNOUSERSITE`: the uenv's packages are found through the
! user site directory (`PYTHONUSERBASE` points at the view), also inside venvs.

# Megatron-LM
Megatron is not part of the image: clone your fork and build its C++ dataset helpers once.
$ git clone https://github.com/swiss-ai/Megatron-LM.git && cd Megatron-LM
$ python setup.py build_ext --inplace                # builds megatron/core/datasets/helpers_cpp
$ export MEGATRON_LM_DIR=$PWD PYTHONPATH=$PWD:$PYTHONPATH
sentencepiece, tiktoken and flask-restful (tokenizers, inference server) are included.
! swiss-ai fork (multimodality/main, c3d83c5): two bugs, fixed by patches in the image:
$ git apply /user-environment/meta/extra/megatron/fix-tp-assistant-mask.patch
$ git apply /user-environment/meta/extra/megatron/fix-fp8-training-padding-slice.patch
>   fix-tp-assistant-mask: TP>1 without --ap-sft deadlocks at the first step
>   fix-fp8-training-padding-slice: fp8 training crashes ('NoneType' ... 'padding_slice')
! The fork stops training when `<trigger-path>/exit` exists, and a finished run creates it:
! use a fresh `--trigger-path` per run.
Measured on 4 nodes (8B Apertus shape, seq 8192, TP=2), TFLOP/s per GPU:
|  bf16, test defaults                                            358
|  + --fp8-format hybrid --fp8-recipe delayed
|    --fp8-amax-history-len 1024 --fp8-amax-compute-algo max     441
|  + --fp8-param-gather, --micro-batch-size 2                    453
|  + --sequence-parallel --tp-comm-overlap
|    --tp-comm-bootstrap-backend nccl   (needs UB_SKIPMC=1)      456-471
Recommended environment for Megatron runs:
$ export CUDA_DEVICE_MAX_CONNECTIONS=1
$ export UB_SKIPMC=1                                 # TP comm overlap: no NVLink multicast here
$ export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True    # -8 GiB GPU memory per node
> Keep the default attention backend (cuDNN fused); `--attention-backend flash` is ~7% slower.

# Environment set by the view
|  NCCL_NET="AWS Libfabric", NCCL_*, FI_PROVIDER=cxi, FI_CXI_*   Slingshot settings
|  SLURM_NETWORK=disable_rdzv_get   see "Launching torch/NCCL jobs"
|  NCCL_GRAPH_REGISTER=0            NCCL collectives across nodes inside CUDA graphs
|  NVSHMEM_REMOTE_TRANSPORT=libfabric, NVSHMEM_LIBFABRIC_PROVIDER=cxi
|  TRITON_CACHE_DIR, TORCHINDUCTOR_CACHE_DIR    JIT caches on node-local /tmp/$USER
|  CUDA_HOME, PYTHONUSERBASE        the view; nvcc is available for JIT/extension builds
! Do not point the JIT caches at a shared filesystem with several nodes:
! concurrent writers fail with `[Errno 116] Stale file handle`.
`NCCL_CROSS_NIC=0` and `NCCL_PXN_DISABLE=1` are set for large runs. On a few nodes they halve
NCCL bandwidth for mid-size messages (measured on 2 nodes, bus bandwidth):
|                                         all-reduce 1 MiB  all-gather 1 MiB  all-reduce 1 GiB
|  view defaults                                  6.7 GB/s          5.0 GB/s          154 GB/s
|  NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0           15.7 GB/s         11.3 GB/s          150 GB/s
For small jobs dominated by mid-size collectives, try overriding them:
$ export NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0
> Measure with your own workload: the large-message bandwidth is unchanged or slightly lower.

# Benchmarks included
|  all_reduce_perf, all_gather_perf, reduce_scatter_perf, alltoall_perf, ...   (nccl-tests)
|  $CUDA_HOME/libexec/osu-micro-benchmarks/mpi/{pt2pt,collective}/osu_*      (OSU, cray-mpich)
|  $CUDA_HOME/bin/perftest/device/coll/alltoall_latency, ...                 (NVSHMEM perftest)
$ srun -N2 --ntasks-per-node=4 --gpus-per-node=4 all_reduce_perf -b 8 -e 4G -f 2 -g 1

# Notes
* CUDA 13.3 runs on the Alps driver (CUDA 13.2) through minor-version compatibility: kernels are
  precompiled for sm_90a; Triton and torch.compile generate sm_90a code with the uenv's ptxas.
* Not included: numba and wandb (`pip install` them in a venv), torchaudio (no release for
  torch 2.14), TensorRT/torch-tensorrt/DALI (binary-only NVIDIA wheels).
* Build notes and test results for maintainers: /user-environment/meta/recipe/README.md
"""

# ANSI styles
BOLD, RESET = "\033[1m", "\033[0m"
HEAD = "\033[1;38;5;45m"  # bold cyan-blue
CMD = "\033[38;5;114m"  # green
CODE = "\033[38;5;80m"  # cyan
NOTE = "\033[38;5;221m"  # yellow
WARN = "\033[38;5;203m"  # red
DIM = "\033[2m"


def inline(text, base=""):
    return re.sub(r"`([^`]+)`", lambda m: f"{BOLD}{m.group(1)}{RESET}{base}", text)


def render(src):
    out = []
    for line in src.strip("\n").splitlines():
        if line.startswith("# "):
            title = line[2:]
            if out and out[-1] != "":
                out.append("")
            out += [f"{HEAD}{title}{RESET}", f"{DIM}{'─' * max(len(title), 8)}{RESET}"]
        elif line.startswith("$ "):
            out.append(f"  {DIM}${RESET} {CMD}{line[2:]}{RESET}")
        elif line.startswith("> "):
            out.append(f"  {NOTE}▸ {inline(line[2:], NOTE)}{RESET}")
        elif line.startswith("! "):
            out.append(f"  {WARN}! {inline(line[2:], WARN)}{RESET}")
        elif line.startswith("| "):
            out.append(f"    {CODE}{line[2:]}{RESET}")
        else:
            out.append(inline(line))
    return "\n".join(out) + "\n\n"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "extra", "readme.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(render(README))
    print(f"wrote {path}")
