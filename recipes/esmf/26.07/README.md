# esmf uenv — build notes

Recipe format **v3** (Stackinator 7), Spack `releases/v1.2` + spack-packages
`releases/v2026.06`, **system gcc-14** (external, from cluster config). Two
environments/views: `esmf` (MPI, cray-mpich@8.1.32) and `esmf-serial` (no MPI).

## The openssl / srun breakage (why views use `link: roots`)

Symptom on the new pilatus/eiger OS image:

```
uenv run esmf/26.2:v1@eiger --view=esmf -- srun --version
srun: error: dlopen(/usr/lib64/slurm/cli_filter_SitePolicies.so):
  /usr/lib64/libcrypto.so.3: version `OPENSSL_3.3.0' not found
  (required by /user-environment/.../openssl-3.6.0/lib64/libssl.so.3)
```

Root cause: the old recipe used `link: run` on the views, which pulls **every**
run dependency of the roots into the view — including `openssl` (a transitive
dep of curl/python/subversion). Combined with `prefix_paths: LD_LIBRARY_PATH:
[lib, lib64]`, the uenv's `libssl.so.3` (3.6.0) leaked onto a **global**
`LD_LIBRARY_PATH`. When the **system** `srun` dlopen'd a **system** Slurm plugin,
the loader bound the uenv's libssl 3.6.0 but the plugin dragged in the **system**
libcrypto.so.3 (older) → `OPENSSL_3.3.0` symbol mismatch → dlopen fails.

Fix: views use **`link: roots`** so only explicitly-requested specs land in the
view / on `LD_LIBRARY_PATH`. openssl, curl, etc. stay in the store, reached only
via RPATH by the binaries that actually need them. Verified: no
`libssl`/`libcrypto`/`libcurl` in either view, and `srun --version` works.

## Packages that MUST be explicit roots because of `link: roots`

`link: roots` only links the listed specs into the view. Files resolved by
**path/@INC** (not RPATH) are therefore missing unless the providing package is
itself a root. Found while building CESM `cesm3_0_beta07`:

- **`perl-xml-sax-base`** — provides `XML::SAX::Exception`, `XML::SAX::Base`.
- **`perl-xml-namespacesupport`** — provides `XML::NamespaceSupport`.

Both are run deps of `perl-xml-sax` (a root), but Perl finds modules via `@INC`
(the view path), not RPATH — so CESM's CLM `build-namelist` (which loads
`XML::LibXML` → `XML::SAX`) failed with `Can't locate XML/SAX/Exception.pm`
until these were added as roots. Anything similar (perl/python modules, data
files under `share/`) that a tool loads by path must be an explicit root.

Libraries (netcdf, hdf5, esmf, parallelio, pnetcdf, openblas, fftw, gsl,
cray-mpich, libfabric) work fine as roots + RPATH and needed no extra additions.

## Validation performed (pilatus)

- `srun --version` → `slurm 25.05.4` in both views (reproducer fixed).
- Full CESM build: clone `cesm3_0_beta07`, `git-fleximod update`,
  `create_newcase --machine eiger --compset FHIST --res f09_g17 --compiler gnu`,
  `case.setup`, `case.build` → **MODEL BUILD HAS FINISHED SUCCESSFULLY**
  (`cesm.exe` links cleanly; its libssl/libcrypto resolve to the consistent
  system pair, no uenv leak).

## Machine files (`extra/<view>/machines/eiger/`)

`config_machines.xml` `mpirun` args hardcode the uenv tag — bumped to
`--uenv=esmf/26.07:v1` for this release. Update on each version bump.
