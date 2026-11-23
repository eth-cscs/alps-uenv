---
applyTo: "recipes/**"
---

# Reviewing uenv recipes

Recipes live in `recipes/<name>/<version>/[<target>/]` and are built with Stackinator.
Each recipe has `config.yaml`, `compilers.yaml`, `environments.yaml`, and optionally
`modules.yaml`, `packages.yaml`, `repo/`, `extra/` (e.g. `extra/reframe.yaml`),
`pre-install` and `post-install`. Cluster defaults (libfabric and other network specs,
cray-mpich, CUDA/nvhpc packages, preferences) come from alps-cluster-config and should
not be repeated in recipes.

Only comment on real problems. Do not comment on YAML style, ordering or formatting.
"Error" = will break the build, deployment or ReFrame tests, or violates a hard rule.
"Warning" = reviewers routinely ask about it; phrase it as a question if unsure.

Each rule names its source: [stackinator] = Stackinator docs/CLAUDE.md for the recipe's
version, [guide] = this repo's `pkg-application-tutorial.md` / `pkg-reframe.md` /
`pkg-writing-docs.md`, [reviewers] = recurring requests from maintainers in past PR reviews.
If a rule here and the Stackinator docs disagree, Stackinator wins for syntax and validity.

## Checklist

1. **default-view**:
   - `prgenv-*` recipes (error, [reviewers]): new versions must set `default-view: default`
     in `config.yaml`. Older prgenv versions that lack it are only flagged if the PR edits
     their `config.yaml`.
   - Any recipe (warning, [stackinator]): a view named `default` implies it is loaded by
     default, so `config.yaml` should set `default-view: default`.
   - Any recipe (error, [stackinator]): if `default-view` is set, it must name a view defined
     in `environments.yaml` (or `modules`/`spack`).
   - Otherwise `default-view` is optional; don't require it.

2. **Stackinator format** (error unless noted, [stackinator]). Check against the docs for
   the recipe's `version`:
   - `version: 3` recipes use Stackinator v7 and Spack ≥ 1.2. `version: 2` recipes use
     Stackinator v6 and Spack 1.0/1.1. Flag a `version` that doesn't match `spack.commit`.
   - `compilers.yaml` versions must be quoted strings (`"14"`, not `14`). A compiler
     `spec:` field replaces the default variants, so the defaults that are still wanted
     must be restated.
   - Environments must not list MPI or compilers in `specs`; those go in `network: mpi:`
     and `compiler:`. The old `mpi:` field was replaced by `network:`. Only one MPI per
     environment.
   - View names must be unique across all environments of a recipe. `uenv_tools` is a
     reserved environment name.
   - In `version: 3`, the environment `packages:` field is ignored (warning); externals go
     in `packages.yaml`.
   - Modules: the presence of `modules.yaml` enables modules. The `config.yaml` `modules:`
     key is deprecated, and if present it must be consistent with whether `modules.yaml`
     exists. `modules:default:arch_folder: true` is an error.
   - `mirrors.yaml` in a recipe is unsupported. `repo/` must contain `packages/`, and a
     `repo/repos.yaml` is ignored.
   - `unify`: use `true` when possible, then `when_possible`, then `false` (warning).

3. **Regressions vs. previous version** ([reviewers]): when a new version directory is
   added, diff it against the most recent earlier version of the same recipe. Flag
   anything dropped without explanation in the PR description:
   - files (`modules.yaml`, `extra/reframe.yaml`, `post-install`, `repo/`);
   - `config.yaml` keys and `network:` settings;
   - view `uenv:` settings (`add_compilers`, `prefix_paths`, `env_vars`);
   - root specs and variants;
   - deployment targets in the top-level `config.yaml`.

4. **Spack commits** (`config.yaml`, [guide] + [reviewers]):
   - Error: `spack.commit` and `spack.packages.commit` must be set, and must not be left
     unpinned or tracking `develop` for a deployed uenv.
   - Warning: prefer a release branch/tag (`releases/vX.Y`, `vYYYY.MM.N`) over a raw sha.
     A sha needs a comment with its date/branch.
   - Warning: no leftover commented-out alternative commits.

5. **Version pins and constraints** (warning, [reviewers]):
   - Every exact version pin (`@x.y.z`, compiler minor versions, CUDA versions) should have
     a comment saying why. The guide lists valid reasons: reproducibility, a well-tested
     version, a bug fix. Pins copied unchanged from the previous version without a comment:
     ask whether they are still needed.
   - Pre-release / rc versions in a user-facing uenv: ask whether intended.
   - Compiler versions should be consistent across targets of the same version
     (e.g. `"14"` on mc vs `"14.2"` on gh200), or the difference explained.

6. **Things alps-cluster-config already provides** (warning, [reviewers]): flag the
   following unless a comment explains why. Prefer the network defaults from the cluster
   `network.yaml`:
   - explicit `libfabric` pins or custom commits in `network: specs:`;
   - external libfabric/cray-mpich/xpmem settings;
   - `packages.yaml` entries that duplicate cluster config.

