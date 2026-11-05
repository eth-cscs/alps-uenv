# linaro-forge 26.0.3 (MCH) — build notes

Built on linard (zen3) against `alps-cluster-config/linard`, store `/user-tools`.

- Forge is a pre-compiled binary tarball, so this one image works on both linard partitions (a100 and zen3).
  It only targets zen3 in `config.yaml`. The CSCS systems use `../cscs`.
- The custom package lives in `../../repo/packages/linaro_forge`. It is reached through the chained `repo` symlinks.
  - The `license=cscs|mch` variant copies `license.<site>` from the package directory to `$prefix/licences/License`.
    Forge reads the British spelling, `licences`.
  - The copy is idempotent, so it survives the build-cache reinstall.
  - `license.mch` is a copy of `/apps/ddt/23.1.2/licences/Licence` (serial 17770, features `ddt,cuda`).
- Version 26.0.3 sha256 values were computed from downloads.linaroforge.com:
  - aarch64: `b76137ec…f47d`
  - x86_64: `a141a0ac…a0a3`
- Verified:
  - `ddt --version` reports 26.0.3.
  - The installed `licences/License` is identical to `license.mch`.
- No concretization or runtime workarounds were needed.
