# netcdf-tools uenv (santis / aarch64 / GH200)

Lightweight uenv of climate/weather pre- and post-processing tools, built for
Grace-Hopper (`neoverse_v2`) nodes on santis. **No CUDA**: despite running on a
GPU system, this is a host-only file-manipulation/analysis environment.

## Build

```
stack-config -r ./recipe -s ./alps-cluster-config/santis/ -b /dev/shm/$USER/build --mirror=mirrors.yaml
cd /dev/shm/$USER/build
env --ignore-environment PATH=/usr/bin:/bin:`pwd -P`/spack/bin HOME=$HOME make store.squashfs NJOBS=32
```

## Key decisions / gotchas

### CUDA-free network stack (task 1)
The shared cluster config (`alps-cluster-config/santis/network.yaml` →
`site/network/gh200`) only provides **+cuda** externals for the Slingshot/CXI
stack, so `libfabric` (and the `buildable:false` `libcxi` external) dragged CUDA
into every MPI-linked package.

Fix — override both externals as `~cuda` in `packages.yaml`, pointing at the same
system prefixes (the CXI libs still work for host / non-GPU-aware MPI):
- `libfabric@1.22.0 fabrics=cxi,rxm,tcp,rxd,udp,shm ~cuda ~gdrcopy` @ `/opt/cray/libfabric/1.22.0`
- `libcxi@12.0.2 ~cuda` @ `/usr`

`environments.yaml` also pins `mpi: cray-mpich@8.1.32 ~cuda~rocm` and network
`specs: [libfabric~cuda~gdrcopy]`, plus a global `~cuda` variant. Result: 0 cuda
packages in the concretization (verify with a JSON scan of `env/spack.lock`).

### View completeness — `link: run`
The `netcdf` view uses `link: run` (not the default `roots`) so transitive
**runtime** deps land in the view. Needed for python: `py-eccodes` needs numpy,
cffi, findlibs co-located in the view's site-packages or `import eccodes` fails.
`LD_LIBRARY_PATH` is prefixed with `lib`, `lib64`.

### Custom package: `repo/packages/ferret`
Ferret is not in the upstream package set at the pinned spack-packages commit
(`releases/v2026.06`); a local `package.py` (generic build) was added.

### Custom package: `repo/packages/ncl` (aarch64 build fixes)
ncl 6.6.2 does **not** build out-of-the-box on aarch64 with the upstream
package. We ship a full copy of the upstream package (`package.py` + its patch
files) with two extra fixes in `patch()`:

1. **Bundled GRIB2 lib (`external/g2clib-1.6.0/makefile`) is x86-only.** Its
   `CFLAGS` hard-code `-m64` (rejected by aarch64 gcc: *"unrecognized
   command-line option '-m64'"*) and reference the jasper include dir with no
   `-I` prefix (so gcc treats the path as an input file). `libgrib2c.a` then
   never builds and the final `ncl` link dies with *"cannot find libgrib2c.a"*.
   We add the `-I` and drop `-m64`. (Upstream `for_aarch64.patch` only fixes the
   *generated* ymake config, not this static makefile.)
2. **Stray debug calls.** ncl 6.6.2 left `nc_set_log_level(3);` uncommented in
   three nio backends (`NclNetCdf.c`, `NclNewHDF5.c`, `NclNetCDF4.c`, all under
   `ni/src/ncl/`). `nc_set_log_level` is only exported by `netcdf-c +logging`
   (variant default off), so the final link fails with *"undefined reference to
   nc_set_log_level"*. These are debug leftovers (each sits below an identical
   commented-out copy) — we remove them rather than force a `netcdf-c +logging`
   rebuild of the whole unified stack.

Note the *"detected recursion whilst expanding macro linux"* errors during the
build are **benign** — GCC's traditional preprocessor reports them and
continues (upstream documents this in the package; do not "fix" with `-Ulinux`).

## Packages
`hdf5 +szip +hl`, `netcdf-c/-cxx4/-fortran`, `ncview`, `cdo`,
`eccodes +netcdf +tools +png`, `py-eccodes`, `gdal +netcdf`, `geos`, `nco`,
`python`, `udunits`, `ferret`, `ncl`.

## ncl cost analysis (task 3)
Adding `ncl` (6.6.2) with its full upstream deps (`+esmf`) pulls in **27
packages used by nothing else** in the stack (total concretization 167). With
the default `~esmf` it is **23 ncl-only packages** (total 163). The notable
heavyweights it drags in on its own:
- `esmf` (8.9.1) + `parallelio` — regridding/ESMF backend (run-time only, `+esmf`)
- `cairo`, `pixman`, `glib`, `gobject-introspection`, `freetype`, `fontconfig`
  and an X font toolchain (`libxfont`, `mkfontdir/scale`, `bdftopcf`, …) — graphics
- `jasper`, `tcsh`, `lzo`, `elfutils` (and `libyaml`, `py-pyyaml` only with `+esmf`)

### esmf removal impact (`+esmf` variant, default off)
`esmf` is only used at runtime by `ESMF_regridding.ncl`, which is not needed at
CSCS. The custom package gates it behind a `+esmf` variant defaulting **off**
(upstream hard-codes it as a `type=run` dep), so plain `- ncl` concretizes as
`ncl~esmf`. Removing it drops **4 packages**: `esmf`, `parallelio`, `libyaml`,
`py-pyyaml` (167 → 163 packages).

squashfs size (both built clean from the same buildcache, identical method):

| configuration | packages | squashfs size |
|---|---|---|
| `ncl +esmf` | 167 | 1,348,956,160 B (1.256 GiB) |
| `ncl ~esmf` (default) | 163 | 1,313,931,264 B (1.224 GiB) |
| **saved by dropping esmf** | −4 | **35,024,896 B (≈33 MiB, ~2.6%)** |

So esmf's cost is modest on disk (~33 MiB compressed; `esmf` 114 MB + `parallelio`
3.2 MB uncompressed in-store) but it does add 4 packages and a heavier build.
To re-enable regridding, build `ncl +esmf`.

Verified working (both variants): `ncl -V` → 6.6.2; runs `.ncl` scripts;
`ncl_filedump` reads a NetCDF file (exercises the patched `NclNetCdf.c` path).
With `~esmf`, `ESMFBINDIR` is correctly left unset.
