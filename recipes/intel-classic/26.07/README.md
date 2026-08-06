# intel-classic — build notes

A one-off uenv for a legacy user needing a mixed Intel toolchain:

- **C / C++** = Intel **oneAPI** `icx` / `icpx` (2023.2.4)
- **Fortran** = Intel **classic** `ifort` (2021.10.0)
- `cray-mpich@8.1.32` wrappers: `mpicc→icx`, `mpicxx→icpx`, `mpif90/mpifort→ifort`
- hdf5, netcdf-{c,cxx,fortran}, osu-micro-benchmarks, system libfabric

Single view `intel` (default), mounted at `/user-environment`.

## How the mixed toolchain is expressed

`compilers.yaml` declares only `intel-classic` (spack pkg
`intel-oneapi-compilers-classic`). Stackinator's `intel-classic` compiler group
*also* builds `intel-oneapi-compilers` (the icx/icpx/ifx provider) as an internal
dependency, so both toolchains are in the store, but only the classic one is
"named".

`environments.yaml` carries a **hand-written `prefer:`** that pins the per-language
compiler for every built package:

```yaml
prefer:
- '%[when=%c] c=oneapi %[when=%cxx] cxx=oneapi %[when=%fortran] fortran=intel'
```

plus the MPI spec `cray-mpich@8.1.32 %c,cxx=oneapi %fortran=intel`.

## Two recipe-level fixes so the view exposes the right compilers

Out of the box the `intel` view only exposed the **classic** bins and the
`CC/CXX/FC` env vars dangled. Two fixes in the recipe:

1. **`post-install` hook** — symlinks the oneAPI `icx`/`icpx`/`ifx` from the
   `intel-oneapi-compilers` install into `<view>/bin`. Stackinator's
   `add_compilers` step only links the compilers *named* in the environment's
   `compiler:` list (i.e. classic + gcc), so the oneAPI bins are otherwise
   missing from the view. The hook globs the store for the (single)
   `intel-oneapi-compilers-*` prefix and is idempotent (`ln -sf`) — important
   because stackinator can run the hook more than once.

2. **`env_vars.set` in the `intel` view** — spack auto-sets `CC/CXX/FC` (from the
   oneAPI compiler package's `setup_run_environment`) to paths under
   `env/oneapi/compiler/2023.2.4/...`, a subtree that `link: roots` never
   projects into the view, so they dangle. We override them to the `<view>/bin`
   symlinks and point **Fortran at classic `ifort`** (spack would default `FC` to
   `ifx`). Uses the `$@view_path@` substitution.

### Why NOT add `intel-oneapi` as a second compiler group

The obvious approach — adding `intel-oneapi` to `compilers.yaml` and the env
`compiler:` list so the view step links icx/icpx automatically — was tried and
**rejected**. It makes `prgenv` `needs:` both compiler groups and produced a
*second, parallel concretization* of the whole MPI stack (a duplicate
`cray-mpich`, `hdf5`, `netcdf-*`, `osu-*`). The two copies then collide on module
file names (`==> Error: Name clashes detected in module files`) and the build
fails at the `modules-done` step. The post-install-hook approach leaves the
known-good single-stack concretization untouched.

## Gotcha: orphaned installs after re-concretization

`spack.commit`/`packages.commit` in `config.yaml` are **branches**
(`releases/v1.2`, `releases/v2026.06`). Re-running `stack-config` re-fetches them,
which can shift concretization to new hashes while the old installs remain in the
store DB — again triggering a module-name clash. If you hit this after an
iteration, uninstall the orphans (installs whose hash is absent from
`env/spack.lock`) before the modules step, e.g. inside `stack-debug.sh`:

```
spack uninstall --force --yes-to-all /<hash> ...
```

or do a clean-store rebuild.

## Verified (2026-08-06)

All exercised inside `uenv run store.squashfs`:

- `which` + `--version`: icx/icpx 2023.2.4, ifort 2021.10.0, ifx 2023.2.4, icc/icpc classic — all in view.
- `CC=icx`, `CXX=icpx`, `FC=F77=ifort` — all resolve (no dangling).
- `mpicc -show`→icx, `mpicxx -show`→icpx, `mpif90 -show`→ifort.
- Compile **and run**: C (icx), C++ (icpx), Fortran (ifort).
- 2-rank MPI (`srun -n2`): C and Fortran both print ranks.
- hdf5 1.14.6 `h5cc` compile+run; netcdf-c 4.10.0 / netcdf-fortran 4.6.2 (`nc-config --cc`→icx).
