[1;33mPyTorch 2.14.1 uenv for Alps GH200[0m

PyTorch 2.14.1 with CUDA 13.3, cuDNN 9.24, NCCL 2.30.7 and aws-ofi-nccl 1.20 for the Slingshot
network, NVSHMEM 3.6.5, cray-mpich 9.1, Triton 3.8, TransformerEngine 2.17, flash-attn 2.8.3,
apex, torchao 0.18, torchvision, the Hugging Face libraries (transformers, datasets, tokenizers),
ONNX, modelopt and nvidia-resiliency-ext. The package set follows the NGC pytorch 26.07
container, built for GH200 (sm_90a). The default view, [1mtorch[0m, puts everything on PATH.

[1;33mGetting started[0m

Start an interactive session, or run a single command:

  [36muenv start --view=torch pytorch/v2.14.1[0m
  [36muenv run pytorch/v2.14.1 -- python -c 'import torch; print(torch.cuda.device_count())'[0m

In Slurm jobs, load the uenv in the batch script header:

  [36m#SBATCH --uenv=pytorch/v2.14.1[0m
  [36m#SBATCH --view=torch[0m

Run [1mreadme[0m to show this text again.

[1;33mLaunching torch and NCCL jobs[0m

[1mNote: [0mtorch/NCCL jobs on Alps must run with the Slingshot option disable_rdzv_get.

The torch view sets [1mSLURM_NETWORK=disable_rdzv_get[0m, so every srun started inside the view
uses it: batch scripts with [1m#SBATCH --uenv[0m and [1m--view[0m, and [1muenv start[0m sessions. An srun
launched from outside the uenv starts before the view is loaded, so it needs the flag itself:

  [36msrun --network=disable_rdzv_get --uenv=pytorch/v2.14.1 --view=torch python train.py[0m

Without it, all-reduce across 4 nodes reaches about 74 instead of 93 GB/s. Give every task all
GPUs of its node ([1m--gpus-per-node=4[0m, not [1m--gpus-per-task=1[0m), so that NCCL can see its peers.

[1;33mMulti-node job template[0m

One task per GPU, without torchrun:

  [36m#!/bin/bash[0m
  [36m#SBATCH --nodes=4[0m
  [36m#SBATCH --ntasks-per-node=4[0m
  [36m#SBATCH --gpus-per-node=4[0m
  [36m#SBATCH --uenv=pytorch/v2.14.1[0m
  [36m#SBATCH --view=torch[0m

  [36mexport MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -1)[0m
  [36mexport MASTER_PORT=29500[0m
  [36msrun bash -c 'RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS python train.py'[0m

In train.py, call [1mtorch.cuda.set_device(LOCAL_RANK)[0m and then
[1mtorch.distributed.init_process_group("nccl", device_id=torch.device("cuda", LOCAL_RANK))[0m.

[1;33mAdding Python packages[0m

Create a virtual environment on top of the uenv. It keeps using the uenv's torch,
TransformerEngine and the other packages:

  [36mpython -m venv --system-site-packages $SCRATCH/venvs/myproj[0m
  [36msource $SCRATCH/venvs/myproj/bin/activate[0m
  [36mpip install wandb numba[0m

CUDA extensions have to build against the uenv's torch, so disable build isolation:

  [36mpip install --no-build-isolation mamba-ssm causal-conv1d[0m

The view provides the usual build backends (setuptools, wheel, setuptools-scm, hatchling,
poetry-core, scikit-build-core, flit-core), pybind11, cmake, ninja, nvcc and gcc 14.

[1mNote: [0mThe uenv's packages are found through the user site directory (PYTHONUSERBASE
      points at the view), also inside a venv: do not use [1mpython -I[0m or set
      PYTHONNOUSERSITE.

[1;33mMegatron-LM[0m

Megatron is not part of the image. Clone your fork and build its C++ dataset helpers once:

  [36mgit clone https://github.com/swiss-ai/Megatron-LM.git && cd Megatron-LM[0m
  [36mpython setup.py build_ext --inplace[0m
  [36mexport MEGATRON_LM_DIR=$PWD PYTHONPATH=$PWD:$PYTHONPATH[0m

sentencepiece, tiktoken and flask-restful (tokenizers and the inference server) are included.

The swiss-ai fork (multimodality/main, c3d83c5) has two bugs: with TP>1 and without --ap-sft
it deadlocks at the first step, and fp8 training crashes ('NoneType' object has no attribute
'padding_slice'). The image includes patches for both:

  [36mgit apply /user-environment/meta/extra/megatron/fix-tp-assistant-mask.patch[0m
  [36mgit apply /user-environment/meta/extra/megatron/fix-fp8-training-padding-slice.patch[0m

[1mNote: [0mThe fork stops training when <trigger-path>/exit exists, and a finished run
      creates that file. Use a fresh --trigger-path for every run.

Measured throughput on 4 nodes (the 8B Apertus shape, sequence length 8192, TP=2), in TFLOP/s
per GPU, each line adding to the one above:

  [36mbf16, test defaults                                            358[0m
  [36m--fp8-format hybrid --fp8-recipe delayed[0m
  [36m  --fp8-amax-history-len 1024 --fp8-amax-compute-algo max      441[0m
  [36m--fp8-param-gather --micro-batch-size 2                        453[0m
  [36m--sequence-parallel --tp-comm-overlap[0m
  [36m  --tp-comm-bootstrap-backend nccl                             456-471[0m

Recommended environment for Megatron runs. UB_SKIPMC=1 is needed for TP comm overlap because
these nodes have no NVLink multicast, and expandable segments save about 8 GiB of GPU memory per
node:

  [36mexport CUDA_DEVICE_MAX_CONNECTIONS=1[0m
  [36mexport UB_SKIPMC=1[0m
  [36mexport PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True[0m

Keep the default attention backend (cuDNN fused attention): [1m--attention-backend flash[0m is
about 7% slower.

[1;33mEnvironment set by the view[0m

The view sets the Slingshot settings for NCCL and libfabric (NCCL_NET="AWS Libfabric",
NCCL_*, FI_PROVIDER=cxi, FI_CXI_*), NVSHMEM's libfabric transport, SLURM_NETWORK (see above),
and NCCL_GRAPH_REGISTER=0, which NCCL collectives across nodes inside CUDA graphs need.
TRITON_CACHE_DIR and TORCHINDUCTOR_CACHE_DIR point to node-local /tmp/$USER, and CUDA_HOME and
PYTHONUSERBASE point to the view, so nvcc is available for JIT and extension builds.

[1mNote: [0mDo not move the JIT caches to a shared filesystem when running on several
      nodes: concurrent writers fail with "[Errno 116] Stale file handle".

NCCL_CROSS_NIC=0 and NCCL_PXN_DISABLE=1 are set for large runs. On a few nodes they halve the
NCCL bandwidth of mid-size messages (bus bandwidth on 2 nodes):

  [36m                                        all-reduce 1 MiB  all-gather 1 MiB  all-reduce 1 GiB[0m
  [36mview defaults                                   6.7 GB/s          5.0 GB/s          154 GB/s[0m
  [36mNCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0            15.7 GB/s         11.3 GB/s          150 GB/s[0m

For a small job dominated by mid-size collectives, try overriding them, and measure with your
own workload:

  [36mexport NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0[0m

[1;33mBenchmarks included[0m

The nccl-tests (all_reduce_perf, all_gather_perf, reduce_scatter_perf, alltoall_perf, ...)
are on PATH. The OSU benchmarks are in $CUDA_HOME/libexec/osu-micro-benchmarks/mpi, and the
NVSHMEM perftests in $CUDA_HOME/bin/perftest:

  [36msrun -N2 --ntasks-per-node=4 --gpus-per-node=4 all_reduce_perf -b 8 -e 4G -f 2 -g 1[0m

[1;33mNotes[0m

CUDA 13.3 runs on the Alps driver (CUDA 13.2) through CUDA minor-version compatibility: the
kernels are precompiled for sm_90a, and Triton and torch.compile generate sm_90a code with the
uenv's ptxas.

Not included: numba and wandb (pip install them in a venv), torchaudio (no release for
torch 2.14), and TensorRT, torch-tensorrt and DALI (binary-only NVIDIA wheels).

Build notes and test results for maintainers: /user-environment/meta/recipe/README.md
