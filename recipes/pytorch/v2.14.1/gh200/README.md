# pytorch/v2.14.1 (gh200) — build notes

Build log for the next build of this recipe; not user-facing documentation.
The recipe started from `alps-uenv/recipes/pytorch/v2.9.1/gh200`, ported to stackinator v7 (`version: 3`, spack v1.2.2, spack-packages `be3466d5`).
The package set follows the Alps `pytorch-cuda:26.07-py3` container (NGC `nvcr.io/nvidia/pytorch:26.07-py3` plus the alps-extended-images network stack); `ngc-26.07-packages.txt` lists the Python packages in the NGC image.

## User readme (the `readme` command)

The user-facing documentation is a readme shown by the `readme` command in the `torch` view.

| File | Purpose |
|---|---|
| `make-readme.py` | source of the readme text (simple line markup) and an ANSI renderer; run `python3 make-readme.py` after editing |
| `extra/readme.txt` | the generated, ANSI-coloured readme (commit it with `make-readme.py`) |
| `extra/bin/readme` | the command: `less -RFX` on a terminal, plain text when piped or with `NO_COLOR` set |
| `extra/megatron/*.patch` | the two swiss-ai Megatron-LM fork fixes, referenced by the readme (installed as `/user-environment/meta/extra/megatron/`) |
| `post-install` | installs `meta/extra/readme.txt` as `/user-environment/readme` and `extra/bin/*` into `env/torch/bin` |

Stackinator copies `extra/` to `/user-environment/meta/extra`. Keep numbers in the readme consistent with the results below when they change.
The renderer is taken from the vllm uenv recipe (`make-guide.py`).

## Open items

### MAGMA: concretized with 2.10.0, NGC uses 2.6.2

NGC 26.07 statically links **MAGMA 2.6.2** into `torch/lib/libtorch_cuda_linalg.so` (`magma_version()` returns 2.6.2; no `libmagma` or dpkg package in the image).
PyTorch's own CI builds MAGMA 2.6.1 with `.ci/magma/package_files/cuda13.patch`.

This recipe instead uses **magma@2.10.0**, because:

- upstream spack `magma` declares `conflicts("^cuda@13:", when="@:2.9.0")`;
- upstream spack `py-torch` requires `magma@:2.9` (pytorch PR 178065, an attempt to move to newer MAGMA, was closed unmerged).

The custom `repo/packages/py_torch` is upstream `be3466d5` with one change: `magma@2.10:` is allowed for `@2.14: +magma +cuda ^cuda@13:`.
torch 2.14 with MAGMA 2.10 is not tested upstream.

Revisit after the build, or earlier if 2.10.0 fails to build or `torch.linalg` misbehaves on GPU.
Status (2026-11-04): magma 2.10.0 builds, and the GPU `torch.linalg.inv` / `eigvals` tests with the magma backend match CPU; broader linalg coverage has not been tested.
Options:

1. custom `magma@2.6.2` with PyTorch's `cuda13.patch` (as NGC/PyTorch CI do), and drop the `py_torch` magma override;
2. `py-torch ~magma` (linalg falls back to cuSOLVER/cuBLAS).

Changing magma changes the py-torch hash, so it means rebuilding torch and its dependents.

### Image size: fixes found in the a100 recipe, not applied here yet

The a100 port (`../a100/README.md`, 2026-11-04) found package problems that apply to this recipe too.
On a100 they took the image from 10.1 to 8.9 GB (21.3 to 18.4 GB unpacked); the gh200 sizes have not been measured.
To apply them, copy the package files from `../a100/repo/packages/`:

- **cutlass** (`cutlass/package.py`): set `CUTLASS_ENABLE_HEADERS_ONLY=ON`.
  The default build compiles the CUTLASS kernel library and profiler (965 MB on a100) and installs the unit tests (593 MB).
  The only consumer, nvidia-mathdx, needs only the headers and CMake config.
  This also makes the build much shorter. It changes the cutlass hash, so nvidia-mathdx and py-transformer-engine rebuild.
- **dynolog** (`dynolog/package.py`): change to `depends_on("rust", type="build")`.
  The link dependency keeps rust (1.3 GB) in the image after `cleanup: runtime`, but the dynolog/dyno binaries do not link any rust library.
- **py-torchao** (`py_torchao/package.py`): `setup.py` builds `_C_cutlass_90a` (sm_90a) and `_C_mxfp8` (sm_100) whenever CUDA >= 12.8, ignoring `TORCH_CUDA_ARCH_LIST`.
  The a100 `patch()` builds each one only when `cuda_arch` matches.
  Here that keeps `_C_cutlass_90a` and drops `_C_mxfp8` (~3 MB, sm_100 SASS + compute_120 PTX, cannot run on sm_90).
  The a100 package also derives `TORCH_CUDA_ARCH_LIST` from `cuda_arch` instead of hardcoding `9.0a`; for `cuda_arch=90a` the value is the same.
- **py-flash-attn** (`py_flash_attn/package.py`): the a100 package derives `FLASH_ATTN_CUDA_ARCHS` from `cuda_arch` instead of hardcoding `90`.
  This makes no difference here, but keeps the two recipes' packages identical.
- **py-torch-nvidia-apex**: the a100 `patch()` skips `group_norm_v2_cuda` (hardcoded sm_90/sm_100/compute_120) when no `cuda_arch` is >= 90.
  This does not change gh200, where the extension is built and usable; it carries sm_100 SASS and compute_120 PTX (~39 MB in total on a100) that could only be removed by patching its `arch_flags`.

