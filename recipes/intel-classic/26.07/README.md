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

## Recipe-level fixes so the view exposes a working toolchain

Out of the box the `intel` view only exposed the **classic** bins, the
`CC/CXX/FC` env vars dangled, and classic **Fortran linking was broken**. Three
fixes in the recipe:

1. **`post-install` hook, part 1 — oneAPI bins into the view.** Symlinks the
   oneAPI `icx`/`icpx`/`ifx` from the `intel-oneapi-compilers` install into
   `<view>/bin` (i.e. `/user-environment/env/intel/bin`). Stackinator's
   `add_compilers` step only links the compilers *named* in the environment's
   `compiler:` list (i.e. classic + gcc), so the oneAPI bins are otherwise
   missing from the view. The hook globs the store for the (single)
   `intel-oneapi-compilers-*` prefix and is idempotent (`ln -sf`) — important
   because stackinator can run the hook more than once.
   **NB:** the hook's target must be the *default view's* bin. The view is named
   `intel` (see `config.yaml`/`environments.yaml`), so `view_bin` is
   `env/intel/bin`. An earlier revision hard-coded `env/oneapi/bin` (a stale
   view name); that directory is not on `PATH`, so `which icx` failed and
   `CC`/`CXX` dangled even though the symlinks existed.

2. **`env_vars.set` in the `intel` view** — spack auto-sets `CC/CXX/FC` (from the
   oneAPI compiler package's `setup_run_environment`) to paths under
   `env/oneapi/compiler/2023.2.4/...`, a subtree that `link: roots` never
   projects into the view, so they dangle. We override them to the `<view>/bin`
   symlinks and point **Fortran at classic `ifort`** (spack would default `FC` to
   `ifx`). Uses the `$@view_path@` substitution.

3. **`post-install` hook, part 2 — classic Fortran runtime libs on
   `LD_LIBRARY_PATH`.** Classic `ifort` drives GNU `ld` with an LTO plugin
   (`<classic>/lib/icx-lto.so`) that `NEED`s `libimf.so` / `libsvml.so` /
   `libirng.so` / `libintlc.so.5`. Spack baked a `RUNPATH` into that plugin
   pointing at the **`intel-oneapi-compilers`** store prefix
   (`compiler/<ver>/linux/compiler/lib/intel64_lin`) — a *different* package with
   a *different* hash — and that `RUNPATH` is the plugin's **only** resolution
   path (the view does not project the compiler `lib` subtree). So after a
   re-concretization that shifts `intel-oneapi-compilers` to a new hash and
   orphans the old install, the `RUNPATH` dangles and Fortran linking dies with:

   ```
   ld: .../icx-lto.so: error loading plugin: libimf.so: cannot open shared object file
   ```

   The classic compiler ships its *own* copy of these libs under
   `compiler/lib/intel64_lin`. The hook symlinks them into `<view>/lib`, which is
   already on the view's `LD_LIBRARY_PATH` and is searched **before** the plugin's
   `RUNPATH`. Resolution becomes self-contained within the (always-present, named)
   classic compiler and no longer depends on the oneAPI package's hash. Verified
   with `ldd icx-lto.so` → `libimf.so => .../env/intel/lib/libimf.so`.

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
`env/spack.lock`) before the modules step. From inside the sandbox (copy the
`env … bwrap-mutable-root.sh …` line out of `stack-debug.sh` and append
`bash -noprofile -lc "<cmd>"`), the exact reconciliation is:

```sh
keep=$(spack -e $BUILD/env find --format '{/hash}' | sort -u)   # keep set (spack.lock)
allh=$(spack find          --format '{/hash}' | sort -u)         # everything in the store DB
orphans=$(comm -13 <(echo "$keep") <(echo "$allh"))              # installed but not in the env
spack uninstall --force --yes-to-all $orphans
```

Compare hashes *with* their leading `/` on both sides — mismatched stripping
makes `comm` flag the keepers as orphans too. Then re-run `make store.squashfs`
(it re-runs the modules step, the post-install hook, and repackages). Or do a
clean-store rebuild.

## Verified (2026-08-06, after the Fortran-linking fix)

All exercised inside `uenv run store.squashfs`:

- `which`: icx/icpx/ifx **and** icc/icpc/ifort all resolve to `env/intel/bin`.
- `--version`: icx/icpx/ifx 2023.2.4, ifort 2021.10.0, icc/icpc classic.
- `CC=icx`, `CXX=icpx`, `FC=F77=ifort` — all resolve (no dangling).
- Compile **and run** (all 6 drivers): C (icx/icc), C++ (icpx/icpc), Fortran (ifort/ifx).
- **Fortran linking regression fixed:** `ifort hello.F90` and `mpif90 hello.F90`
  both link and run. `ldd .../icx-lto.so` shows `libimf.so` (and svml/irng/intlc)
  resolving from `env/intel/lib/` — the classic package's own libs via
  `LD_LIBRARY_PATH`, not the oneAPI-hashed `RUNPATH`. This is robust across
  re-concretization (previously failed with `error loading plugin: libimf.so`).
- `mpicc` compile+run.

Not re-run this pass (unchanged since prior verification): 2-rank `srun` MPI,
hdf5 `h5cc`, netcdf `nc-config`.
