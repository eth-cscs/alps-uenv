# pytorch/v2.14.1 (a100) — build notes

Build log for the next build of this recipe; not user-facing documentation.

This recipe is a copy of `../gh200` (same package set, versions and build fixes), ported to the A100 nodes of **linard** (AMD EPYC 7713 / zen3, 4x A100-SXM4-80GB per node, all-to-all NVLink, 4 Slingshot NICs `cxi0-3`, driver 595.91.07).
Read `../gh200/README.md` for the history of the shared custom packages (py-torch, triton, flash-attn, TE, nvshmem, magma, arrow, ...), the view environment and the MAGMA open item: everything there applies here unless listed below.
Built with stackinator main (`1c5f39a`), cluster config `alps-cluster-config/linard`, spack v1.2.2, spack-packages `be3466d5`.

## Differences from gh200

### Recipe

- `cuda_arch=80` (gh200: `90a`). Only one CUDA arch is targeted: see "Single CUDA arch" below.
- `py-torch +fbgemm` (gh200: `~fbgemm`, which fails to link on aarch64). Gives the x86 `fbgemm` quantized CPU engine.
  `~mkldnn` is kept: spack's py-torch adds a dependency on `mkl` for `+mkldnn`.
- `NCCL_NET_GDR_C2C` removed from the view (Grace C2C only). All other NCCL/libfabric settings are as on gh200.
- libfabric 2.6.0 and cray-mpich 9.1.0 build against linard's system libcxi (SHS 13.1.0, same version as daint), although the linard cluster config prefers the system libfabric 2.3.1 for MCH workloads.

### Custom packages

- **cudnn, cusparselt, cublasmp**: the NGC 26.07 versions (9.24.0.43, 0.9.1, 0.9.1.3056) only had aarch64 tarballs; added the x86_64 sha256 from NVIDIA's `redistrib_<version>.json` (the aarch64 values in those manifests match the existing ones).
- **py-flash-attn**: `FLASH_ATTN_CUDA_ARCHS` was hardcoded to `90`; now derived from py-torch's `cuda_arch`.
- **py-torchao**: `TORCH_CUDA_ARCH_LIST` was hardcoded to `9.0a`; now derived from `cuda_arch`.
  torchao 0.18's `setup.py` also builds `_C_cutlass_90a` (sm_90a) and `_C_mxfp8` (sm_100) whenever CUDA >= 12.8, regardless of the arch list; `patch()` now builds them only when `cuda_arch` contains `90a` / `100*`.
  torchao 0.18 has no other CUDA kernels (the sm_80 Marlin/FP6 kernels were removed upstream), so on A100 no torchao CUDA extension is built; torchao uses its Python/Triton paths (int8 weight-only quantization tested).
- **py-torch-nvidia-apex**: `group_norm_v2_cuda` hardcodes sm_90/sm_100/compute_120 (39 MB, unusable on A100); `patch()` skips it when no `cuda_arch` is >= 90.
- **cutlass**: `CUTLASS_ENABLE_HEADERS_ONLY=ON`. The default build compiled the CUTLASS kernel library + profiler (965 MB) and installed the unit tests (593 MB). Its only consumer, nvidia-mathdx, needs only the headers and CMake config.
- **dynolog**: `depends_on("rust", type="build")` (was a link dependency). The binaries do not link rust libraries; the link dependency kept rust (1.3 GB) in the image after `cleanup: runtime`.

The last four apply to gh200 as well (cutlass and dynolog give the same savings there).

## Single CUDA arch

All 15 packages with a `cuda_arch` variant are `cuda_arch=80`. `tests/arch_scan.sh` (see Validation) lists every shared object with SASS/PTX for other archs; after the fixes above the remaining exceptions are small and were left alone:

