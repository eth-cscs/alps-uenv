[1;38;5;45mPyTorch 2.14.1 uenv for Alps GH200[0m
[2m──────────────────────────────────[0m
PyTorch 2.14.1, CUDA 13.3, cuDNN 9.24, NCCL 2.30.7 + aws-ofi-nccl 1.20 (Slingshot), NVSHMEM 3.6.5,
cray-mpich 9.1, Triton 3.8, TransformerEngine 2.17, flash-attn 2.8.3, apex, torchao 0.18,
torchvision, Hugging Face (transformers, datasets, tokenizers), ONNX, modelopt, resiliency-ext.
The package set follows the NGC pytorch 26.07 container. Built for sm_90a (GH200).
The default view [1mtorch[0m puts everything on PATH.

[1;38;5;45mStart[0m
[2m────────[0m
  [2m$[0m [38;5;114muenv start --view=torch pytorch/v2.14.1            # interactive[0m
  [2m$[0m [38;5;114muenv run pytorch/v2.14.1 -- python -c 'import torch; print(torch.cuda.device_count())'[0m
  [2m$[0m [38;5;114mpytorch-readme                                     # print this readme again[0m
In Slurm jobs, use the uenv Slurm plugin in the batch script header:
    [38;5;80m #SBATCH --uenv=pytorch/v2.14.1[0m
    [38;5;80m #SBATCH --view=torch[0m

[1;38;5;45mLaunching torch/NCCL jobs: --network=disable_rdzv_get[0m
[2m─────────────────────────────────────────────────────[0m
  [38;5;203m! torch/NCCL jobs on Alps must run with the Slingshot option [1mdisable_rdzv_get[0m[38;5;203m.[0m
The torch view sets [1mSLURM_NETWORK=disable_rdzv_get[0m, so every srun started inside the view uses it
(batch scripts with [1m#SBATCH --uenv[0m/[1m--view[0m, [1muenv start[0m sessions).
A direct srun from outside the uenv starts before the view is loaded and needs the flag:
  [2m$[0m [38;5;114msrun --network=disable_rdzv_get --uenv=pytorch/v2.14.1 --view=torch python train.py[0m
  [38;5;221m▸ Without it, 4-node NCCL all-reduce reaches ~74 instead of ~93 GB/s bus bandwidth.[0m
  [38;5;203m! Give every task all GPUs of its node ([1m--gpus-per-node=4[0m[38;5;203m, not [1m--gpus-per-task=1[0m[38;5;203m):[0m
  [38;5;203m! NCCL needs to see its peers on the node.[0m

[1;38;5;45mMulti-node job template (one task per GPU, no torchrun)[0m
[2m───────────────────────────────────────────────────────[0m
    [38;5;80m #!/bin/bash[0m
    [38;5;80m #SBATCH --nodes=4[0m
    [38;5;80m #SBATCH --ntasks-per-node=4[0m
    [38;5;80m #SBATCH --gpus-per-node=4[0m
    [38;5;80m #SBATCH --uenv=pytorch/v2.14.1[0m
    [38;5;80m #SBATCH --view=torch[0m
    [38;5;80m export MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELIST | head -1)[0m
    [38;5;80m export MASTER_PORT=29500[0m
    [38;5;80m srun bash -c 'RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS python train.py'[0m
In train.py: [1mtorch.cuda.set_device(LOCAL_RANK)[0m, then
[1mtorch.distributed.init_process_group("nccl", device_id=torch.device("cuda", LOCAL_RANK))[0m.

[1;38;5;45mAdding Python packages[0m
[2m──────────────────────[0m
Create a venv on top of the uenv (keeps the uenv's torch, TE, ...):
  [2m$[0m [38;5;114mpython -m venv --system-site-packages $SCRATCH/venvs/myproj[0m
  [2m$[0m [38;5;114msource $SCRATCH/venvs/myproj/bin/activate[0m
  [2m$[0m [38;5;114mpip install wandb numba                            # pure python / prebuilt wheels[0m
CUDA extensions must build against the uenv's torch: disable build isolation.
  [2m$[0m [38;5;114mpip install --no-build-isolation mamba-ssm causal-conv1d[0m
  [38;5;221m▸ Build backends (setuptools, wheel, setuptools-scm, hatchling, poetry-core, scikit-build-core,[0m
  [38;5;221m▸ flit-core), pybind11, cmake, ninja, nvcc and gcc 14 are in the view.[0m
  [38;5;203m! Do not use [1mpython -I[0m[38;5;203m or set [1mPYTHONNOUSERSITE[0m[38;5;203m: the uenv's packages are found through the[0m
  [38;5;203m! user site directory ([1mPYTHONUSERBASE[0m[38;5;203m points at the view), also inside venvs.[0m

[1;38;5;45mMegatron-LM[0m
[2m───────────[0m
Megatron is not part of the image: clone your fork and build its C++ dataset helpers once.
  [2m$[0m [38;5;114mgit clone https://github.com/swiss-ai/Megatron-LM.git && cd Megatron-LM[0m
  [2m$[0m [38;5;114mpython setup.py build_ext --inplace                # builds megatron/core/datasets/helpers_cpp[0m
  [2m$[0m [38;5;114mexport MEGATRON_LM_DIR=$PWD PYTHONPATH=$PWD:$PYTHONPATH[0m
sentencepiece, tiktoken and flask-restful (tokenizers, inference server) are included.
  [38;5;203m! swiss-ai fork (multimodality/main, c3d83c5): two bugs, fixed by patches in the image:[0m
  [2m$[0m [38;5;114mgit apply /user-environment/meta/extra/megatron/fix-tp-assistant-mask.patch[0m
  [2m$[0m [38;5;114mgit apply /user-environment/meta/extra/megatron/fix-fp8-training-padding-slice.patch[0m
  [38;5;221m▸   fix-tp-assistant-mask: TP>1 without --ap-sft deadlocks at the first step[0m
  [38;5;221m▸   fix-fp8-training-padding-slice: fp8 training crashes ('NoneType' ... 'padding_slice')[0m
  [38;5;203m! The fork stops training when [1m<trigger-path>/exit[0m[38;5;203m exists, and a finished run creates it:[0m
  [38;5;203m! use a fresh [1m--trigger-path[0m[38;5;203m per run.[0m
Measured on 4 nodes (8B Apertus shape, seq 8192, TP=2), TFLOP/s per GPU:
    [38;5;80m bf16, test defaults                                            358[0m
    [38;5;80m + --fp8-format hybrid --fp8-recipe delayed[0m
    [38;5;80m   --fp8-amax-history-len 1024 --fp8-amax-compute-algo max     441[0m
    [38;5;80m + --fp8-param-gather, --micro-batch-size 2                    453[0m
    [38;5;80m + --sequence-parallel --tp-comm-overlap[0m
    [38;5;80m   --tp-comm-bootstrap-backend nccl   (needs UB_SKIPMC=1)      456-471[0m
Recommended environment for Megatron runs:
  [2m$[0m [38;5;114mexport CUDA_DEVICE_MAX_CONNECTIONS=1[0m
  [2m$[0m [38;5;114mexport UB_SKIPMC=1                                 # TP comm overlap: no NVLink multicast here[0m
  [2m$[0m [38;5;114mexport PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True    # -8 GiB GPU memory per node[0m
  [38;5;221m▸ Keep the default attention backend (cuDNN fused); [1m--attention-backend flash[0m[38;5;221m is ~7% slower.[0m

[1;38;5;45mEnvironment set by the view[0m
[2m───────────────────────────[0m
    [38;5;80m NCCL_NET="AWS Libfabric", NCCL_*, FI_PROVIDER=cxi, FI_CXI_*   Slingshot settings[0m
    [38;5;80m SLURM_NETWORK=disable_rdzv_get   see "Launching torch/NCCL jobs"[0m
    [38;5;80m NCCL_GRAPH_REGISTER=0            NCCL collectives across nodes inside CUDA graphs[0m
    [38;5;80m NVSHMEM_REMOTE_TRANSPORT=libfabric, NVSHMEM_LIBFABRIC_PROVIDER=cxi[0m
    [38;5;80m TRITON_CACHE_DIR, TORCHINDUCTOR_CACHE_DIR    JIT caches on node-local /tmp/$USER[0m
    [38;5;80m CUDA_HOME, PYTHONUSERBASE        the view; nvcc is available for JIT/extension builds[0m
  [38;5;203m! Do not point the JIT caches at a shared filesystem with several nodes:[0m
  [38;5;203m! concurrent writers fail with [1m[Errno 116] Stale file handle[0m[38;5;203m.[0m
[1mNCCL_CROSS_NIC=0[0m and [1mNCCL_PXN_DISABLE=1[0m are set for large runs. On a few nodes they halve
NCCL bandwidth for mid-size messages (measured on 2 nodes, bus bandwidth):
    [38;5;80m                                        all-reduce 1 MiB  all-gather 1 MiB  all-reduce 1 GiB[0m
    [38;5;80m view defaults                                  6.7 GB/s          5.0 GB/s          154 GB/s[0m
    [38;5;80m NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0           15.7 GB/s         11.3 GB/s          150 GB/s[0m
For small jobs dominated by mid-size collectives, try overriding them:
  [2m$[0m [38;5;114mexport NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0[0m
  [38;5;221m▸ Measure with your own workload: the large-message bandwidth is unchanged or slightly lower.[0m

[1;38;5;45mBenchmarks included[0m
[2m───────────────────[0m
    [38;5;80m all_reduce_perf, all_gather_perf, reduce_scatter_perf, alltoall_perf, ...   (nccl-tests)[0m
    [38;5;80m $CUDA_HOME/libexec/osu-micro-benchmarks/mpi/{pt2pt,collective}/osu_*      (OSU, cray-mpich)[0m
    [38;5;80m $CUDA_HOME/bin/perftest/device/coll/alltoall_latency, ...                 (NVSHMEM perftest)[0m
  [2m$[0m [38;5;114msrun -N2 --ntasks-per-node=4 --gpus-per-node=4 all_reduce_perf -b 8 -e 4G -f 2 -g 1[0m

[1;38;5;45mNotes[0m
[2m────────[0m
* CUDA 13.3 runs on the Alps driver (CUDA 13.2) through minor-version compatibility: kernels are
  precompiled for sm_90a; Triton and torch.compile generate sm_90a code with the uenv's ptxas.
* Not included: numba and wandb ([1mpip install[0m them in a venv), torchaudio (no release for
  torch 2.14), TensorRT/torch-tensorrt/DALI (binary-only NVIDIA wheels).
* Build notes and test results for maintainers: /user-environment/meta/recipe/README.md