The a100 recipe also has a script that lists the shared objects containing CUDA code for archs other than the target (`/scratch/mch/bcumming/torch-uenv-a100/tests/arch_scan.sh` on linard; change `sm_80` and `linux-zen3` for gh200).

## Build fixes

Several fixes come from the vllm uenv recipe (`/users/bcumming/uenv/vllm/recipe`, see its README).

- **nvshmem 3.6.5-0** failed in the perftests with MPICH (`cast from 'void*' to 'MPI_Comm' {aka 'int'} loses precision`).
  The existing `v3.4.5-perftest-mpich.patch` applies to 3.6.5-0 (offset 38 lines), so its `when=` now covers both versions.
- **gloo** (`gloo@2026-06-10 +cuda`: `c10/util/BFloat16.h: No such file or directory`): `gloo+cuda` includes py-torch's own c10 headers, a circular dependency.
  As in the vllm uenv, `repo/packages/py_torch` no longer requires `gloo+cuda`, and sets `USE_SYSTEM_GLOO=OFF` for `+gloo+cuda`, so torch builds its vendored `third_party/gloo`.
  Unlike the vllm uenv, the external gloo dependency is limited to `+gloo~cuda`, so no unused gloo is built.
- **py-triton 3.8.0** (CMake: `Could not find TRITON_GSAN_CLANGXX using the following names: clang++`): 3.8 builds its GSan device runtime with `${LLVM_SYSPATH}/bin/clang++`.
  `repo/packages/py_triton` is now the vllm uenv's package (pinned llvm-project as a checksummed `resource()`, offline build, CUDA tools/headers symlinked into `triton/backends/nvidia`), extended to 3.8.0: llvm `5f07f818` from `cmake/llvm-info.json`, and `clang` added to `LLVM_ENABLE_PROJECTS` for `@3.8:`.
  The previous package git-cloned llvm-project during the build and relied on `setup_run_environment`, which views do not apply.
- **llvm 22.1.8** (link failures in `lli`, `llvm-lto`): only needed by `py-numba -> py-llvmlite`; resolved by commenting out py-numba (see below).
- **fbgemm**: `py-torch ~fbgemm`, because `+fbgemm` fails to link on aarch64 (found in the vllm uenv).
- **ucc 1.8.0** failed, but ucx/ucc have been dropped (see below).
- **py-flash-attn 2.8.3** (`nvcc fatal: Failed to preprocess host compiler properties`): torch's cpp_extension calls nvcc without `-ccbin`, so nvcc uses the first `gcc` on `PATH`, Spack's compiler wrapper.
  Upstream py-flash-attn only declares `depends_on("cxx")`, and without a C compiler the wrapper `gcc` fails; added `depends_on("c", type="build")`.
  Reproduced in the sandbox (`spack -e env build-env py-flash-attn`): plain `nvcc -c` failed, `nvcc -ccbin $CXX` worked.
  Second failure: torch 2.14 headers are C++20 (`c10/util/intrusive_ptr.h` uses `operator<=>` returning `std::strong_ordering`), but flash-attn's `setup.py` hardcodes `-std=c++17`; `patch()` replaces it with `-std=c++20` when building against `py-torch@2.14:`.
- **py-transformer-engine 2.17** (`Could not locate NCCL core (nccl.h + libnccl.so). Set NCCL_HOME`): the NCCL EP build finds NCCL via `NCCL_HOME`; the package now sets it to the spack nccl.
  Second failure: `nvshmem_tensor.h: fatal error: cuda/std/tuple: No such file or directory` in `csrc/extensions/nvshmem_comm.cpp`.
  CUDA 13 moved the CCCL headers to `include/cccl`; nvcc adds that path itself, but `.cpp` files are compiled by the host compiler, so the package appends it to `CPATH`.
- **py-nvidia-resiliency-ext 0.6.0**: the `tag="v0.6.0"` git checkout failed inside the build sandbox (`git checkout` exit 128) but works outside; switched to the release tarball with a sha256.
- **Memory**: torch's flash-attention units need 6-7 GB per `cicc` process (measured in the vllm uenv), so the build runs with `NJOBS=64`.
  Job caps in the custom packages: flash-attn `MAX_JOBS<=24`, `NVCC_THREADS=2`; TE `MAX_JOBS<=16`; torchao `MAX_JOBS<=32`; apex `APEX_PARALLEL_BUILD<=16`, nvcc `--threads 4` (it was `make_jobs` x `make_jobs`).

- **arrow `~parquet`** (runtime, found by testing the first image): Spack's arrow defaults to `~parquet`, so `import datasets` failed (`pyarrow ... not built with support for the Parquet file format`).
  This also disabled modelopt's transformers/HF plugins (the `ModelOptHFTrainer` import errors follow from it).
  `arrow +parquet +dataset +snappy +zstd +brotli` is now a root spec, close to the features of the PyPI pyarrow wheel; this only rebuilds arrow, thrift, brotli, pyarrow, datasets and torchtitan.
  `+lz4` was dropped: arrow 24's CMake finds liblz4 through pkg-config, then fails with `Could NOT find lz4Alt (missing: LZ4_LIB)`. Not investigated; Parquet files compressed with lz4 cannot be read.