| Library | Non-sm_80 code | Why |
|---|---|---|
| `libtransformer_engine.so` | one sm_90a + one sm_75 cubin, 520 KB (of 194 MB sm_80) | TE hardcodes sm_90a for `gemm/cutlass_grouped_gemm.cu` |
| `libnccl.so` | 1.5 MB sm_100 + 4 MB compute_80 PTX (of 50 MB) | NCCL builds some kernels for sm_100 itself |
| `libmpi_gtl_cuda.so` (cray-gtl) | sm_75 | HPE binary |

Not addressed: `libmagma.so` (120 MB) carries compute_80 PTX alongside the sm_80 SASS (531 MB PTX vs 294 MB SASS uncompressed); dropping it needs a custom magma package (`CMAKE_CUDA_ARCHITECTURES=80-real`), estimated 50-70 MB. faiss similarly.
The NVIDIA binary packages (cuda 7.2 GB, cudnn 2.1 GB, cutensor 1.4 GB, cusparselt 0.6 GB) are fat binaries for all archs and cannot be rebuilt.

## Build

- linard Slurm: request cores with `-c 128` together with `--exclusive`; `--exclusive` alone gives one core.
- The build cache (`/scratch/mch/bcumming/uenv-cache/user-environment`) is shared with the gh200 build only by mount point: the x86_64/zen3 specs are separate, so the first build was from source.
- First build (job 349584, 2026-11-04): 2h09m, image 10.1 GB (21.3 GB unpacked).
- Second build with the cutlass/dynolog/apex/torchao fixes (2026-11-04, 64 cores, warm cache): ~12 min, image 8.9 GB (18.4 GB unpacked); rust is gone and cutlass is 26 MB.
- Stackinator pushes every package to the build cache right after it is installed, except `cuda`, `perl` and `nvhpc` (excluded in its Makefile; they come from the source cache).

## Validation

Test scripts are kept outside the recipe in `/scratch/mch/bcumming/torch-uenv-a100/tests/`:

- `single_node.py`: 16 checks — versions/arch list, bf16 matmul, `torch.compile`, triton JIT kernel, SDPA flash backend fwd/bwd, flash-attn fwd/bwd vs SDPA, TE `Linear`/`LayerNormMLP`/`DotProductAttention` bf16 fwd/bwd, TE fp8 rejected cleanly on sm_80, apex `FusedAdam`/`FusedLayerNorm`, torchao int8 weight-only, torchao has no extension for archs it cannot run, magma `inv`/`eigvals` vs CPU, fbgemm dynamic quantized linear, Parquet + `datasets` round trip (snappy/zstd/brotli/gzip), import of 67 modules.
- `arch_scan.sh`: non-sm_80 CUDA code in the image's shared objects.
- `allreduce.py`: `torchrun --standalone --nproc-per-node=4 allreduce.py`, NCCL all-reduce correctness and bandwidth.

First image (2026-11-04): all 16 checks pass. torch 2.14.1, CUDA 13.3, cuDNN 9.24.0, NCCL 2.30.7, arch list `['sm_80']`, `has_magma=True`, fbgemm engine available.
CUDA 13.3 on the 13.2 driver works for these paths (minor-version compatibility; all kernels are sm_80 SASS, no PTX JIT).
FP8 (TE fp8 autocast, torchao float8) needs sm_89+ and is not available on A100.

Second image (2026-11-04): all 16 checks pass; `arch_scan.sh` shows only the exceptions in the table above.
Single node, 4x A100 over NVLink: `all_reduce_perf -g 4` 227 GB/s bus bandwidth at 2 GiB (avg 183 GB/s over 8 MiB-2 GiB); `torch.distributed` all-reduce, 4 ranks, 512 MiB bf16: correct, 210 GB/s.

Not yet tested: multi-node (aws-ofi-nccl over the 4 CXI NICs, `NCCL_NET_GDR_LEVEL=PHB`, whether linard's Slurm accepts `--network=disable_rdzv_get` / `SLURM_NETWORK`), and a real training workload.
