#!/usr/bin/env bash
# Run the AI recipe review locally, the same way .github/workflows/ai-review.yaml
# does, to iterate on prompt.md and recipes.instructions.md without pushing.
#
# The prompt and checklist are taken from THIS checkout (including uncommitted
# edits); the PR is fetched from GitHub. Nothing is posted, the review is printed.
#
# usage: .github/ai-review/run-local.sh [--backend cscs|anthropic] <pr-number> [owner/repo]
#
# Backends:
#   cscs       CSCS Inference Service, as in the workflow (default).
#              Key:   $CSCS_INFERENCE_API_KEY (required)
#              Model: $AI_REVIEW_MODEL (default zai-org/GLM-5.3-Flash)
#   anthropic  native Claude.
#              Auth:  $ANTHROPIC_API_KEY, or $CLAUDE_CODE_OAUTH_TOKEN for a Claude
#                     subscription (create it once with `claude setup-token`)
#              Model: $AI_REVIEW_MODEL (default: Claude Code's default model)
# Keys come only from the environment: as arguments they would show up in ps and
# the shell history. The run uses an isolated Claude Code config dir, so your
# normal `claude` login is not used.
#
# Claude:  $CLAUDE (default: claude from PATH)
# Workdir: $AI_REVIEW_WORKDIR (default: a new temp dir, kept for inspection)
set -euo pipefail

usage() {
  echo "usage: $0 [--backend cscs|anthropic] <pr-number> [owner/repo]" >&2
  exit 2
}

BACKEND=cscs
while [ $# -gt 0 ]; do
  case "$1" in
    -b | --backend) [ $# -ge 2 ] || usage; BACKEND=$2; shift 2 ;;
    --backend=*) BACKEND=${1#*=}; shift ;;
    -h | --help) usage ;;
    -*) usage ;;
    *) break ;;
  esac
done
PR=${1:-}
[ -n "$PR" ] || usage
REPO=${2:-eth-cscs/alps-uenv}

# backend-specific environment for run-review.sh
case "$BACKEND" in
  cscs)
    if [ -z "${CSCS_INFERENCE_API_KEY:-}" ]; then
      echo "error: set CSCS_INFERENCE_API_KEY" >&2
      exit 1
    fi
    MODEL=${AI_REVIEW_MODEL:-zai-org/GLM-5.3-Flash}
    backend_env=(
      ANTHROPIC_BASE_URL=https://api.inference.cscs.ch
      ANTHROPIC_AUTH_TOKEN="$CSCS_INFERENCE_API_KEY"
      MODEL="$MODEL"
    )
    ;;
  anthropic)
    if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
      echo "error: set ANTHROPIC_API_KEY, or CLAUDE_CODE_OAUTH_TOKEN (create it with \`claude setup-token\`)" >&2
      exit 1
    fi
    MODEL=${AI_REVIEW_MODEL:-}
    # a CSCS setup in the calling shell must not redirect the requests
    backend_env=(-u ANTHROPIC_BASE_URL -u ANTHROPIC_AUTH_TOKEN -u MODEL)
    [ -z "$MODEL" ] || backend_env+=(MODEL="$MODEL")
    ;;
  *) usage ;;
esac

BASE=$(cd "$(dirname "$0")/../.." && pwd)
WORK=${AI_REVIEW_WORKDIR:-$(mktemp -d -t ai-review.XXXXXX)}
mkdir -p "$WORK"
echo "backend: $BACKEND, model: ${MODEL:-Claude Code default}" >&2

echo "workdir: $WORK" >&2
cd "$WORK"
ln -sfn "$BASE" base

# PR checkout, in its own clone so the local repo is not touched
base_ref=$(gh pr view "$PR" --repo "$REPO" --json baseRefName -q .baseRefName)
rm -rf pr
git clone -q --filter=blob:none --no-checkout "https://github.com/$REPO.git" pr
git -C pr fetch -q --no-tags origin "pull/$PR/head:pr-head" "$base_ref:pr-base"
git -C pr checkout -q pr-head
rm -rf pr/.claude pr/CLAUDE.md pr/CLAUDE.local.md pr/.mcp.json
if ! git -C pr diff --name-only pr-base...HEAD | grep -q '^recipes/'; then
  echo "PR $PR does not change anything under recipes/, nothing to review." >&2
  exit 0
fi

# trusted reference material, same refs as the workflow
clone() { [ -d "$2" ] || git clone -q --depth 1 --branch "$3" "https://github.com/$1.git" "$2"; }
clone eth-cscs/stackinator stackinator main
clone eth-cscs/cscs-reframe-tests cscs-reframe-tests main

# Claude Code from $CLAUDE or PATH; the workflow pins a version, a local
# install may differ
CLAUDE=${CLAUDE:-claude}
if ! command -v "$CLAUDE" >/dev/null; then
  echo "error: claude not found; install Claude Code or set CLAUDE" >&2
  exit 1
fi
echo "claude: $("$CLAUDE" --version)" >&2

# isolated config dir: no personal settings, hooks, plugins or MCP servers
mkdir -p claude-config
cd pr
env "${backend_env[@]}" \
  CLAUDE="$CLAUDE" \
  CLAUDE_CONFIG_DIR="$WORK/claude-config" \
  "$BASE/.github/ai-review/run-review.sh" "$WORK"

echo >&2
echo "review ($WORK/review.md):" >&2
cat "$WORK/review.md"