Logs of the first attempt (2026-11-03): `$SCRATCH/ngc/failed-logs/`; second attempt: `$SCRATCH/ngc/run2/` (incl. `memlog.txt`).

## View environment

Beyond the alps-extended-images runtime settings, taken from the vllm uenv:

- `NCCL_GRAPH_REGISTER=0`: NCCL buffer registration during CUDA graph capture fails over aws-ofi-nccl/CXI for inter-node collectives inside CUDA graphs.
- `SLURM_NETWORK=disable_rdzv_get`: see "Launching jobs" (this one was added for this recipe, not taken from the vllm uenv).
- `TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR` in `/tmp/${@USER@}/`: on the shared filesystem concurrent writers on several nodes failed with `Stale file handle`.

## Validation

Test scripts are kept outside the recipe (`$SCRATCH/torch-uenv/tests/`), since the recipe directory is copied into the image.

Single node (4x GH200, 2026-11-04, first image):

- torch 2.14.1, CUDA 13.3, cuDNN 9.24.0, NCCL 2.30.7, 4 GPUs, arch list `['sm_90a']`.
- Pass: bf16 matmul; `torch.compile` (inductor + triton codegen) matches eager; custom triton JIT kernel; SDPA fwd/bwd; flash-attn fwd/bwd (max diff to SDPA 3.9e-3); TE `Linear` under fp8 autocast fwd/bwd; apex `FusedAdam` + `FusedLayerNorm`; torchao float8 training fwd/bwd.
  None of these hit PTX JIT errors, so CUDA 13.3 on the 13.2 driver works for these paths.
- Pass: `torch.linalg.inv` and non-symmetric `eigvals` with `preferred_linalg_library("magma")` match CPU (`torch.cuda.has_magma=True`), so magma 2.10 works for these ops.
- Fail in the first image (fixed, see arrow above): `import datasets`, `pyarrow.parquet`.
- The view provides `python`, `nvcc`, `gcc`/`g++` 14.2 (not the system gcc 7.5), `mpicc`, `cmake`, `ninja`, `all_reduce_perf`, OSU benchmarks.

Second image (arrow `+parquet`, 2026-11-04 10:34): all 49 checked modules import, all 11 single-node checks pass, modelopt's transformers/HF plugins load, and a Parquet write/`datasets.load_dataset` round trip works for snappy, zstd, brotli and gzip.

Multi-node (aws-ofi-nccl 1.20.0 loaded as `AWS Libfabric` net plugin in every run):

