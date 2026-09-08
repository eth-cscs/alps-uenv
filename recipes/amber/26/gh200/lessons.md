# Amber26 uenv — Lessons Learned

Key technical findings: env vars, version compatibility, Spack package fixes, system quirks.

## Version compatibility
- **CUDA 12.8** is the most recent CUDA supported by Amber26.
- **GCC 12.5** — most recent non-deprecated GCC compatible with CUDA 12.8 in Spack
  (gcc 13.x compatible with cuda 12.8 only up to 13.2, and 13.2 is deprecated → forced to gcc 12.5).
- **Python 3.12** — most recent Python compatible with all Amber python packages
  (py-mpi4py newer than vendored 3.1.4 needed for py3.12).

## Environment / build quirks
- `-DCMAKE_Fortran_FLAGS="-fPIC"` required: works around COMMON block size issue on Grace-Hopper.
- `freesasa` python package not in Spack → installed via `pip` in `post-install`.
- **`f90nml` python package** — `AmberTools/src/PyPE_RESP/setup.py` line 92 hard-codes
  `pip install f90nml` at *build* time. The uenv view is READ-ONLY at user build time, so this
  aborts PyPE_RESP install with `OSError [Errno 30] Read-only file system`. `py-f90nml` is NOT in
  Spack → must be pip-installed into the view in `post-install` (same pattern as freesasa).
  Symptom in build log: `Could not install packages due to an OSError ... Read-only file system:
  '/user-environment/.../site-packages/f90nml'`. Non-fatal to overall `make` (exit 0) but silently
  drops the PyPE_RESP tool.
- Amber's python-package presence check (`cmake/PythonBuildConfig.cmake`) needs:
  numpy scipy matplotlib setuptools pandas numba gemmi Bio(=biopython) rich freesasa
  sklearn(=scikit-learn) sympy pydantic psutil networkx — all satisfied by the recipe.
  Optional extras Amber's conda list also wants (NOT hard-required, currently omitted):
  mrcfile, pdb2pqr, rdkit.
- Amber CMake sets CC/CXX/FC to clang (nonexistent) — `post-install` rewrites them to gcc in `meta/env.json`.
- Amber vendors boost and (with MPI) fftw, building its own copies — awkward to override; currently let it.
- `-DDOWNLOAD_MINICONDA=false` essential: conda env has ~115k inodes, murders distributed FS.
- `-DBUILD_QUICK=off` speeds up AmberTools build dramatically (Quick GPU build takes hours).

## System quirks (daint gh200)
- Build must not be under /tmp, $HOME, / (bwrap bind restriction) → use /dev/shm.
- cuda_arch=90a for GH200.
- GPU MPI runs must be launched with `srun` (cray-mpich). Peer-to-Peer between GH200
  GPUs is ENABLED — multi-GPU `pmemd.cuda.MPI` works across GPUs on one node.
- `pmemd.cuda.MPI` requires **≥32× more atoms than MPI ranks** (`ERROR: Must have 32x
  more atoms than processors!`). Tiny GB test systems (e.g. gb_ala3, 42 atoms) abort with
  2 ranks — not a build fault. Use a realistically sized system (JAC/DHFR ~23k atoms) for
  multi-rank GPU validation.
- Harmless at runtime: `Note: floating-point exceptions ... IEEE_UNDERFLOW_FLAG` /
  `IEEE_INVALID_FLAG` printed by pmemd — expected, not an error.

## Validation results (existing rc image, pre-f90nml-fix)
- CPU-only AmberTools build: SUCCESS. cpptraj/sander/tleap run.
- MPI+CUDA AmberTools + pmemd build: SUCCESS. Built pmemd, pmemd.cuda[_SPFP/_DPFP],
  pmemd.cuda.MPI, pmemd.MPI, sander[.MPI], gem.pmemd.
- pmemd.cuda serial GB run on GH200: SUCCESS ("NVIDIA GPU IN USE", GH200 detected).
- pmemd.cuda.MPI 2-GPU JAC run: SUCCESS (Peer-to-Peer ENABLED, 50 steps, T≈296K).

## Open questions / to verify
- (to be filled in during reproduction build)
