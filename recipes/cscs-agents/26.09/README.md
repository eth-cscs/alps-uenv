# CSCS coding agents uenv

This uenv provides isolated OpenCode 1.18.25 and Oh-My-Pi (OMP) 18.0.9 launchers with CSCS production and experimental Forno inference discovery, packaged CSCS skills, ripgrep, ShellCheck, jq, and yq.

## Quick start

Export either or both CSCS inference keys before starting a harness:

```bash
export CSCS_INFERENCE_API_KEY=...        # production gateway
export CSCS_INFERENCE_API_KEY_FORNO=...  # experimental Forno gateway
```

`CSCS_API_KEY` is accepted as a compatibility alias for the production key. `CSCS_INFERENCE_API_KEY_FORNO` is the canonical Forno key name. Keys are read from the environment and are never written to generated configuration.

When starting through `uenv run`:

```bash
uenv run cscs-agents/26.09 -- omp-bwrap
uenv run cscs-agents/26.09 -- opencode-bwrap
```

When the uenv and its `agents` view are already active:

```bash
omp-bwrap
opencode-bwrap
```

Use `--` to separate launcher options from harness arguments:

```bash
omp-bwrap -- --resume 01a0437e-5c57-727d-9bd9-8735c07fab3d
opencode-bwrap -- <opencode arguments>
```

The current directory is the default writable project directory. Run either launcher with `--help` for project/XDG directory overrides, extra bind mounts, SSH-agent forwarding, GPU control, and a sandbox shell.

## CSCS inference configuration

The image contains static production model defaults, so the `cscs` provider is available before the first successful metadata refresh. On every harness launch, the wrapper checks whether a refresh is due:

- at least one production or Forno key must be available;
- the managed config must still match its ownership hash;
- the set of available gateway credentials must have changed, or at least 24 hours must have passed since the last successful refresh.

The first launch with either key refreshes immediately. Adding or removing the Forno key also refreshes immediately instead of waiting for the 24-hour interval. Refresh is launch-driven; there is no background service. Generation is atomic: a gateway or metadata failure keeps the existing complete config and is retried on the next launch. Set `CSCS_MODEL_REFRESH_VERBOSE=1` to display generator errors and wrapper warnings.

When `CSCS_INFERENCE_API_KEY_FORNO` is set, the generator queries `https://ai-gateway.forno-tds.tds.cscs.ch/v1/models` and adds every advertised model under the `cscs-forno` provider. The catalogue is not pinned because Forno is an experimental service and changes frequently. Forno exposes OpenAI Chat Completions rather than the production Anthropic Messages route, so the generated OpenCode and OMP providers use their OpenAI-compatible adapters. Forno currently publishes neither prices nor deployment context lengths; the generator uses public Hugging Face metadata when available and a conservative 32,768-token context fallback for a new or private model until metadata appears.

With both keys present, the production default remains selected. With only the Forno key, OpenCode selects the first advertised Forno model while retaining the static production catalogue for later use when its key becomes available.

OMP defaults to these model roles:

| Role | Model |
|---|---|
| `default` | `cscs/moonshotai/Kimi-K2.7-Code` |
| `smol` | `cscs/swiss-ai/Apertus-8B-Instruct-2509` |
| `slow` | `cscs/zai-org/GLM-5.2` |

OpenCode defaults to `cscs/moonshotai/Kimi-K2.7-Code`.

Launcher-owned files use SHA-256 sidecars. Editing a managed model file makes it user-owned and stops automatic refresh rather than overwriting the edit.

OpenCode manages `opencode.json` and leaves `opencode.jsonc` user-owned; OpenCode merges both files. For OMP, a user-created `models.yaml` takes precedence and disables launcher management of `models.yml`.

| Harness | Host configuration directory |
|---|---|
| OpenCode | `${XDG_CONFIG_HOME:-$HOME/.config}/opencode-spack/xdg/opencode` |
| OMP | `${XDG_CONFIG_HOME:-$HOME/.config}/omp-spack/home/.omp/agent` |

To force the next refresh without changing ownership, delete only the relevant refresh stamp:

```bash
rm "${XDG_CONFIG_HOME:-$HOME/.config}/opencode-spack/xdg/opencode/.opencode-bwrap-cscs-models.refresh"
rm "${XDG_CONFIG_HOME:-$HOME/.config}/omp-spack/home/.omp/agent/.omp-bwrap-cscs-models.refresh"
```

## Using another uenv

Mounting another uenv is not enough: its view must also be active. For example, to use the Python and packages from a PyTorch uenv:

```bash
uenv run cscs-agents/26.09,pytorch --view=agents,default -- omp-bwrap
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

The launcher separately maintains a private uv-managed Python for `cscs-agent-model-config`. Its executable links are deliberately not on `PATH`, so it cannot shadow project Python. The model generator always selects this private interpreter and never depends on the project or host Python.

An isolated uv project environment does not automatically inherit packages from a PyTorch uenv. Use the loaded uenv's Python directly when its packaged PyTorch installation is required, or declare the dependencies in the uv project.

## uv and mutable tools

On first launch, the wrapper installs uv and a private managed Python under `${XDG_DATA_HOME:-$HOME/.local/share}/cscs-agent-tools`. This requires host `curl`, network access, and can take about a minute; it is noninteractive. Later launches validate a version marker and skip installation.

Use uv normally for project-local dependencies and tools:

```bash
uv run --with pyyaml python -c 'import yaml'
uv tool install <tool>
```

The uenv also exposes `shellcheck`, `jq`, `yq`, and `rg` without requiring uv.

## Isolation model

The wrappers expose the host filesystem read-only, hide normal home directories and `/tmp`, and make only the project directory plus launcher-specific XDG state writable. Network and GPU devices are available by default. SSH agent access requires `--ssh-agent`.

OpenCode and OMP use separate configuration, data, cache, and state roots. Existing configuration in the applications' normal home-directory locations is not used unless explicitly selected.

Because the harness itself runs in bubblewrap, nested bubblewrap workflows such as Stackinator builds must be run outside the harness.

## Maintainer information

Package internals, launcher invariants, build history, and Stackinator workarounds are recorded in [BUILD_NOTES.md](BUILD_NOTES.md).
