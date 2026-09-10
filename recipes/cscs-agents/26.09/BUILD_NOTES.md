# Maintainer and build notes

User-facing launch and CSCS inference instructions are in [README.md](README.md). This file records implementation constraints and build findings that should survive recipe updates.

## Recipe composition

- Spack is pinned to `v1.2.2`; `spack-packages` is pinned to commit `7318c6ac1a452a5e9f433d6de81841a036114e8f` from 2026-08-21.
- The `cscs-agents/26.09` recipe uses an `agents` environment and view, GCC 14, `unify: true`, root linking, and `add_compilers: false`.
- Runtime roots are `cscs-agent-model-config`, `cscs-agent-launchers@2026.09.10`, ShellCheck, jq, yq 4, and `squashfs`. Version selection of the packaged harnesses lives in the launcher: `cscs-agent-launchers@2026.09.10` pins `opencode@1.18.30` and `oh-my-pi@18.1.16`, while `@2026.09.01` pins `opencode@1.18.25` and `oh-my-pi@18.0.9`. Bumping a harness therefore means a new launcher version plus the new version blocks in the harness packages; `environments.yaml` selects the launcher version only. Keeping the harnesses out of the environment specs also keeps their bare binaries out of the `link: roots` view.
- Keep `cleanup: runtime` and keep `squashfs` explicit. Stackinator's implicit `squashfs` group is not an explicit environment root and is otherwise eligible for garbage collection before image creation.
- The podman support packages (`crun`, `catatonit`, `fuse-overlayfs`) are explicit environment roots alongside `squashfs` for the same keep-alive reason: the launcher resolves their install paths at package-install time and `--podman` fails loudly when they are missing.

## Custom packages

### `cscs-agent-launchers`

Installs `opencode-bwrap` and `omp-bwrap` from one `agent-bwrap.in` template. Argument parsing, XDG isolation, bind policy, SSH-agent validation, skill setup, managed-config refresh, mutable-tool bootstrap, and bubblewrap assembly must remain shared. Harness-specific initialization is selected from the invoked launcher name. Refresh stamps record production/Forno credential availability, never key values, so adding or removing a gateway key triggers an immediate atomic regeneration.

`content_hash()` includes the launcher template and packaged defaults. Installation rejects unresolved substitution tokens.

### `cscs-agent-model-config`

Installs static OpenCode/OMP production defaults, `cscs_models.py`, and the `cscs-agent-model-config` launcher as version 2026.09.01. It has no Spack Python dependency. The launcher executes the generator through uv with `UV_PYTHON_PREFERENCE=only-managed`; its template and all defaults participate in `content_hash()`.

The generator performs metadata GETs only: production and Forno model catalogues, production prices and documentation, and public Hugging Face model metadata. It never submits inference work and never writes API-key values. Production uses the Anthropic Messages route and `{env:CSCS_INFERENCE_API_KEY}`; Forno uses OpenAI Chat Completions, provider key `cscs-forno`, and `{env:CSCS_INFERENCE_API_KEY_FORNO}`. Forno has no pricing or deployment-context endpoint, so public model metadata wins and unresolved models receive a conservative 32,768-token fallback rather than disappearing from agent configuration.


### `oh-my-pi`

Packages upstream OMP 18.0.9 release binaries for ARM64 and x86-64. Spack requires a main non-expanded source, so the release `LICENSE` is the root source and the architecture-specific executable is a conditional resource.

Installation replaces literal ED3 terminal scrollback clears (`ESC[3J`) with harmless SGR resets. `content_hash()` must continue to invalidate same-version installs when this binary mutation changes.

### `crun`

OCI runtime built with a one-line carried patch (`devpts-gid.patch`): stock crun mounts `/dev/pts` with `gid=5` whenever the calling process has euid 0, and in a single-gid-mapping user namespace that gid is unmappable, so the kernel rejects the devpts mount with EINVAL and every container start fails. The patch omits `gid=5` whenever gid 5 is not covered by `/proc/self/gid_map`, which is exactly what crun's own rootless branch does. On normal hosts the stock behavior is preserved. `content_hash()` includes the patch so a patch change invalidates same-version build-cache entries. Built `--disable-systemd --disable-criu --without-*` (wasm runtimes, bindings); hard deps are `json-c`, `libseccomp`, `libcap`.

### `catatonit`

PID-1 pause process for rootless container namespaces, from the actively maintained openSUSE fork (the original opencontainers repo is gone). Single C file, no deps.

### `fuse-overlayfs`

