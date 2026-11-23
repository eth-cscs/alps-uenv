#!/usr/bin/env bash
# Run the AI recipe review locally, the same way .github/workflows/ai-review.yaml
# does, to iterate on prompt.md and recipes.instructions.md without pushing.
#
# The prompt and checklist are taken from THIS checkout (including uncommitted
# edits); the PR is fetched from GitHub. Nothing is posted, the review is printed.
#
# usage: .github/ai-review/run-local.sh <pr-number> [owner/repo]
#
# API key: $CSCS_INFERENCE_API_KEY (required)
# Model:   $AI_REVIEW_MODEL (default zai-org/GLM-5.3-Flash)
# Claude:  $CLAUDE (default: claude from PATH)
# Workdir: $AI_REVIEW_WORKDIR (default: a new temp dir, kept for inspection)
set -euo pipefail

PR=${1:?usage: $0 <pr-number> [owner/repo]}
REPO=${2:-eth-cscs/alps-uenv}
MODEL=${AI_REVIEW_MODEL:-zai-org/GLM-5.3-Flash}
BASE=$(cd "$(dirname "$0")/../.." && pwd)
WORK=${AI_REVIEW_WORKDIR:-$(mktemp -d -t ai-review.XXXXXX)}
mkdir -p "$WORK"

# the key comes only from the environment: as an argument it would show up in
# ps and the shell history
KEY=${CSCS_INFERENCE_API_KEY:-}
if [ -z "$KEY" ]; then
  echo "error: set CSCS_INFERENCE_API_KEY" >&2
  exit 1
fi

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
CLAUDE="$CLAUDE" \
CLAUDE_CONFIG_DIR="$WORK/claude-config" \
ANTHROPIC_BASE_URL=https://api.inference.cscs.ch \
ANTHROPIC_AUTH_TOKEN="$KEY" \
MODEL="$MODEL" \
  "$BASE/.github/ai-review/run-review.sh" "$WORK"

echo >&2
echo "review ($WORK/review.md):" >&2
cat "$WORK/review.md"