| Test | Result |
|---|---|
| `all_reduce_perf`, 1 node, 4 ranks | 340 GB/s bus bandwidth (2 GiB) |
| `all_reduce_perf`, 2 nodes, 8 ranks | 160 GB/s (2 GiB) |
| `all_reduce_perf`, 4 nodes, 16 ranks | 39-54 GB/s on one allocation; 70-75 GB/s, reproducible, on another |
| same, `NCCL_CROSS_NIC=1` | ~70 GB/s (no improvement, so the container's `0` is kept) |
| `torch.distributed` all_reduce, 16 ranks | correct; 71.5 GB/s for 1 GiB bf16 |
| `osu_bw` D D, 2 nodes, cray-mpich | 22 GB/s (one Slingshot NIC is 25 GB/s) |

The low 4-node all-reduce is a launch setting, not a defect of the stack (see "Launching jobs").

## Launching jobs: `--network=disable_rdzv_get` is required

Torch/NCCL jobs on Alps must run with the Slingshot network option `disable_rdzv_get` (a CSCS requirement for torch/NCCL; the view's `FI_CXI_RDZV_PROTO=alt_read` relies on it).

- The `torch` view (the default view) sets `SLURM_NETWORK=disable_rdzv_get`, so every `srun` started *inside* the view uses it: batch scripts with `#SBATCH --uenv=...` / `#SBATCH --view=torch`, and `uenv start` sessions.
- A direct `srun --uenv=<image> --view=torch ...` from outside the uenv starts the step before the view is applied, so it needs the flag explicitly:
  ```bash
  srun --network=disable_rdzv_get --uenv=pytorch/v2.14.1 --view=torch python train.py
  ```
- Measured without it: 4-node NCCL all-reduce 74 GB/s instead of 93 GB/s (data below).
- Verified (job 5254387, when the view was still named `default`): a batch script with `#SBATCH --uenv=<image>` / `#SBATCH --view=default` sees `SLURM_NETWORK=disable_rdzv_get`, and a plain inner `srun` (no `--network` flag) reaches 93 GB/s on 4 nodes.

### Measurements

4 nodes x 4 GPUs, `all_reduce_perf` bus bandwidth at 4 GiB (jobs 5253873, 5253911, each in a single allocation):

| Setup | plain `srun` | `srun --network=disable_rdzv_get` |
|---|---|---|
| Alps 26.07 container | 74 GB/s (job 5254352) | 93 GB/s |
| uenv, `FI_CXI_RDZV_PROTO=alt_read` etc. (as the container) | 74 GB/s | 93 GB/s |
| uenv, libfabric default rendezvous settings | 74 GB/s | 91 GB/s |

- With `--network=disable_rdzv_get`, the uenv and the container perform the same; their NCCL/FI environments are identical.
- The container needs the flag as well (job 5254352, one allocation, 4 GiB): container 74 GB/s without / 93 GB/s with, uenv 74 / 93; without it the container prints its alt_read warning.
- The container is always launched with `--network=disable_rdzv_get` (its CI sets `SLURM_NETWORK`) and prints a warning when `FI_CXI_RDZV_PROTO=alt_read` is used without it.
- The flag, not the alt_read settings, is what matters; alt_read is slightly better with the flag, so it is kept.
- A uenv cannot add srun flags. `SLURM_NETWORK=disable_rdzv_get` in the view would apply to sruns started inside the view (sbatch with `--uenv`/`--view`, `uenv start`), not to a direct `srun --uenv=... --view=...`.
Effect of the flag on other traffic (job 5254306, one 4-node allocation; single runs):

| Test | plain `srun` | `--network=disable_rdzv_get` |
|---|---|---|
| `torch.distributed` all_reduce, 16 ranks, 1 GiB bf16 | 75.1 GB/s | 91.6 GB/s |
| NCCL `all_reduce_perf`, 2 nodes | 126-128 GB/s | 129-131 GB/s |
| `osu_bw` D D, cray-mpich | 22.4-23.0 GB/s | 22.5-23.5 GB/s |
| `osu_bw` H H | 23.0-23.6 GB/s | 22.0 GB/s |
| `osu_latency` 8 B | 6.24 us | 5.68 us |
| `osu_allreduce` D D, 16 ranks, 64 MiB | 2462 us | 2458 us |
| NCCL 4 nodes, `SLURM_NETWORK=disable_rdzv_get` exported, plain `srun` | 93 GB/s | |

- The flag helps NCCL (4 nodes +25%), and has no clear effect on cray-mpich (the 5% H H difference is within single-run noise).
- Setting `SLURM_NETWORK` in the environment before `srun` works as well as the flag.
- Decision (2026-11-04): the flag is a requirement for torch/NCCL jobs; document it and set `SLURM_NETWORK` in the view (above).

## Communication benchmarks against pytorch/v2.9.1 (2026-11-05)

The benchmarks of the v2.9.1 PR (alps-uenv PR #281: OSU `osu_bw` H-H/D-D, `osu_alltoall` with GPU buffers, nccl-tests, NVSHMEM device `alltoall_latency`), extended to all four NCCL collectives up to 4 GiB and 4 nodes, run on `pytorch/v2.9.1:v2` and this recipe's image in the same allocations (jobs 5262875, 5262878; investigation 5262892, 5262918).
Report: https://claude.ai/artifact/GMoXGo9xZ5NiaUzdHBCn3y. Scripts, logs and parsed data: `/ritom/scratch/cscs/bcumming/torch-uenv/comm-bench/` (`comm.sbatch`, `parse.py`, `make_report.py`, `results2/`, `data.json`).

- Large messages: equal or better (NCCL 4 GiB all-reduce 341 / 161 / 93 GB/s on 1 / 2 / 4 nodes; 2 nodes +6%); 4-node all-to-all at 4 GiB is 8% lower. MPI point-to-point and torch.distributed (92.8 GB/s, 16 ranks) are equal.
- **Mid-size NCCL messages across nodes are 2x slower on a few nodes** (1 MiB all-reduce 15.3 -> 6.8 GB/s on 2 nodes, all-gather/reduce-scatter -35 to -40%).
  Cause: `NCCL_CROSS_NIC=0` and `NCCL_PXN_DISABLE=1` in the view (taken from the alps-extended-images settings; v2.9.1 has `NCCL_CROSS_NIC=1`, PXN enabled).
  With both as in v2.9.1: 2-node all-reduce at 1 MiB 6.7 -> 15.7 GB/s, all-gather 5.0 -> 11.5 GB/s, all-reduce 64 MiB 108 -> 114 GB/s; all-reduce 1 GiB 154 -> 149 GB/s.
  Decision (2026-11-05): keep `NCCL_CROSS_NIC=0` and `NCCL_PXN_DISABLE=1`, which are useful for larger runs; the user readme (`readme`, "Environment set by the view") documents them and the `NCCL_CROSS_NIC=1 NCCL_PXN_DISABLE=0` override for small jobs dominated by mid-size collectives, with these numbers.
  The Megatron results above were measured with the view defaults.
- `FI_CXI_SAFE_DEVMEM_COPY_THRESHOLD` and `FI_MR_CACHE_MAX_SIZE/COUNT` (only in this view) make no measurable difference.
- MPI `osu_alltoall` with GPU buffers: small messages slower (32 B on 2 nodes 25 -> 92 us), large ones faster (4 MiB on 4 nodes -15%); not caused by the environment, so cray-mpich 9.1 or libfabric 2.6.0; not investigated further.
- Launch note: an `srun -N <n> --ntasks-per-node=<k>` inside an `sbatch` job without `--ntasks` silently ran on one node (`can't run 1 processes on 2 nodes, setting nnodes to 1`); pass `-n` explicitly.

## Megatron-LM (2026-11-04)

Tested with the alps-extended-images apertus-1p5 test (`Alps-Images/apps/apertus-1p5/tests/megatron_pretrain.sh`): swiss-ai Megatron-LM `multimodality/main` at `c3d83c5a0` plus NVIDIA PR 1871, mock data, Apertus features (xIELU, AdEMAMix, goldfish loss, apex QK-norm).
The container used for comparison is `ghcr.io/eth-cscs/alps-extended-images/apertus-1p5-cuda:alps7-dev` (on pytorch-cuda 26.02: torch 2.11.0a0, CUDA 13.1, cuDNN 9.19, NCCL 2.29.2, TE 2.12), which ships the same Megatron commit in `/opt/megatron`.
Benchmark scripts and logs: `$SCRATCH/torch-uenv/megatron-bench/` (`bench2.sbatch`, `megatron_pretrain_var.sh`, `memsummary.py`).

Using it with the uenv: clone the fork, `python setup.py build_ext --inplace` inside the uenv (builds `megatron/core/datasets/helpers_cpp`), set `MEGATRON_LM_DIR`; no extra Python packages were needed for this test.

Problems found (not uenv specific; they affect the container too):

- **TP>1 deadlock in the fork**: `get_batch_on_this_tp_rank` broadcasts `assistant_mask` from TP rank 0 whenever the dataset returns one (the GPT dataset always does), but the other TP ranks only receive it with `--ap-sft`.
  With TP>1 and no `--ap-sft`, rank 0 waits in an extra broadcast and the job hangs at the first step (in both stacks; `TORCH_DISTRIBUTED_DEBUG=DETAIL` shows BROADCAST [1, seq] vs REDUCE_SCATTER).
  The test's production default is TP=2; its CI uses TP=1, so CI does not see it.
  Fix: `$SCRATCH/torch-uenv/megatron-bench/fix-tp-assistant-mask.patch` (rank 0 only broadcasts it with `--ap-sft`); mounted into the container for the comparison.
- **fp8 training crash in the fork**: `Attention.forward` zeroes padding tokens via `inference_context.padding_slice` whenever quantization scales are used; the block is meant for dynamic-batching inference but sits at the level of the training branch, so fp8 training fails with `'NoneType' object has no attribute 'padding_slice'` (both stacks).
  Fix: `$SCRATCH/torch-uenv/megatron-bench/fix-fp8-training-padding-slice.patch` (guard on `inference_context is not None`); also mounted into the container.
- **Exit trigger**: the fork stops training when `<trigger-path>/exit` exists, and a finished run creates it; the test uses `/tmp/trigger_${SLURM_JOB_ID}`, so a second run in the same job stops after one iteration (uenv runs share the host `/tmp`; the container has a private `/tmp`).

8B shape (32 layers, hidden 4096, FFN 21504, GQA 8, seq 8192, TP=2, MBS 1, GBS 32, bf16), 4 nodes x 4 GPUs, mean of iterations 11-30, all launched with `SLURM_NETWORK=disable_rdzv_get`:

| Run (same allocation, job 5256192) | ms/iter | TFLOP/s/GPU | host RAM increase/node | GPU memory/node |
|---|---|---|---|---|
| container | 2267 | 355.2 | 111 GiB | 227 GiB |
| uenv | 2253 | 357.2 | 103 GiB | 229 GiB |
| uenv (repeat) | 2243 | 358.7 | 97 GiB | 231 GiB |

Memory: on GH200 the GPU HBM is part of the OS-visible memory, so "host RAM increase" = increase of `free` used minus GPU memory used; the idle node already uses 90-130 GiB.

bf16 and fp8 (`--fp8-format hybrid --fp8-recipe tensorwise`), both stacks in one allocation (job 5256518):

| Run | ms/iter | TFLOP/s/GPU | vs container bf16 | host RAM increase/node | GPU memory/node |
|---|---|---|---|---|---|
| container bf16 | 2281 | 352.8 | | 110 GiB | 230 GiB |
| uenv bf16 | 2244 | 358.6 | +1.6% | 108 GiB | 230 GiB |
| container fp8 | 1880 | 428.0 | +21.3% | 110 GiB | 239 GiB |
| uenv fp8 | 1838 | 437.7 | +24.1% | 108 GiB | 239 GiB |

The uenv is 1.6% (bf16) and 2.3% (fp8) faster than the container for the same Megatron code and flags.
bf16 loss curves of the two stacks agree (10.545 -> 2.32 after 30 iterations); the fp8 curves of the two stacks agree with each other.

Best settings, both stacks in one allocation (job 5256738): `--fp8-format hybrid --fp8-recipe tensorwise --fp8-param-gather`, `MBS=2`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`:

| Run | ms/iter | TFLOP/s/GPU | vs container bf16 | host RAM increase/node | GPU memory/node |
|---|---|---|---|---|---|
| container bf16 (test defaults) | 2305 | 349.1 | | 105 GiB | 229 GiB |
| container, best settings | 1974 | 407.6 | +16.8% | 137 GiB | 283 GiB |
| uenv, best settings | 1858 | 433.0 | +24.0% | 124 GiB | 284 GiB |

With the same settings the uenv is 6.2% faster than the container. MBS=2 helps the uenv slightly but makes the container slower than its plain fp8 run (407.6 vs 428.0 TFLOP/s/GPU in job 5256518).

Delayed fp8 recipe and TP comm overlap, one allocation (job 5256768); all runs `MBS=2`, `expandable_segments:True`, `--fp8-format hybrid --fp8-recipe delayed --fp8-amax-history-len 1024 --fp8-amax-compute-algo max --fp8-param-gather`:

| Run | ms/iter | TFLOP/s/GPU | host RAM increase/node | GPU memory/node |
|---|---|---|---|---|
| container | 1872 | 429.9 | 130 GiB | 289 GiB |
| uenv | 1776 | 453.2 (+5.4%) | 126 GiB | 292 GiB |
| uenv + `--sequence-parallel --tp-comm-overlap --tp-comm-bootstrap-backend nccl`, `UB_SKIPMC=1` | 1710 | 470.7 (+9.5%) | 123 GiB | 273 GiB |

The best uenv configuration is ~34% faster than the container with the test's default (bf16) settings (349-353 TFLOP/s/GPU).

Both stacks with TP comm overlap (same settings as the last row above), one allocation (job 5256869): container 1857 ms/iter, 433.6 TFLOP/s/GPU (144 GiB host RAM increase/node, 270 GiB GPU); uenv 1765 ms/iter, 456.1 TFLOP/s/GPU (+5.2%; 132 GiB, 271 GiB).
The uenv's absolute number differs by 3% between allocations (470.7 vs 456.1); within each allocation the uenv leads by 5-6% with tuned settings.

Summary (4 nodes x 4 GH200, same Megatron code and flags in both stacks):

| Settings | uenv vs container |
|---|---|
| test defaults (bf16) | +0.6-1.6% |
| fp8 tensorwise | +2.3% |
| fp8 tensorwise + param gather + MBS=2 | +6.2% |
| fp8 delayed + param gather + MBS=2 | +5.4% |
| same + sequence parallel + TP comm overlap | +5.2% |

Host RAM per node (increase during training, excluding GPU memory) is 2-14 GiB lower with the uenv in every same-allocation comparison.
Loss curves of the three runs agree (10.565 -> 2.07-2.17 after 30 iterations).

uenv tuning (job 5256611, against fp8 tensorwise at 429.4 TFLOP/s/GPU): delayed recipe (`--fp8-recipe delayed --fp8-amax-history-len 1024 --fp8-amax-compute-algo max`) 441.4 (+2.8%); `MBS=2` 439.6 (+2.4%, +78 GiB GPU/node); `--fp8-param-gather` 431.1 (+0.4%, -27 GiB GPU/node).
`--tp-comm-overlap` (TE userbuffers) fails: `CUDA device, driver and/or toolkit version does not support comm+GEMM overlap with CUDA Multicast` (no NVLS multicast on these nodes); `UB_SKIPMC=1` selects CUDA IPC instead.

Per-process memory (1 node, 16-layer variant, TP=2, peak sample of `/proc/<pid>/smaps_rollup`; `megatron-bench/rss3/`):

| | uenv | container |
|---|---|---|
| python processes | 38 | 152 |
| anonymous (private) memory, all processes | 13.1 GiB | 22.8 GiB |
| of which helper processes (inductor compile workers etc.) | 34 procs, 4.3 GiB | 140 procs, 10.4 GiB |
| total PSS | 96.5 GiB | 117.0 GiB |

Each training rank also maps ~20 GiB as shmem, about its GPU memory use (HBM is system memory on GH200), so it is not additional host RAM.
The container uses ~10 GiB more host RAM per node, mostly from 4x more helper processes (torch 2.11 vs 2.14 compile-worker defaults).
This does not fully account for the ~100 GiB/node "non-GPU increase" measured with `free` in the 4-node runs (different model size and measurement); not reconciled.

Attention backend (jobs 5256395/5256396): the default (`auto`) and `--attention-backend fused` (cuDNN) are equal; `--attention-backend flash` is 7.4% slower.
`--use-precision-aware-optimizer` is only supported with Adam (the test uses AdEMAMix).

Tuning (uenv, each against a baseline in the same allocation, jobs 5256254/5256255): `TORCH_NCCL_AVOID_RECORD_STREAMS=1`, `TORCHINDUCTOR_COMPILE_THREADS=1` and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` do not change throughput (within 0.1%); expandable_segments reduces GPU memory by 8 GiB/node. `--sequence-parallel` is 3.8% slower and uses 19 GiB/node less GPU memory. `NVTE_FUSED_ATTN`/`NVTE_FLASH_ATTN` are rejected by Megatron (use `--attention-backend`).

## Packages kept for users building on top of the uenv

- **Python build backends** (`py-wheel`, `py-setuptools-scm`, `py-hatchling`, `py-hatch-vcs`, `py-poetry-core`, `py-scikit-build-core`, `py-flit-core`) are explicit root specs.
  `cleanup: runtime` (`spack gc`) removes packages that are only needed to build the stack, which removed these from the first images (`import wheel` failed).
  Users build CUDA extensions against the uenv's torch with `pip install --no-build-isolation` (e.g. mamba-ssm, causal-conv1d, vllm), which needs the package's build backend to be installed.
  maturin and setuptools-rust are not kept: they need rust, which gc also removes.
- **Megatron-LM extras** (`py-sentencepiece`, `py-tiktoken`, `py-flask-restful`): the Alps apertus-1p5 (Megatron) container pip-installs these on top of its base image.
  sentencepiece and tiktoken back Megatron's `SentencePieceTokenizer`/`TikTokenizer` tokenizer types; flask-restful is used by Megatron's REST inference server (`tools/run_text_generation_server.py`).
  Megatron itself is not part of the image: it is pure Python plus one small C++ helper (`python setup.py build_ext --inplace`), and users run their own fork and version.
  wandb (also installed by the container) is not included: Spack's py-wandb needs go and rust to build; users can `pip install wandb`.

## Deviations from NGC 26.07

- torch 2.14.1 (NGC: 2.13.0a0 snapshot); triton 3.8.0 as pinned by torch 2.14 (NGC: 3.7.1); torchvision 0.29.1.
- CUDA 13.3.1 as in NGC, but the daint driver (595.91.07) supports CUDA 13.2: relies on CUDA minor-version compatibility.
  Packages must ship sm_90a SASS; JIT of 13.3 PTX by the 13.2 driver fails.
- MPI is cray-mpich 9.1.0 (the container builds OpenMPI).
- UCX and UCC are not included (both were root specs in pytorch/v2.9.1, and the container builds UCX 1.20.1 / UCC 1.8.0).
  Nothing in this stack depends on them: py-torch is `~ucc`, nvshmem is `~ucx`, and UCC was their only consumer.
  UCX has no Slingshot/CXI transport; inter-node traffic goes through libfabric CXI (aws-ofi-nccl, NVSHMEM libfabric transport, cray-mpich).
- numpy resolves to 2.5.4 (NGC 2.1.0).
- flash-attn 2.8.3 (NGC: NVIDIA fork of 2.7.4.post1); apex 26.09 tag (NGC: master build).
- numba/llvmlite are not included (NGC has numba 0.64.0, llvmlite 0.46.0); the spec is commented out in `environments.yaml`, with the reasons it might be re-enabled.
  Nothing in the stack depends on numba (Megatron-LM does not use it), and Spack's py-llvmlite builds a full llvm@22.
  Users can `pip install numba` on top of the uenv; the aarch64 llvmlite wheels link LLVM statically.
- Not included: torchaudio (not in NGC 26.07; 2.11 is the newest release, older than torch 2.14), TensorRT / torch-tensorrt / DALI / nvimgcodec / cutlass-dsl (binary-only wheels), Jupyter and the long tail.

## ReFrame tests (2026-11-24)

Image v7 (`$SCRATCH/torch-uenv/pytorch-v2.14.1-gh200-v7.squashfs`) on daint, cscs-reframe-tests `main` at a5cd74c2, ReFrame 4.10.4, `CSCS_RFM_UENV=<path to squashfs>` with `meta/` extracted beside it, `-p '(?!PrgEnv-.*|builtin)' -S build_locally=0`.
Stage directories and logs: `$SCRATCH/torch-uenv/reframe/run-*`.

The features in `extra/reframe.yaml` select 20 tests; 19 were run (ICON4PyBenchmarks, which matches any `+uenv +cuda` environment, was left out): 9 pass, 6 fail, 4 are skipped.

- Pass (9): StreamTest, cscs_gpu_burn_check, NCCLTestsUENV all_reduce (145.8 GB/s) and sendrecv (23.4 GB/s) on 2 nodes, OSUBandwidthCuda, osu_pt2pt_check osu_bw and osu_latency (CPU build), osu_collective_check alltoall and allreduce (CPU build, 6 nodes).
- OSULatency, OSUBandwidth, OSULatencyCuda fail the 256 byte reference and pass the 4 MiB one (10.9 us vs 2.3 us; 275 MB/s vs 600 MB/s; 11.7 us vs 3.75 us).
  Cause: the view sets `FI_CXI_RDZV_EAGER_SIZE=0`, `FI_CXI_RDZV_GET_MIN=0`, `FI_CXI_RDZV_THRESHOLD=0` (alps-extended-images NCCL settings; also in v2.9.1), so MPI messages of 256 bytes and more use the rendezvous protocol.
  Unsetting the three variables in a copy of the job gives 4.4 us at 256 bytes instead of 17 us on the same nodes (job 5444930, `reframe/osu-check/`).
  That pair of nodes was in two dragonfly groups (`nid005617` in group19, `nid006348` in group26), which is why 4.4 us is still above the 3.68 us limit of the test: see "Node placement" below.
  Decision (2026-11-24): keep `FI_CXI_RDZV_*=0` in the view. The OSU uenv tests are changed to use a second set of references when the environment turns the eager protocol off (cscs-reframe-tests branch `osu-uenv-eager-references`, commit 326e8758, not pushed).
  Only `FI_CXI_RDZV_THRESHOLD=0` and `FI_CXI_RDZV_GET_MIN=0` together turn it off for 256 byte messages; each variable alone, and `FI_CXI_RDZV_EAGER_SIZE=0`, have no effect at that size (jobs 5446410-5446418 and 5446437, `reframe/eager-ref/`).
  Same-group pairs with the view: `osu_latency` 8.9-10.9 us (host) and 9.6-11.6 us (GPU), `osu_bw` 268-303 MB/s (host) and 226-251 MB/s (GPU) at 256 bytes; with the variables unset 2.7-3.2 us, 3.5-3.9 us, 527-625 MB/s and 384-457 MB/s.
  With the change, the four OSU uenv tests pass for this image and for `prgenv-gnu/25.11:v1` (`reframe/run-osu-rdzv/`, run with `-J switches=1`).
- Node placement: the latency between two nodes depends on the dragonfly group of each. Slurm's topology on daint has one "switch" per group (`scontrol show topology`, `group16`-`group27`, about 110 nodes each).
  `osu_latency` with the eager protocol on, twelve 2-node jobs (5446022-5446033, `reframe/switches/`): 1.9 us or 2.2 us at 8 bytes and 2.7 us or 3.0 us at 256 bytes inside one group, 3.35 us and 4.2 us across two groups.
  `--switches=1` kept all six jobs that used it in one group; one of six jobs without it spanned two groups.
  Decision (2026-11-24): `--switches=1` is not added to the tests. A 2-node latency test can therefore fail when its nodes are in two groups: check the node list of a failing run before blaming the image.
  Measured on 4 nodes, 2 interleaved repetitions (job 5445432, `$SCRATCH/torch-uenv/reframe/rdzv-eval/`), all three 0 (view) against all three unset:
  MPI host and GPU latency for 256 B to 16 KiB is 14 us against 4.2-5.5 us, and `osu_bw D D` at 4-16 KiB is 2.3x lower; from 32 KiB there is no difference.
  NCCL all-reduce on 16 GPUs is 37% slower up to 64 KiB (0.55 against 0.88 GB/s at 16 KiB), 15% faster at 256 KiB-1 MiB, 18% faster at 16 MiB (25.6 against 21.6 GB/s) and 13% faster at 64 MiB (86 against 76 GB/s); from 256 MiB, NCCL send-receive from 64 KiB, and the 1 GiB torch.distributed all-reduce are the same.
  Only `FI_CXI_RDZV_EAGER_SIZE=0` (the other two unset) restores the small messages and keeps the 64 MiB gain, but not the 16 MiB one, and is the slowest at 1 MiB (3.8 against 4.7 GB/s).
  The settings are also the CSCS workaround for NCCL hangs and watchdog timeouts (docs.cscs.ch NCCL known issues), which this benchmark cannot evaluate.
- build_osu_benchmarks (CUDA build) fails to compile: OSU 7.2 calls `cudaMemPrefetchAsync` with the CUDA 12 signature. The four OSU CUDA tests that use it are skipped. A fault of the test with CUDA 13.
  Fix (2026-11-24, cscs-reframe-tests branch `osu-bump-version`, not committed): the test downloads OSU 7.5.2, the version in the image, and passes the message size as `-m <size>:<size>`, because the 7.5.2 executables crash with a segmentation fault when `-m` has a single value.
  With it, the CUDA build compiles and all eight tests of `osu_tests.py` pass for this image and for `prgenv-gnu/25.11:v1` (21 of 21 test cases, `reframe/run-osu-752b/`).
- CXIGPU2GPULoopbackBW: 175.1 Gb/s vs 183.3 Gb/s minimum on nid006022. A test of the node (`cxi_gpu_loopback_bw`) that does not use the image.
- PyTorchMegatronLM_UENV llama3-8b (16 nodes) and llama3-70b (32 nodes) fail as shipped, for three reasons in the test and in the Megatron fork, not in the image:
    - the test pins Megatron `de14c22` (2025-03), which stops with `ValueError: apply_rope_fusion is not available` with the Transformer Engine of the image;
    - a newer commit (`c3d83c5a0`, the one used in the Megatron section above) needs `--eval-interval`, which the test does not pass (`TypeError` in `get_train_valid_test_num_samples`);
    - the fork deadlocks with TP > 1 (`assistant_mask` broadcast, see the Megatron section), which stops llama3-70b (TP 4, PP 8) with `ncclInternalError` and a watchdog timeout. Fork `main` (`04edde000`) still has the fault.
- llama3-8b (TP 1, sequence length 8192) fills the GPU: 87 GiB of 95 GiB with the old Megatron on `pytorch/v2.9.1`, about 6 GiB more with `c3d83c5a0` (CUDA out of memory on v2.9.1), and with this image 97 GiB plus 876 GiB of host memory with the 32 data workers per rank of the test, so the kernel kills the job.
  An earlier note here that two ranks shared a GPU was wrong: there is one process per GPU.
- Draft fix (2026-11-25, cscs-reframe-tests branch `pytorch-uenv-megatron-update`, not committed): Megatron `c3d83c5a0`, `--eval-interval`, a `sed` that applies the TP fix, 8 data workers per rank and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
  Results at the size of the test (`reframe/run-v8/`, `reframe/run-v291-megatron/`; reference in brackets, the test accepts 10% less):

    | test | image | tokens/s/GPU | TFLOP/s/GPU | result |
    |------|-------|--------------|-------------|--------|
    | llama3-70b | this image | 890 (870) | 400 (420) | pass |
    | llama3-70b | pytorch/v2.9.1:v2 | 885 (870) | 398 (420) | pass |
    | llama3-8b | this image | 7451 (7600) | 384 (440) | fail on TFLOP |
    | llama3-8b | pytorch/v2.9.1:v2 | 7428 (7600) | 383 (440) | fail on TFLOP |

  The two images give the same figures, so the llama3-8b failure is not a property of this image.
  The newer Megatron reports fewer TFLOP for the same tokens per second (old Megatron on v2.9.1: 7762 tokens/s and 450 TFLOP; new: 7772 tokens/s and 401 TFLOP in a run by hand), so the 440 TFLOP reference of llama3-8b is no longer correct for it.
  Not resolved: the llama3-8b runs under ReFrame were 4% slower than the run by hand (7451 against 7772 tokens/s), and it is not known which of the two memory settings is necessary.
- nid005669: a 32-node llama3-70b run that included this node stopped on GPU 0 of the node with `CUDA error: an illegal memory access`, with both images (2026-11-24 17:40); without the node both pass. See the node history in `reframe/node-check/`. The runs above exclude the node.
