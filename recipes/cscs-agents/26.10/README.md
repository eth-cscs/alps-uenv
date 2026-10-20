# CSCS coding agents uenv

This uenv provides isolated OpenCode 2.1.0, Oh-My-Pi (OMP) 18.10.3, and Prime Agent 0.10.0 launchers with CSCS production and experimental Forno inference discovery, packaged CSCS skills, ripgrep, ShellCheck, jq, and yq.

## Quick start

Export either or both CSCS inference keys before starting a harness:

```bash
export CSCS_INFERENCE_API_KEY=...        # production gateway
export CSCS_INFERENCE_API_KEY_FORNO=...  # experimental Forno gateway
```

`CSCS_API_KEY` is accepted as a compatibility alias for the production key. `CSCS_INFERENCE_API_KEY_FORNO` is the canonical Forno key name. Keys are read from the environment and are never written to generated configuration.

When starting through `uenv run`:

```bash
uenv run cscs-agents/26.10 -- omp-bwrap
uenv run cscs-agents/26.10 -- opencode-bwrap
uenv run cscs-agents/26.10 -- prime-agent-bwrap
```

When the uenv and its `agents` view are already active:

```bash
omp-bwrap
opencode-bwrap
prime-agent-bwrap
```

Use `--` to separate launcher options from harness arguments:

```bash
omp-bwrap -- --resume 01a0437e-5c57-727d-9bd9-8735c07fab3d
opencode-bwrap -- <opencode arguments>
prime-agent-bwrap -- <prime-agent arguments>
```

The current directory is the default writable project directory. Run any launcher with `--help` for project/XDG directory overrides, extra bind mounts, SSH-agent forwarding, GPU control, and a sandbox shell.

## Concurrent agents and project-local profiles

Use `--project-local` to give a project its own harness settings, sessions, and checkpoints instead of sharing the default home profile:

```bash
cd /path/to/project
omp-bwrap --project-local
```

Different projects can run independently. To run multiple agents of the same harness in one project, use distinct instance names in separate terminals:

```bash
omp-bwrap --project-local --instance implementer
omp-bwrap --project-local --instance reviewer
```

The same options work with `opencode-bwrap` and `prime-agent-bwrap`. Each harness and instance has a separate persistent profile at `.cscs-agents/26.10/<harness>/<instance>/`, containing `config`, `data`, `cache`, and `state` roots. The harness directory is `opencode-v2`, `omp`, or `prime-agent`; the new OpenCode namespace leaves v1 profiles untouched. Omitting `--instance` selects `default`. Names must start with an ASCII letter or digit and contain only ASCII letters, digits, `.`, `_`, or `-`.

The selected project is `--project-dir PATH`, or the current directory if omitted; the launcher does not search for a Git repository root. Use the same project directory and instance name to resume work:

```bash
omp-bwrap --project-dir /path/to/project --project-local --instance reviewer -- --continue
prime-agent-bwrap --project-dir /path/to/project --project-local --instance reviewer -- shutdown --force
```

Project-local mode starts with a fresh profile and packaged CSCS defaults; it does not copy or change your home profile. Continue exporting the inference keys in your shell. It cannot be combined with explicit `--config-dir`, `--data-dir`, `--cache-dir`, or `--state-dir` options. Without `--project-local`, the default home profiles are used; OpenCode v2 has its own new home namespace.

Only persistent harness data moves into the project. SQLite databases, runtime directories, and file-lock-sensitive state remain on validated node-local storage. Each instance retains its single-writer lease: a second OpenCode or OMP writer to the same instance is refused, while Prime Agent clients can reconnect to that instance's existing daemon. For stale-lease recovery, select the same profile, for example `omp-bwrap --project-local --instance reviewer --recover-storage`.

New `.cscs-agents` directories receive a `.gitignore` excluding all their contents, because profiles may contain credentials and conversation transcripts. Existing ignore rules are preserved; do not force-add these profiles to Git. The launcher rejects symlinked project-profile directories.

**Working files are still shared.** Named instances isolate harness state, not concurrent source edits or Git operations. Use separate worktrees/projects when agents must edit independently.

## CSCS inference configuration

The image contains static production model defaults, so the `cscs` provider is available before the first successful metadata refresh. On every harness launch, the wrapper checks whether a refresh is due:

- at least one production or Forno key must be available;
- the managed config must still match its ownership hash;
- the set of available gateway credentials must have changed, or at least 24 hours must have passed since the last successful refresh.

The first launch with either key refreshes immediately. Adding or removing the Forno key also refreshes immediately instead of waiting for the 24-hour interval. Model refresh is launch-driven and does not run in the background daemon. Generation happens in a temporary directory: a gateway or metadata failure keeps the existing complete config and is retried on the next launch. Set `CSCS_MODEL_REFRESH_VERBOSE=1` to display generator errors and wrapper warnings.

