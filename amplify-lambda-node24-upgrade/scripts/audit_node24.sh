#!/usr/bin/env bash
# Audit an Amplify Lambda function (or whole repo) for code that the Node.js 24
# Lambda runtime (nodejs24.x) breaks or deprecates. Prints file:line hits grouped
# by issue. ALWAYS read-only — fixes nothing. Each hit is a required manual review.
#
# Usage:
#   audit_node24.sh <path>              Detail hits (default; used by the fix workflow)
#   audit_node24.sh --report <path>     Report-only repo audit: a consolidated rollup
#                                       (generation + runtime inventory + issue counts +
#                                       verdict) followed by detail. Changes nothing —
#                                       does NOT trigger any fixing. Good for "just
#                                       audit this repo". <path> defaults to "."
#
# Companion docs: ../references/breaking-changes.md  ../references/amplify-config.md

set -euo pipefail

REPORT=0
case "${1:-}" in
  -r|--report) REPORT=1; shift ;;
esac
ROOT="${1:-.}"

if [ ! -e "$ROOT" ]; then
  echo "error: path not found: $ROOT" >&2
  exit 2
fi

# Prefer ripgrep; fall back to grep -rn. Both skip node_modules/dist/.git/build.
if command -v rg >/dev/null 2>&1; then
  search() { rg -n --no-heading \
      -g '!node_modules' -g '!dist' -g '!build' -g '!.git' -g '!*.min.js' \
      -g '*.js' -g '*.mjs' -g '*.cjs' -g '*.ts' -g '*.json' \
      -e "$1" "$ROOT" 2>/dev/null || true; }
else
  search() { grep -rnE \
      --include='*.js' --include='*.mjs' --include='*.cjs' --include='*.ts' --include='*.json' \
      --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=.git \
      "$1" "$ROOT" 2>/dev/null || true; }
fi

count_lines() { [ -z "$1" ] && echo 0 || { printf '%s\n' "$1" | grep -c . || true; }; }

found_any=0
issue_total=0
summary=""   # newline-accumulated "  [TAG] title — N"

# section <tag-is-issue:0|1> <title> <pattern> <note>
section() {
  local is_issue="$1" title="$2" pattern="$3" note="$4"
  local hits n; hits="$(search "$pattern")"; n="$(count_lines "$hits")"
  if [ "$n" -gt 0 ]; then
    found_any=1
    [ "$is_issue" = "1" ] && issue_total=$((issue_total + n))
    summary="${summary}  ${title} — ${n}"$'\n'
    DETAILS="${DETAILS}"$'\n'"### ${title}"$'\n'"${note}"$'\n'"${hits}"$'\n'
  fi
}

DETAILS=""

# --- A. Lambda runtime API removals (highest priority) ---
section 1 "[A1] Callback-style handler signature (REMOVED)" \
  '\(\s*event\s*,\s*context\s*,\s*callback\s*\)' \
  "→ Convert handler to async; return instead of callback(null,x), throw instead of callback(err)."

section 1 "[A1] Other callback-style function signatures" \
  '\(\s*err\s*,\s*[A-Za-z_]+\s*\)\s*=>|function\s*\(\s*err\s*,' \
  "→ Possible callback patterns; promisify any callback-only deps used in the handler."

section 1 "[A4] context.callbackWaitsForEmptyEventLoop (REMOVED)" \
  'callbackWaitsForEmptyEventLoop' \
  "→ Delete the line; ensure background work is awaited (see A2)."

section 1 "[A3] context.succeed / fail / done (REMOVED)" \
  'context\.(succeed|fail|done)\s*\(' \
  "→ return (succeed/done-result), throw (fail/done-error) from an async handler."

# --- B. Node 24 / V8 language removals & deprecations ---
section 1 "[B1] crypto.createCipher / createDecipher (REMOVED — throws)" \
  'createCipher\s*\(|createDecipher\s*\(' \
  "→ Migrate to createCipheriv/createDecipheriv (real refactor — wire format changes)."

section 1 "[B2] url.parse() (runtime-deprecated — warns)" \
  '\burl\.parse\s*\(' \
  "→ Prefer new URL(); note query → URLSearchParams and absolute-URL requirement."

section 1 "[B3] new Buffer() / SlowBuffer / tls.createSecurePair (REMOVED)" \
  'new\s+Buffer\s*\(|SlowBuffer|tls\.createSecurePair' \
  "→ Buffer.from/alloc; Buffer.allocUnsafeSlow; tls.TLSSocket. Often inside old deps."

section 1 "[B7] AWS SDK v2 import (separate, larger migration)" \
  "require\(['\"]aws-sdk['\"]\)|from\s+['\"]aws-sdk['\"]" \
  "→ Node 24 bundles SDK v3 only. Migrate to @aws-sdk/* and bundle it yourself."

# --- Config: current runtime strings to flip (informational, not counted as code issues) ---
section 0 "[CONFIG] Existing runtime strings (Gen 1 CloudFormation)" \
  'nodejs(18|20|22)\.x' \
  "→ Change to nodejs24.x in <name>-cloudformation-template.json."

section 0 "[CONFIG] defineFunction runtime (Gen 2)" \
  'runtime\s*:\s*(18|20|22)\b' \
  "→ Set runtime: 24 in amplify/functions/<name>/resource.ts."

section 0 "[TOOLCHAIN] @types/node / engines pinned below 24" \
  '"@types/node"\s*:\s*"[^"]*1[0-9]|"@types/node"\s*:\s*"[^"]*2[0-3]|"node"\s*:\s*"[^"]*<\s*24' \
  "→ Bump @types/node to ^24 and engines.node to >=24."