7. **Custom packages in `repo/packages/`** (warning, [reviewers]):
   - Ask whether each package is still needed at the pinned spack-packages commit. Has
     the change been upstreamed? Would bumping spack-packages remove the need?
   - Changes from upstream should carry a comment explaining them.
   - Flag package files that are identical to upstream.

8. **Files that don't belong** (warning, [reviewers]):
   - personal build/helper scripts, and `cache-config.yaml` or other local build config;
   - unused files;
   - debug leftovers: specs commented out "for testing", TODOs meant for before merging;
   - edits to `ci/` files that look accidental.

9. **PR scope** (warning, [reviewers]): changes to other, already deployed recipe versions
   usually don't belong in the PR (e.g. an older `prgenv-gnu/25.x` while adding 26.x).
   Flag them unless the PR description explains them.

10. **Copy-paste leftovers** (warning, [reviewers]): flag what belongs to the recipe this
    one was copied from:
    - names, comments, variants, packages or env vars, e.g. features or specs for a
      package the recipe no longer contains;
    - architecture suffixes in env/view names of a single-target recipe;
    - stale comments.

11. **Targets** ([reviewers]): if a recipe has several targets (e.g. `mc`, `gh200`, `zen2`),
    changes to one target should normally be mirrored in the others (modulo CUDA/ROCm).
    Flag differences in specs, variants, `config.yaml` or `reframe.yaml` that look accidental.

12. **Views** (warning, [guide]):
    - Use `link: roots`. Other settings pull implicit dependencies such as `libssl` into
      the view, which breaks system tools like `git` when `LD_LIBRARY_PATH` is set.
      Everything users need at runtime or to build against must then be a root spec.
    - Prefer setting env vars in the view's `uenv: env_vars` over activation scripts
      ([reviewers]).
    - Mount point: tool uenvs meant to be used alongside another uenv use
      `store: /user-tools`; others use `store: /user-environment`.

13. **Naming, description, GPU variants** ([guide]):
    - `name` in `config.yaml` is the same on every target and has no target suffix
      (`arbor`, not `arbor-gpu`/`arbor-x86`). It matches the name in the top-level
      `config.yaml` (error if not).
    - `description` fits on one line (warning).
    - NVIDIA GPU environments set `+cuda` and a `cuda_arch` matching the target:
      `90`/`90a` for gh200, `80` for a100.
    - AMD GPU environments set `+rocm` and an `amdgpu_target` matching the target:
      `gfx90a` for mi200, `gfx942` for mi300.
    - Flag a missing GPU variant, or an arch that doesn't match the target (error).

14. **ReFrame metadata** (`extra/reframe.yaml`, [guide] `pkg-reframe.md` + [reviewers]):
    - Every recipe should provide one (warning). It must not be dropped if the previous
      version had one.
    - Each top-level key is a ReFrame environment with `features`, `cc`, `cxx`, `ftn`, and
      optionally `views`, `activation` and `extras`.
    - Every view under `views` must exist in `environments.yaml`, or be the `modules`/`spack`
      view the recipe provides. A wrong view name breaks the deployed uenv's tests (error).
    - An environment that uses modules needs an `activation` section that loads them (error).
    - `features` must match what the view actually provides. For example:
      - `cuda` only with CUDA, and `rocm` (not `cuda`) on AMD GPUs;
      - `mpi` together with the flavour feature (`cray-mpich`);
      - `nccl`/`nccl-tests` (or the rccl equivalents) if those are in the uenv;
      - `prgenv` for programming-environment views;
      - `<app>` only if the view contains the application. A view that only has the
        dependencies to build it uses `<app>-dev`;
      - no features for packages that are not root specs.
    - Features must not be lost compared to the previous version or other targets without
      a reason. For features the PR adds, check that some test in cscs-reframe-tests uses
      them (grep for `+<feature>`). If none does, warn: it may be a typo. Features carried
      over from the previous version are fine.
    - Application uenvs (cp2k, quantumespresso, ...) should set `extras: version: <version>`
      if the previous version or other targets do.
    - `cc`/`cxx`/`ftn` must be compilers or MPI wrappers the environment provides.

15. **Registration and docs** ([guide] + [reviewers]):
    - A new recipe or version must be added to the top-level `config.yaml` under
      `uenvs: <name>: <version>:`, with:
      - `recipes: <uarch>: <path>` pointing to existing recipe directories (error if a
        path doesn't exist);
      - `deploy: <cluster>: [<uarch>]` covering at least the same clusters as the previous
        version. Ask about clusters it is missing from.
    - The uenv name must stay consistent with existing naming.
    - User-facing uenvs should update `docs/uenv-<name>.md` in the same PR. A new docs page
      must also be added to `nav` in `mkdocs.yml`, or it won't be published.
    - A new recipe directory should get a `.github/CODEOWNERS` entry.

16. **Specs** (warning, [reviewers]):
    - Flag duplicate root specs in an environment, e.g. `hdf5+mpi` and
      `hdf5+cxx+hl+fortran` listed separately.
    - Flag several specs where one was probably intended.
    - Flag conflicting variants on the same package.
    - Two variants of the same package are fine if intended (e.g. `hdf5~mpi` and
      `hdf5+mpi`) together with `unify: when_possible`/`false`.