When `CSCS_INFERENCE_API_KEY_FORNO` is set, the generator queries `https://ai-gateway.forno-tds.tds.cscs.ch/v1/models` and adds every advertised model under the `cscs-forno` provider. The catalogue is not pinned because Forno is an experimental service and changes frequently. Forno exposes OpenAI Chat Completions rather than the production Anthropic Messages route, so the generated OpenCode, OMP, and Prime Agent providers use their OpenAI-compatible adapters. Forno currently publishes neither prices nor deployment context lengths; the generator uses public Hugging Face metadata when available and a conservative 32,768-token context fallback for a new or private model until metadata appears.

With both keys present, the production default remains selected. With only the Forno key, OpenCode selects the first advertised Forno model while retaining the static production catalogue for later use when its key becomes available.

Prime Agent keeps its production default when both gateways are configured. With only a Forno key, select a generated model explicitly, for example with `prime-agent-bwrap -- --provider cscs-forno --model <model-id>`.

OMP defaults to these model roles:

| Role | Model |
|---|---|
| `default` | `cscs/moonshotai/Kimi-K2.7-Code` |
| `smol` | `cscs/swiss-ai/Apertus-8B-Instruct-2509` |
| `slow` | `cscs/zai-org/GLM-5.2` |

OpenCode and Prime Agent default to `cscs/moonshotai/Kimi-K2.7-Code`.

Launcher-owned files use SHA-256 sidecars. Editing a managed model, provider, or settings file makes it user-owned and stops automatic updates rather than overwriting the edit.

OpenCode manages `opencode.json` and leaves `opencode.jsonc` user-owned; OpenCode merges both files. For OMP, a user-created `models.yaml` takes precedence and disables launcher management of `models.yml`. Prime Agent manages its native `models.json` and seeds `settings.json`; editing either file transfers ownership to the user.

