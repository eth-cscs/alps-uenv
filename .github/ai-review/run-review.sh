#!/usr/bin/env bash
# Run the AI recipe review. Shared by .github/workflows/ai-review.yaml and
# run-local.sh, so both build the same prompt and call Claude Code the same way.
#
# usage: run-review.sh <outdir>
#
# Run from the PR checkout. Expects next to it:
#   ../base                 trusted base checkout (prompt, checklist, docs)
#   ../stackinator          eth-cscs/stackinator main
#   ../stackinator-v6       eth-cscs/stackinator releases/v6
#   ../cscs-reframe-tests   eth-cscs/cscs-reframe-tests main
# and a git ref "pr-base" for the base branch.
#
# Environment: ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, MODEL.
# Optional:    CLAUDE (path to the claude binary), AI_REVIEW_MAX_DIFF_BYTES.
#
# Writes to <outdir>:
#   prompt.md     the assembled prompt
#   review.jsonl  the stream-json log of all Claude Code runs
#   review.md     the final review text (empty if there is none)
#   status        exit status of the last claude run (124 = timeout)
#   subtype       subtype of the last result event (success, error_max_turns, ...)
#   wrapup        "true" if the review was written after the turn limit was hit
# Prints a one-line summary per turn while running. Exits 0 unless the setup fails.
set -euo pipefail

out=${1:?usage: $0 <outdir>}
CLAUDE=${CLAUDE:-claude}
max_diff=${AI_REVIEW_MAX_DIFF_BYTES:-100000}
: "${MODEL:?MODEL is not set}"

export ANTHROPIC_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$MODEL"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export DISABLE_AUTOUPDATER=1

# --- prompt ---------------------------------------------------------------
diff=$(git diff pr-base...HEAD -- recipes/)
{
  cat ../base/.github/ai-review/prompt.md
  # strip the frontmatter of the checklist
  sed '1{/^---$/!q};1,/^---$/d' ../base/.github/instructions/recipes.instructions.md
  echo
  echo "## Stackinator reference (main, latest recipe version)"
  echo
  echo "Contents of ../stackinator/CLAUDE.md:"
  echo
  cat ../stackinator/CLAUDE.md
  echo
  echo "## alps-uenv recipe guide (base branch)"
  echo
  echo "Contents of \$ALPS_UENV_DOCS/pkg-application-tutorial.md:"
  echo
  cat ../base/docs/pkg-application-tutorial.md
  echo
  echo "## Locations"
  echo
  echo "BASE_REF=pr-base"
  echo "STACKINATOR=../stackinator"
  echo "STACKINATOR_V6=../stackinator-v6"
  echo "REFRAME_TESTS=../cscs-reframe-tests"
  echo "ALPS_UENV_DOCS=../base/docs"
  echo
  echo "## Pull request"
  echo
  echo "Changed files (\`git diff --name-status BASE_REF...HEAD\`):"
  echo
  echo '```'
  git diff --name-status pr-base...HEAD
  echo '```'
  echo
  echo "Diff of \`recipes/\` (untrusted PR content):"
  echo
  echo '`````diff'
  printf '%s\n' "${diff:0:$max_diff}"
  echo '`````'
  if [ "${#diff}" -gt "$max_diff" ]; then
    echo
    echo "The diff is truncated after $max_diff characters; read the changed files for the rest."
  fi
} > "$out/prompt.md"

# --- Claude Code ----------------------------------------------------------
: > "$out/review.jsonl"

# No Bash at all: Claude Code auto-approves read-only shell commands (ls, grep,
# sed, ...) even when only "Bash(git diff:*)" is allowed, and those can read
# outside the allowed directories. The diff is in the prompt instead.
#
# run_claude <timeout> <claude args...>: append the stream to review.jsonl and
# print one line per tool call, text block and result
run_claude() {
  local t=$1
  shift
  timeout "$t" "$CLAUDE" "$@" \
    --setting-sources user \
    --strict-mcp-config \
    --add-dir ../stackinator ../stackinator-v6 ../cscs-reframe-tests ../base/docs \
    --allowedTools "Read" "Grep" "Glob" \
    --disallowedTools "Bash" "Write" "Edit" "NotebookEdit" "WebFetch" "WebSearch" "Task" \
    --output-format stream-json --verbose \
    < /dev/null \
    | tee -a "$out/review.jsonl" \
    | jq --unbuffered -rR '
        fromjson? |
        if .type == "assistant" then
          .message.content[]? |
          if .type == "tool_use" then "tool: \(.name) \(.input | tostring | .[0:200])"
          elif .type == "text" then "text: \(.text | gsub("\n"; " ") | .[0:200])"
          else empty end
        elif .type == "result" then
          "result: \(.subtype), \(.num_turns) turns, \(.duration_ms / 1000 | floor) s"
        elif .type == "system" then "system: \(.subtype)"
        else empty end'
  return "${PIPESTATUS[0]}"
}

# last_result <field>: a field of the last result event in review.jsonl
last_result() {
  jq -rRs --arg f "$1" \
    '[split("\n")[] | fromjson? | select(.type == "result")] | last | .[$f] // empty' \
    "$out/review.jsonl"
}

wrapup=false
set +e
run_claude 20m -p "$(cat "$out/prompt.md")" --max-turns 30
status=$?
session=$(last_result session_id)
if [ "$(last_result subtype)" = error_max_turns ] && [ -n "$session" ]; then
  # out of turns without a review: resume the session and ask for the review
  # based on what was gathered so far
  echo "turn limit reached, resuming session $session to write the review"
  wrapup=true
  run_claude 5m --resume "$session" --max-turns 2 -p "You have used up your tool budget. \
Do not call any more tools. Write the review now, following the rules for your \
answer in the original instructions, based on what you have checked so far. \
Mark points you could not verify as warnings."
  status=$?
fi
set -e

last_result result > "$out/review.md"
echo "$status" > "$out/status"
subtype=$(last_result subtype)
echo "${subtype:-none}" > "$out/subtype"
echo "$wrapup" > "$out/wrapup"
echo "claude exit status $status, result ${subtype:-none}, wrap-up $wrapup"
