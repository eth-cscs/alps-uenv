# Amber26 build environment — recipe build notes

Build-log notes for the `amber/26` uenv. This uenv provides the toolchain + libraries to
**build** Amber26 (AmberTools + PMEMD); it deliberately does **not** contain Amber itself
(licensing — CSCS may not redistribute Amber).
User-facing instructions live in docs.cscs.ch/software.
See also `lessons.md` (technical findings) and `../progress.md` (work log).

## Target
- System: **daint** (Alps), **gh200** nodes (GH200, `cuda_arch=90a`).
- Cluster config: `alps-cluster-config/daint/`.

## Version pins (and why)
- **cuda@12.8** — newest CUDA supported by Amber26.
- **gcc 12.5** (`compilers.yaml`) — newest non-deprecated GCC compatible with CUDA 12.8 in
  Spack (gcc 13 is only cuda-12.8-compatible up to 13.2, which is deprecated).
- **python@3.12 +tkinter** — newest Python compatible with all Amber python packages;
  `+tkinter` is required by Amber and is NOT the default in the prgenv uenv.
- **cray-mpich@8.1.32 +cuda** — CUDA-aware MPI from the system network config.

## Views
- Single view `amber` with `link: run` so ALL python runtime deps appear in the view
  (Amber's build imports them). `add_compilers: true` and `LD_LIBRARY_PATH` prefixed with
  lib/lib64.

## post-install (IMPORTANT — custom step)
`post-install` pip-installs two python packages into the view that are **not in Spack**:
- **freesasa** — required python package, not packaged in Spack.
- **f90nml** — `AmberTools/src/PyPE_RESP/setup.py` runs `pip install f90nml` unconditionally
  at *user* build time. The view is READ-ONLY then, so without this the install aborts with
  `OSError [Errno 30] Read-only file system`, silently dropping the PyPE_RESP tool. Installing
  it here (view is writable during the uenv build) makes that pip call a no-op.

The post-install also rewrites `CC`/`CXX`/`FC` in `meta/env.json` to the view's gcc/g++/
gfortran — Spack was setting them to nonexistent clang wrappers, which broke Amber's
`-DCOMPILER=GNU` detection.

> Note: freesasa/f90nml are installed with `pip` (not a build-cache-backed Spack package),
> so they are re-fetched from PyPI each build. If PyPI is unreachable, add them to the
> source cache or vendor wheels.

## Python packages Amber checks for (all present as Spack specs)
`cmake/PythonBuildConfig.cmake` requires: numpy scipy matplotlib setuptools pandas numba
gemmi biopython(Bio) rich freesasa scikit-learn(sklearn) sympy pydantic psutil networkx —
plus mpi4py. All are in `environments.yaml`. Optional extras Amber's conda list also names
but does NOT hard-require (currently omitted, add if a user needs them): mrcfile, pdb2pqr,
rdkit, fastapi (web GUI only).

## Things deliberately NOT done
- boost is NOT provided as a spec — Amber was too awkward about using an external boost, so
  it builds its own vendored copy. Same for fftw when building Amber with MPI.

## Build / test procedure
```
stack-config -r ./recipe -s ./alps-cluster-config/daint/ -b /dev/shm/$USER/build --mirror=mirrors.yaml
cd /dev/shm/$USER/build
env --ignore-environment PATH=/usr/bin:/bin:`pwd -P`/spack/bin HOME=$HOME make store.squashfs NJOBS=64
```
Only `post-install` changes rebuild fast (all Spack packages restore from the build cache).

Validated end-to-end (see lessons.md): CPU-only and MPI+CUDA AmberTools+pmemd builds succeed;
`pmemd.cuda` runs on GH200; `pmemd.cuda.MPI` runs across 2 GH200 GPUs (peer-to-peer enabled).