Default home-profile locations (project-local profiles use the instance's `config` root instead):

| Harness | Host configuration directory |
|---|---|
| OpenCode | `${XDG_CONFIG_HOME:-$HOME/.config}/opencode-v2-cscs-agents-26.10/xdg/opencode` |
| OMP | `${XDG_CONFIG_HOME:-$HOME/.config}/omp-cscs-agents-26.10/home/.omp/agent` |
| Prime Agent | `${XDG_CONFIG_HOME:-$HOME/.config}/prime-agent-cscs-agents-26.10/home/.prime/agent` |

To force the next refresh without changing ownership, delete only the relevant refresh stamp:

```bash
rm "${XDG_CONFIG_HOME:-$HOME/.config}/opencode-v2-cscs-agents-26.10/xdg/opencode/.opencode-bwrap-cscs-models.refresh"
rm "${XDG_CONFIG_HOME:-$HOME/.config}/omp-cscs-agents-26.10/home/.omp/agent/.omp-bwrap-cscs-models.refresh"
rm "${XDG_CONFIG_HOME:-$HOME/.config}/prime-agent-cscs-agents-26.10/home/.prime/agent/.prime-agent-bwrap-cscs-models.refresh"
```

## OpenCode 2 migration

OpenCode uses a private server owned by each foreground invocation, not a persistent background service. No separate daemon or uenv is needed. The launcher binds its `service.json` read-only with `disabled: true`, so enabling the managed background service cannot bypass the writer lease and final checkpoint. An inherited `OPENCODE_CONFIG_DIR` is unset to preserve profile isolation. Use `--project-local --instance NAME` for concurrent agents.

Terminal settings now live in the profile's `xdg/opencode/cli.json`; `mouse: false` is seeded only when that file is absent. Generated native v2 providers keep the existing gateway routes and credential variables, explicitly retain Forno's `max_tokens` parameter, and leave thinking defaults to the gateway rather than inferring unsupported effort variants. The title agent uses the selected CSCS default model. Outside-project file access requires approval by default.

**Upstream capability changes:** v2.1.0 does not run language servers or provide LSP tools/diagnostics. Use project compiler, typecheck, and lint commands instead. V1 plugins and server API integrations need porting, and project guidance should use `AGENTS.md`, not the removed `CLAUDE.md` fallback. See the [upstream v1 migration guide](https://github.com/anomalyco/opencode/blob/v2.1.0/services/www/src/docs/content/migrate-v1.mdx).

Home roots are now `opencode-v2-cscs-agents-26.10`; project roots use `opencode-v2/<instance>`. Checkpoints and leases use `.cscs-agent-storage/opencode-v2*` even with explicit directory overrides. V1 profiles and checkpoint generations are not imported or modified automatically, so the old image remains usable with its original state.

To import history, stop the old writer and copy a healthy, immutable v1 checkpoint **before the first v2 session**. For default home profiles:

```bash
old="${XDG_DATA_HOME:-$HOME/.local/share}/opencode-cscs-agents-26.10/.cscs-agent-storage/opencode"
new="${XDG_DATA_HOME:-$HOME/.local/share}/opencode-v2-cscs-agents-26.10"
generation="$(cat "${old}/current")"
install -Dm600 "${old}/generations/${generation}/opencode.db" "${new}/opencode/opencode.db"
opencode-bwrap
```

For project profiles, substitute the old `opencode/<instance>/data` and new `opencode-v2/<instance>/data` roots. The launcher byte-stages the copied database locally; upstream then migrates history to v2, and subsequent checkpoints go only to the v2 namespace. Keep the original backup: rich-history migration and downgrade compatibility need validation on your own data. Review custom settings and plugins rather than copying an entire v1 configuration tree.


## Prime Agent background service

Prime Agent uses a persistent supervisor and worker processes. `prime-agent-bwrap` starts the supervisor through a storage guard in a separate bubblewrap sandbox, then connects the foreground client through a private Unix socket. The daemon is keyed by node boot, Slurm allocation, project path, profile, and launcher isolation options, so it is never reused by another allocation or node. Each profile also has a separate node-local `TMPDIR` discovery root, so `status`, `doctor`, and `shutdown` cannot act on another profile's daemon. The guard holds the profile's distributed writer lease for the daemon lifetime and terminates the daemon if the guard exits.

Sessions and the Python kernel environment live under `${XDG_DATA_HOME:-$HOME/.local/share}/prime-agent-cscs-agents-26.10`; daemon logs live under `${XDG_STATE_HOME:-$HOME/.local/state}/prime-agent-cscs-agents-26.10/daemons`. Use Prime Agent's `list`, `status`, and `doctor` commands through `prime-agent-bwrap`. Stop the service with `prime-agent-bwrap shutdown --force`, using the same launcher options that started it.

## Persistent storage and recovery

The default CSCS home filesystem is NFSv3 and cannot safely host SQLite WAL databases or process-local lock state. The launchers therefore enforce one active writer for each harness profile, where a profile is identified by its config, data, and state roots, whether selected from home XDG directories or a project-local instance.

OpenCode keeps its SQLite database under `/dev/shm` and publishes a validated SQLite backup to immutable generations under its persistent data root. Its cache is disposable node-local state; writable overlays keep `state/opencode/locks`, `state/opencode/pty`, and `state/opencode/latest/locks` local while durable preferences remain persistent. These runtime overlays start fresh under each writer lease. OMP keeps XDG data, state, cache, SQLite databases, and runtime locks under `/dev/shm`; its large sessions, blobs, plugins, worktrees, and similar durable directories remain directly on persistent storage under the single-writer lease. OMP data and state not covered by those direct persistent directories are included in the same generation mechanism. Prime Agent keeps sessions, settings, credentials, and its kernel environment persistent while its session leases, worker registry, sockets, and PID state stay node-local.

OpenCode and OMP checkpoint every 30 seconds by default and again after a clean exit. A node failure or `SIGKILL` can therefore lose at most the changes since the last successful periodic checkpoint; the previous complete generation is retained and used automatically when the current generation fails its SQLite integrity check. Override the interval with `CSCS_AGENT_CHECKPOINT_SECONDS`.

Node-local state defaults to `/dev/shm/cscs-agent-storage-$(id -u)`. `CSCS_AGENT_LOCAL_STORAGE_DIR` may select another owned, non-symlink directory, but the launcher rejects known network filesystem types. Extra writable binds may not overlap protected node-local storage or runtime paths.

The launcher never steals a stale profile lease automatically. When startup reports an existing lease, verify that its recorded process or Slurm job is gone, then quarantine it explicitly:

```bash
opencode-bwrap --recover-storage
omp-bwrap --recover-storage
prime-agent-bwrap --recover-storage
```

Recovery does not delete the old lease; it renames it for inspection. Profile lease acquisition, release, and recovery are serialized by a second atomic operation lease, and generated configuration maintenance uses a separate short-lived lease. Prime Agent management commands do not start a daemon merely to answer `status`, `doctor`, or `shutdown`.

The 26.10 launchers use versioned `*-cscs-agents-26.10` profile roots and never import from or modify the older persistent `*-spack` profiles automatically. Migration from an earlier image is an explicit one-time administrative task. When a legacy database is deliberately placed in a new profile for import, its database and WAL journal are copied to node-local staging before SQLite opens them. Do not use `omp-local` with this image.

Prime Agent discovers the packaged CSCS skills from its launcher-owned `skills` directory and project skills from `.agents/skills`. The separate `prime-rl` project is not installed: it is a GPU reinforcement-learning training stack, not a runtime dependency of the coding agent. Prime Agent's upstream `prime-intellect` skill still provides guidance for Prime Intellect services, including prime-rl workflows.

## Using another uenv

Mounting another uenv is not enough: its view must also be active. For example, to use the Python and packages from a PyTorch uenv:

```bash
uenv run cscs-agents/26.10,pytorch --view=agents,default -- omp-bwrap
```

Use fully qualified uenv names or image paths as appropriate. Verify both views with:

```bash
uenv status
```

Expected state:

```text
uenv  cscs-agents
  views  [agents]
uenv  pytorch
  views  [default]
```

Direct `python` and `python3` follow the inherited view `PATH`; with the PyTorch default view active they resolve to its interpreter and retain its packages. User-facing uv also prefers compatible interpreters from the inherited `PATH`.

The launcher separately maintains a private uv-managed Python for `cscs-agent-model-config`. Its executable links are stored under version-specific private directories and are deliberately not on `PATH`, so they cannot shadow project Python. The model generator always selects this private interpreter and never depends on the project or host Python. Prime Agent also creates a persistent, isolated Python kernel environment under its launcher data directory; it uses the same launcher-managed uv command without changing project `python` resolution.

An isolated uv project environment does not automatically inherit packages from a PyTorch uenv. Use the loaded uenv's Python directly when its packaged PyTorch installation is required, or declare the dependencies in the uv project.

## uv and mutable tools

On first launch on each node, the wrapper installs uv and a private managed Python under `${CSCS_AGENT_LOCAL_STORAGE_DIR:-/dev/shm/cscs-agent-storage-$(id -u)}/tools`; the uv cache lives in the sibling `uv-cache` directory. These directories are shared by all harness profiles on that node. Both must stay on a local filesystem: uv takes file locks in its cache and Python installation directories, and those operations can hang on NFS before the normal lock timeout applies.

Bootstrap requires host `curl` and network access and is noninteractive. An atomic bootstrap directory serializes installation, and later launches validate both uv's reported version and the managed interpreter links. Prime Agent uses that uv installation to create its kernel environment on first use of the Python tool.

`CSCS_AGENT_TOOLS_DIR` and `CSCS_AGENT_TOOLS_CACHE_DIR` can select other owned, non-symlink directories on local filesystems. Network-backed overrides are rejected before uv starts, and extra bind mounts cannot mask the tools or cache paths. Old tools under the XDG data/cache roots are not imported or deleted automatically.

uv, managed Python, the cache, and `uv tool` installations are node-local and are not checkpointed. They must be reinstalled on another node or after this storage is cleared; bootstrap handles uv and managed Python automatically. Agent configuration and sessions remain persistent.

Use uv normally for project-local dependencies and tools:

```bash
uv run --with pyyaml python -c 'import yaml'
uv tool install <tool>
```

The uenv also exposes `shellcheck`, `jq`, `yq`, and `rg` without requiring uv.

## Building containers

Launch any harness with `--podman` to get a working `podman` command inside the sandbox:

```bash
uenv run cscs-agents/26.10 -- omp-bwrap --podman
```

The command runs the host podman inside an isolated user and mount namespace with its own generated configuration. Image layers and volatile runtime state are stored under `/dev/shm` (RAM-backed, shared across launches, and counted against the node's memory allocation); only the small generated configuration lives under the launcher's data directory. Containers run as the current user. Requirements: host podman and `/dev/fuse`; do not combine with `--no-gpu-devices`.

```bash
podman pull registry.suse.com/bci/bci-base:latest
podman run --rm registry.suse.com/bci/bci-base:latest cat /etc/os-release
```

## Isolation model

The wrappers expose the host filesystem read-only, hide normal home directories and `/tmp`, and make only the project directory plus launcher-specific XDG state writable. Network and GPU devices are available by default. SSH agent access requires `--ssh-agent`.

OpenCode, OMP, and Prime Agent use separate persistent profiles. OpenCode and OMP additionally receive private node-local storage for SQLite and lock-sensitive state. Existing configuration in the applications' normal home-directory locations is not used unless explicitly selected.

Because the harness itself runs in bubblewrap, nested bubblewrap workflows such as Stackinator builds must be run outside the harness.

## Maintainer information

Package internals, launcher invariants, build history, and Stackinator workarounds are recorded in [BUILD_NOTES.md](BUILD_NOTES.md).