Overlay storage mount program for podman inside the sandbox: kernel-native overlay cannot be used because the sandbox user cannot remount mounts private, and setuid `fusermount3` does not work because the node mounts `/` nosuid. As namespace root (inside the podman wrapper's user namespace) `fusermount3` is not needed. Built from the v1.18 git-tag archive (no release tarball); autotools build with `libfuse@3.2.1:`, `autoconf`, `automake`, `libtool`, `m4`.
### `opencode`

Builds OpenCode 1.18.25 from source with Bun and Node.js. The installed binary is standalone; Bun and Node are build dependencies. Runtime auto-update is disabled.

### `cscs-agent-skills`

Packages CSCS agent skills at commit `62b583eb3407f6266198db5d22244a233741aa45` as version 2026.09.01 and adds the `refresh-cscs-models` skill. Launchers install relative links into launcher-owned skill directories and leave user-owned directories untouched.

## Launcher invariants

Podman volatile state MUST live on `/dev/shm`, never on the home NFS filesystem, and must be shared across podman invocations. Three verified failure modes on NFS: (1) buildah creates mode-0100 scratch directories and writes into them, relying on CAP_DAC_OVERRIDE, which the kernel does not honor across NFS (mkdir EACCES during `podman build`); (2) fuse-overlayfs unmounts leave `.nfs*` silly-rename files that break container cleanup; (3) conmon exit files and crun container state under the per-invocation tmpfs `/run` vanish when the wrapper's namespace exits, so detached containers were misreported as exited and `podman exec`/`stop` failed across invocations. The wrapper therefore binds persistent `/dev/shm` directories over `/run/libpod` and `/run/crun`, keeps `TMPDIR`/`XDG_RUNTIME_DIR`/runroot under a shared `/dev/shm/podman-<uid>-state` tree, and rewrites the generated `containers.conf`/`storage.conf` runroot+tmpdir accordingly (the store database pins these at first creation, so changing them later requires wiping the graphroot). Known limitation: `podman exec` into a detached container only works from the same podman invocation's user namespace; `podman stop` works across invocations (signal path). The `--podman` sandbox root also shadows `/var/cache` and `/var/tmp` with tmpfs because rootful containers/image hardcodes those paths for its blob cache and staging.

The launcher's `--podman` mode exposes host podman through a wrapper (`files/podman.in`, installed per-user) that re-execs through `unshare --user --map-root-user --mount --propagation slave`: a fresh user namespace where the current user is root with CAP_SYS_ADMIN over a fresh mount namespace. Inside it, `/run` is a tmpfs (the sandbox `/` is read-only), `/etc/resolv.conf` is restored from a launcher copy (the host file is a symlink into `/run`), and host podman runs rootful with generated `CONTAINERS_CONF`/`CONTAINERS_STORAGE_CONF`. Rootful-in-userns maps container root to the current user, so layer extraction never needs subid ranges; images live on `/dev/shm/podman-$(id -u)` (RAM-backed, session-shared), runtime state under the launcher data dir. Known invariants: do not combine `--podman` with `--no-gpu-devices` (needs `/dev/fuse`); the podman stack (crun/catatonit/fuse-overlayfs) must remain explicit environment roots; the wrapper's resolv.conf restore must run before podman starts.

- Keep `--ro-bind / /` before `--proc /proc`. Reversing them exposes host `/proc` inside the private PID namespace and breaks CUDA initialization.
- The project and launcher XDG roots are writable; the remaining host filesystem is read-only. `/users`, `/home`, `/root`, and sandbox `/tmp` are hidden except for explicit bind paths.
- PID and IPC namespaces are private by default. Network and `/dev` are inherited; SSH agent access is opt-in and validates socket type, ownership, permissions, and symlinks.
- OpenCode and OMP retain separate XDG roots. Packaged skills use harness-specific ownership markers so existing managed directories continue to update.
- OMP interactive launches use `script` and Perl to remove dynamically generated ED3 sequences. The filter is disabled with `OMP_BWRAP_FILTER_ED3=0` and is skipped when either host command is unavailable.

## CSCS managed configuration

- Static production defaults are seeded only when no user alternative exists. Managed files have SHA-256 ownership sidecars.
- A launch refresh requires either a production or Forno key, an unchanged managed file, and an executable generator. It runs immediately when the set of available gateway credentials differs from the stamp, otherwise after 86,400 seconds.
- A successful refresh replaces the complete file, records its new hash, and writes only `production=0|1 forno=0|1` to the stamp. Failure preserves the file and old stamp, causing a retry on the next launch.
- When only the Forno key is present, the generator retains production models from the published snapshot but marks them credential-unavailable when choosing the default. This avoids deleting the production provider while allowing OpenCode to start on the first live Forno model.
- OpenCode management applies to `opencode.json` even when `opencode.jsonc` exists because OpenCode merges both. Generated production and Forno providers use their distinct key environment variables and API adapters.
- OMP does not manage `models.yml` when `models.yaml` exists. OMP 18 cost blocks must contain `input`, `output`, `cacheRead`, and `cacheWrite`; the generator emits all four when production pricing is available.
- The output budget must stay capped at half the context window (`limits()` in `cscs_models.py`), and gateway-advertised `maxTokens` must never feed the generator. External report (2026-09-10): the gateway's proxy discovery advertises `maxTokens: 262144` for `moonshotai/Kimi-K2.7-Code`, equal to the full context window. An Anthropic-adapter client with OMP's Kimi-family `alwaysSendMaxTokens` quirk shipped that value as `max_tokens`, and the Anthropic Messages API enforces `input_tokens + max_tokens <= context_window`, so any non-empty prompt failed with 400. The generator reads only `id`/`created` from `/v1/models` and derives the budget from `--max-output` (32768) with the half-context cap, so this uenv's configs never saw the bogus value. Do not remove the cap or start trusting discovery `maxTokens` even if the gateway fixes the value.
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

- The split and consolidated launcher iterations were built and exercised on Daint GH200 under the former `agents-bwrap/26.08` identity. The recipe was then renamed to `cscs-agents/26.08`, its view to `agents`, and the shared skills package to `cscs-agent-skills`. The Forno-enabled package revisions were published as `cscs-agents/26.09`.
- The current component update targets OpenCode 1.18.25, OMP 18.0.9, `cscs-agent-skills@2026.09.01`, `cscs-agent-model-config@2026.09.01`, and `cscs-agent-launchers@2026.09.01`. Upstream archive and release-asset checksums were refreshed from those pinned revisions.
- The 2026.09.01 model-config update adds dynamic Forno discovery. The gateway was verified to expose OpenAI-compatible `/v1/models` and `/v1/chat/completions`; its `/v1/messages` route did not accept either bearer or `x-api-key` authentication, so Forno must not reuse the production Anthropic adapter.
- Pre-build verification for the Forno update ran three focused generator contract tests, parsed every generated JSON/YAML output, loaded `cscs-forno/zai-org/GLM-5.3` through OpenCode 1.18.25 and OMP 18.0.9 model listing, and checked both launcher templates with Bash and ShellCheck. Stackinator and the uenv build were intentionally not run.
- The rebuilt `cscs-agents/26.09` image was exercised from an OMP launcher session with both gateway keys exported. The refresh stamp recorded `production=1 forno=1`; the managed ownership hash matched; live generation returned eight production models and one Forno model; OpenCode and OMP loaded both providers; and real inference returned the requested sentinel through all four provider/client combinations (production and Forno in both harnesses).
- During the consolidated build, `ftp.gnu.org` was unreachable for the URL patches of `bash@5.3`, while `mirror.spack.io` lacked the objects. Downloading all nine patches from `https://ftpmirror.gnu.org/bash/bash-5.3-patches/`, verifying the package checksums, and placing them in the configured content-addressed Spack source cache allowed the unmodified Bash package to build.
- `cleanup: runtime` initially removed Stackinator's implicit GCC and `squashfs` groups. Missing GCC produced an empty compiler configuration but was nonfatal; missing `squashfs` made image creation resolve `/bin/mksquashfs`. Making `squashfs` an explicit recipe root is the per-recipe keep exception. Revisit this if Stackinator begins protecting its internal packaging tools.
- The 2026-09-10 component update targets OpenCode 1.18.30 and OMP 18.1.16, carried by the new `cscs-agent-launchers@2026.09.10`. Both releases are routine fixes with no config-format changes; the OMP 18.1.16 Linux binaries contain the two expected ED3 sequences (the install-time scrollback patch still applies), and the opencode 1.18.30 workspace layout, bun pin (1.3.14), `script/build.ts` flags (`--single --skip-install`), and `dist/<name>/bin/opencode` output path are unchanged. The package recipes keep the previous harness versions (opencode 1.18.25, OMP 18.0.9) installable via `cscs-agent-launchers@2026.09.01`.
- Validation performed during development includes Bash syntax checks, Python source compilation, JSON/YAML parsing, substitution-token/content-hash checks, fake-bubblewrap launcher exercises, managed-config ownership tests, first/cached uv bootstrap tests, and live multi-uenv Python/PyTorch selection. The current component update additionally verified archive layouts and checksums, confirmed both OMP Linux binaries still contain the two expected ED3 sequences, and ran the patched ARM64 binary successfully as `omp/18.0.9`. Post-build runtime checks confirmed OpenCode 1.18.25, OMP 18.0.9, launcher help, static CSCS provider loading in OpenCode, OMP managed-file ownership, uv 0.12.7, private CPython 3.13.15, and PyTorch 2.9.1 with CUDA available.
