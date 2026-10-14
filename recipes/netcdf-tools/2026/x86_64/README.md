# netcdf-tools uenv

Utilities for climate/weather analysis and file manipulation (netcdf-c/cxx4/fortran,
hdf5, cdo, nco, ncview, eccodes, gdal, geos, ferret, ncl, python, ...).

- **Recipe version:** 3
- **Toolchain:** stackinator v7 (main / 7.0.0-dev), spack `releases/v1.2`,
  spack-packages `releases/v2026.06`
- **Compiler:** system gcc @12.3.0
- **Target built/tested on:** eiger (linux-sles15-zen2, x86_64)

Build:

```
stack-config -r ./recipe -s ./alps-cluster-config/eiger/ -b /dev/shm/$USER/build --mirror=mirrors.yaml
cd /dev/shm/$USER/build
env --ignore-environment PATH=/usr/bin:/bin:`pwd -P`/spack/bin HOME=$HOME make store.squashfs NJOBS=32
```

The recipe has no `default-view`, so test with an explicit view:
`uenv run store.squashfs --view=netcdf -- <cmd>`.

## Custom packages (`repo/`)

### `ferret` — build on both aarch64 and x86_64
Copy of the upstream `ferret` package. On top of the upstream version it:
- adds a `libxmu` dependency and extra `-Wno-implicit-*` warning-suppression
  flags needed by modern gcc (already present in recipe v1);
- (commit "ferret: fix build on aarch64") strips the x86-only `-m64` flag from
  the build-config files and only links `-lquadmath` on `target=x86_64:`. Both
  guards are **no-ops on x86_64**, so on eiger ferret builds/runs unchanged from
  upstream. Ferret was verified to build from source (~3m) and run (`ferret`
  starts, banner "FERRET v7.6", executes commands).

### `ncl` — build without ESMF, and link fix
Copy of the upstream `ncl` package (6.6.2) with two changes:

1. **ESMF made optional and off by default.** Upstream has an unconditional
   `depends_on("esmf+netcdf", type="run")`. ESMF is only needed for the
   `ESMF_regridding.ncl` helper functions, which CSCS does not use, and it is
   heavy/fragile to build. Replaced with a new `esmf` variant (default
   `False`): `depends_on("esmf+netcdf", type="run", when="+esmf")`. The
   `ESMFBINDIR` export in `setup_run_environment` is now guarded by
   `+esmf` so NCL runs fine with ESMF absent (only ESMF_regrid_* is unavailable).

2. **`netcdf-c+logging`.** NCL's NetCDF interface (`NclNetCdf.c`,
   `NclNetCDF4.c`, `NclNewHDF5.c`) calls `nc_set_log_level()`, which netcdf-c
   only exports when built `+logging` (default off). Without it the `ncl`
   binary fails to link: `undefined reference to nc_set_log_level`. The package
   now `depends_on("netcdf-c+logging")`. Because the environment uses
   `unify: true`, this makes the whole stack use one `netcdf-c +logging` build
   (harmless for the other tools).

## Gotchas

- **Changing a shared variant (e.g. netcdf-c `+logging`) needs a clean build
  dir.** Rebuilding into an existing `-b` build directory left the old
  `netcdf-c ~logging` (and its rebuilt dependents) in the store alongside the
  new `+logging` set. Module generation runs over the whole store DB, and with
  `hash_length: 0` / `projections {name}/{version}` both variants map to the
  same module file → `Error: Name clashes detected in module files` at the
  `modules-done` step. Fix: `rm -rf` the build directory and rebuild fresh
  (buildcache makes this fast). The packages themselves build fine; only module
  generation trips.