# [CONFIG] Gen 2 function dirs whose own package.json lacks "type": "module".
# The runtime-24-capable @aws-amplify/backend ships a deployer that loads
# backend.ts as real ESM (tsx tsImport); a typeless package.json CJS-scopes that
# dir's resource.ts, hiding its named exports and failing synth with
# "does not provide an export named ...". Absence check, so not a section() grep.
if ls "$ROOT"/amplify/backend.ts >/dev/null 2>&1; then
  esm_hits=""
  while IFS= read -r pj; do
    grep -q '"type"[[:space:]]*:[[:space:]]*"module"' "$pj" 2>/dev/null || esm_hits="${esm_hits}${pj}: missing \"type\": \"module\""$'\n'
  done < <(find "$ROOT/amplify" -mindepth 2 -maxdepth 4 -name package.json -not -path '*/node_modules/*' 2>/dev/null)
  esm_hits="${esm_hits%$'\n'}"
  n_esm="$(count_lines "$esm_hits")"
  if [ "$n_esm" -gt 0 ]; then
    found_any=1
    summary="${summary}  [CONFIG] Function package.json without type:module (Gen 2 deployer ESM) — ${n_esm}"$'\n'
    DETAILS="${DETAILS}"$'\n'"### [CONFIG] Function package.json without \"type\": \"module\" (Gen 2 deployer ESM)"$'\n'"→ Add \"type\": \"module\" (and rename any CJS jest.config.js → jest.config.cjs) before upgrading @aws-amplify/backend — see amplify-config.md 'Deployer 2.x ESM module scoping'."$'\n'"${esm_hits}"$'\n'
  fi
fi

# ---------------------------------------------------------------------------
# Report-only rollup
# ---------------------------------------------------------------------------
if [ "$REPORT" = "1" ]; then
  # Generation detection + function discovery (read-only).
  gen1_n="$(find "$ROOT" -path '*/amplify/backend/function/*-cloudformation-template.json' \
            -not -path '*/node_modules/*' 2>/dev/null | wc -l | tr -d ' ')"
  gen2_files="$(search 'defineFunction' | cut -d: -f1 | sort -u)"
  gen2_n="$(count_lines "$gen2_files")"
  rt_20="$(count_lines "$(search 'nodejs20\.x|runtime\s*:\s*20\b')")"
  rt_18_22="$(count_lines "$(search 'nodejs(18|22)\.x|runtime\s*:\s*(18|22)\b')")"
  rt_24="$(count_lines "$(search 'nodejs24\.x|runtime\s*:\s*24\b')")"

  gens=""
  [ "$gen1_n" -gt 0 ] && gens="Gen 1"
  [ "$gen2_n" -gt 0 ] && gens="${gens:+$gens + }Gen 2"
  [ -z "$gens" ] && gens="none detected (is this an Amplify repo?)"

  echo "================================================================"
  echo " Node 24 Lambda upgrade — REPORT-ONLY AUDIT (no files changed)"
  echo " Path: $ROOT"
  echo "================================================================"
  echo
  echo "## Summary"
  echo "Amplify generation:   $gens"
  echo "Functions discovered: Gen 1 = $gen1_n, Gen 2 = $gen2_n"
  echo "Runtime inventory:    on 20 = $rt_20, on 18/22 = $rt_18_22, already on 24 = $rt_24"
  echo "Code findings (A/B):  $issue_total total"
  if [ -n "$summary" ]; then
    echo "By category:"
    printf '%s' "$summary"
  fi
  echo
  if [ "$issue_total" -gt 0 ]; then
    echo "Verdict: NEEDS CODE FIXES — $issue_total greppable finding(s) before this repo is Node-24-safe."
  else
    echo "Verdict: no greppable code findings. Still REQUIRES the manual [A2] review below."
  fi
  echo
  echo "## Manual review required (not greppable)"
  echo "[A2] Fire-and-forget promises: Lambda no longer drains the event loop."
  echo "     Inspect each handler for promises NOT awaited/returned — logging.flush(),"
  echo "     analytics/metrics, SNS/SQS/EventBridge publishes, DynamoDB/RDS writes."
  echo
  echo "## Details"
  if [ "$found_any" = "1" ]; then printf '%s\n' "$DETAILS"; else echo "(no greppable patterns)"; fi
  echo
  echo "Report-only: this command makes NO changes and does NOT run any fixer."
  echo "To fix, follow the SKILL.md workflow (audit → flip runtime → delegate fixes)."
  exit 0
fi

# ---------------------------------------------------------------------------
# Default (detail) mode — used by the per-function fix workflow
# ---------------------------------------------------------------------------
echo "== Node 24 Lambda upgrade audit: $ROOT =="
echo "(no changes made — review each hit against references/breaking-changes.md)"
if [ "$found_any" = "1" ]; then printf '%s\n' "$DETAILS"; fi

echo ""
echo "== Manual review required (not greppable) =="
echo "[A2] Fire-and-forget promises: Lambda no longer drains the event loop."
echo "     Inspect the handler for promises that are NOT awaited/returned —"
echo "     logging.flush(), analytics/metrics, SNS/SQS/EventBridge publishes,"
echo "     DynamoDB/RDS writes. Await everything whose completion matters."

if [ "$found_any" -eq 0 ]; then
  echo ""
  echo "No greppable breaking patterns found. Still review [A2] manually and confirm the runtime string is flipped to nodejs24.x / runtime: 24."
fi
