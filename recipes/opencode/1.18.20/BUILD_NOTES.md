# Maintainer and build notes

User-facing launch and CSCS inference instructions are in [README.md](README.md). This file records implementation constraints and build findings that should survive recipe updates.

## Recipe composition

- Spack is pinned to `v1.2.2`; `spack-packages` is pinned to commit `7318c6ac1a452a5e9f433d6de81841a036114e8f` from 2026-08-21.
- The environment uses GCC 14, `unify: true`, a root-linked `opencode` view, and `add_compilers: false`.
- Runtime roots are `cscs-agent-model-config`, `cscs-agent-launchers@2026.08.27`, ShellCheck, jq, yq 4, and `squashfs`.
- Keep `cleanup: runtime` and keep `squashfs` explicit. Stackinator's implicit `squashfs` group is not an explicit environment root and is otherwise eligible for garbage collection before image creation.

## Custom packages

### `cscs-agent-launchers`

Installs `opencode-bwrap` and `omp-bwrap` from one `agent-bwrap.in` template. Argument parsing, XDG isolation, bind policy, SSH-agent validation, skill setup, managed-config refresh, mutable-tool bootstrap, and bubblewrap assembly must remain shared. Harness-specific initialization is selected from the invoked launcher name.

`content_hash()` includes the launcher template and packaged defaults. Installation rejects unresolved substitution tokens.

### `cscs-agent-model-config`

Installs static OpenCode/OMP CSCS defaults, `cscs_models.py`, and the `cscs-agent-model-config` launcher. It has no Spack Python dependency. The launcher executes the generator through uv with `UV_PYTHON_PREFERENCE=only-managed`; its template and all defaults participate in `content_hash()`.

The generator performs metadata GETs only: CSCS model catalogue, prices, documentation, and public Hugging Face model metadata. It never submits inference work and never writes API-key values.

### `oh-my-pi`

Packages upstream OMP 18.0.5 release binaries for ARM64 and x86-64. Spack requires a main non-expanded source, so the release `LICENSE` is the root source and the architecture-specific executable is a conditional resource.

Installation replaces literal ED3 terminal scrollback clears (`ESC[3J`) with harmless SGR resets. `content_hash()` must continue to invalidate same-version installs when this binary mutation changes.

### `opencode`

Builds OpenCode 1.18.20 from source with Bun and Node.js. The installed binary is standalone; Bun and Node are build dependencies. Runtime auto-update is disabled.

### `opencode-cscs-skills`

Packages the CSCS agent skills and adds the `refresh-cscs-models` skill. Launchers install relative links into launcher-owned skill directories and leave user-owned directories untouched.

## Launcher invariants

- Keep `--ro-bind / /` before `--proc /proc`. Reversing them exposes host `/proc` inside the private PID namespace and breaks CUDA initialization.
- The project and launcher XDG roots are writable; the remaining host filesystem is read-only. `/users`, `/home`, `/root`, and sandbox `/tmp` are hidden except for explicit bind paths.
- PID and IPC namespaces are private by default. Network and `/dev` are inherited; SSH agent access is opt-in and validates socket type, ownership, permissions, and symlinks.
- OpenCode and OMP retain separate XDG roots. Packaged skills use harness-specific ownership markers so existing managed directories continue to update.
- OMP interactive launches use `script` and Perl to remove dynamically generated ED3 sequences. The filter is disabled with `OMP_BWRAP_FILTER_ED3=0` and is skipped when either host command is unavailable.

## CSCS managed configuration

- Static defaults are seeded only when no user alternative exists. Managed files have SHA-256 ownership sidecars.
- A launch refresh requires a CSCS key, an unchanged managed file, an executable generator, and either no refresh stamp or one at least 86,400 seconds old.
- A successful refresh replaces the file, records its new hash, and updates the stamp. Failure preserves the file and old stamp, causing a retry on the next launch.
- OpenCode management applies to `opencode.json` even when `opencode.jsonc` exists because OpenCode merges both. Generated config references `{env:CSCS_INFERENCE_API_KEY}`.
- OMP does not manage `models.yml` when `models.yaml` exists. OMP 18 cost blocks must contain `input`, `output`, `cacheRead`, and `cacheWrite`; the generator emits all four when pricing is available.
- OMP launcher defaults enable quiet startup, disable update/changelog prompts, preserve resize scrollback, and select Kimi K2.7 Code, Apertus 8B, and GLM-5.2 for the default, smol, and slow roles.
- Refresh errors are intentionally quiet unless `CSCS_MODEL_REFRESH_VERBOSE=1` is set.

## Mutable uv and Python

- Astral's versioned installer places uv under the shared XDG data root. It runs quietly and noninteractively with `UV_INSTALL_DIR`, `UV_NO_MODIFY_PATH=1`, and the target bin directory temporarily first on `PATH`.
- Managed CPython is stored under `python/`; its unversioned links are stored under private `python-bin/`, which is not retained on `PATH`.
- `uv python install --default` explicitly enables the `python-install-default` preview feature and temporarily prepends `python-bin` to suppress both uv bootstrap warnings.
- `.managed-python-version` plus prefix validation avoids repeated install checks. The launcher rejects private links that resolve outside `UV_PYTHON_INSTALL_DIR`.
- The persistent `PATH` order is packaged harness, packaged ripgrep, mutable uv/tool bin, then inherited paths. Since the mutable tool bin has no Python links, an active secondary-uenv view supplies project Python.
- User-facing uv uses `UV_PYTHON_PREFERENCE=system`, meaning it prefers compatible interpreters inherited on `PATH`. The model generator overrides this with `only-managed`.
- Mounting another uenv without activating its view does not expose its Python on `PATH`. Multi-uenv validation used the PyTorch `default` view: Python 3.12.12, PyTorch 2.9.1, and CUDA availability all passed while the private infrastructure interpreter remained CPython 3.13.15.

## Build history and workarounds

- The earlier split-launcher recipe built as `agents-bwrap/v26.08` on Daint GH200. The consolidated launcher recipe subsequently built successfully and was exercised through the published uenv.
- During the consolidated build, `ftp.gnu.org` was unreachable for the URL patches of `bash@5.3`, while `mirror.spack.io` lacked the objects. Downloading all nine patches from `https://ftpmirror.gnu.org/bash/bash-5.3-patches/`, verifying the package checksums, and placing them in the configured content-addressed Spack source cache allowed the unmodified Bash package to build.
- `cleanup: runtime` initially removed Stackinator's implicit GCC and `squashfs` groups. Missing GCC produced an empty compiler configuration but was nonfatal; missing `squashfs` made image creation resolve `/bin/mksquashfs`. Making `squashfs` an explicit recipe root is the per-recipe keep exception. Revisit this if Stackinator begins protecting its internal packaging tools.
- Validation performed during development includes Bash syntax checks, Python source compilation, JSON/YAML parsing, substitution-token/content-hash checks, fake-bubblewrap launcher exercises, managed-config ownership tests, first/cached uv bootstrap tests, and live multi-uenv Python/PyTorch selection.
