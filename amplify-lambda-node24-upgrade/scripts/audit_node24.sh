#!/usr/bin/env bash
# Audit an Amplify Lambda function (or whole repo) for code that the Node.js 24
# Lambda runtime (nodejs24.x) breaks or deprecates. Prints file:line hits grouped
# by issue. Read-only — fixes nothing. Each hit is a required manual review.
#
# Usage: audit_node24.sh <path>     (defaults to current directory)
#
# Companion docs: ../references/breaking-changes.md  ../references/amplify-config.md

set -euo pipefail
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

found_any=0
section() {
  local title="$1" pattern="$2" note="$3"
  local hits; hits="$(search "$pattern")"
  if [ -n "$hits" ]; then
    found_any=1
    printf '\n### %s\n%s\n' "$title" "$note"
    printf '%s\n' "$hits"
  fi
}

echo "== Node 24 Lambda upgrade audit: $ROOT =="
echo "(no changes made — review each hit against references/breaking-changes.md)"

# --- A. Lambda runtime API removals (highest priority) ---
section "[A1] Callback-style handler signature (REMOVED)" \
  '\(\s*event\s*,\s*context\s*,\s*callback\s*\)' \
  "→ Convert handler to async; return instead of callback(null,x), throw instead of callback(err)."

section "[A1] Other callback-style function signatures" \
  '\(\s*err\s*,\s*[A-Za-z_]+\s*\)\s*=>|function\s*\(\s*err\s*,' \
  "→ Possible callback patterns; promisify any callback-only deps used in the handler."

section "[A4] context.callbackWaitsForEmptyEventLoop (REMOVED)" \
  'callbackWaitsForEmptyEventLoop' \
  "→ Delete the line; ensure background work is awaited (see A2)."

section "[A3] context.succeed / fail / done (REMOVED)" \
  'context\.(succeed|fail|done)\s*\(' \
  "→ return (succeed/done-result), throw (fail/done-error) from an async handler."

# --- B. Node 24 / V8 language removals & deprecations ---
section "[B1] crypto.createCipher / createDecipher (REMOVED — throws)" \
  'createCipher\s*\(|createDecipher\s*\(' \
  "→ Migrate to createCipheriv/createDecipheriv (real refactor — wire format changes)."

section "[B2] url.parse() (runtime-deprecated — warns)" \
  '\burl\.parse\s*\(' \
  "→ Prefer new URL(); note query → URLSearchParams and absolute-URL requirement."

section "[B3] new Buffer() / SlowBuffer / tls.createSecurePair (REMOVED)" \
  'new\s+Buffer\s*\(|SlowBuffer|tls\.createSecurePair' \
  "→ Buffer.from/alloc; Buffer.allocUnsafeSlow; tls.TLSSocket. Often inside old deps."

section "[B7] AWS SDK v2 import (separate, larger migration)" \
  "require\(['\"]aws-sdk['\"]\)|from\s+['\"]aws-sdk['\"]" \
  "→ Node 24 bundles SDK v3 only. Migrate to @aws-sdk/* and bundle it yourself."

# --- Config: current runtime strings to flip ---
section "[CONFIG] Existing runtime strings (Gen 1 CloudFormation)" \
  'nodejs(18|20|22)\.x' \
  "→ Change to nodejs24.x in <name>-cloudformation-template.json."

section "[CONFIG] defineFunction runtime (Gen 2)" \
  'runtime\s*:\s*(18|20|22)\b' \
  "→ Set runtime: 24 in amplify/functions/<name>/resource.ts (or CDK escape hatch)."

section "[TOOLCHAIN] @types/node / engines pinned below 24" \
  '"@types/node"\s*:\s*"[^"]*1[0-9]|"@types/node"\s*:\s*"[^"]*2[0-3]|"node"\s*:\s*"[^"]*<\s*24' \
  "→ Bump @types/node to ^24 and engines.node to >=24."

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
