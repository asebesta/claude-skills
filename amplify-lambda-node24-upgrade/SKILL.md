---
name: amplify-lambda-node24-upgrade
description: Upgrade an AWS Amplify backend Lambda function from the Node.js 20 runtime (nodejs20.x) to Node.js 24 (nodejs24.x), including the runtime config change AND the source-code fixes the new runtime requires. Use when a user wants to migrate, bump, or upgrade an Amplify (Gen 1 or Gen 2) Lambda function — or a whole Amplify backend — from Node 20 (or 18/22) to Node 24, or asks why a function broke after moving to nodejs24.x. Covers locating the runtime setting in Amplify Gen 1 (cloudformation-template.json) and Gen 2 (defineFunction runtime / CDK escape hatch), the removed callback-style handler API, the removed context.callbackWaitsForEmptyEventLoop / context.succeed/fail/done, the "Lambda no longer waits for unresolved promises" behavior change, and Node 20→24 language/V8 breaking changes (crypto.createCipher, url.parse, SlowBuffer, AL2023 base image, @types/node, esbuild target). Triggers on Amplify + Lambda + Node 20/24, nodejs24.x, defineFunction runtime, or "callback handler stopped working after Node 24".
---

# Amplify Lambda: Node 20 → Node 24 Upgrade

Upgrade an AWS Amplify backend Lambda function from `nodejs20.x` to `nodejs24.x`. A correct upgrade is **two parts**: (1) flip the runtime in the Amplify config, and (2) fix the source code, because the Node 24 Lambda runtime ships a new Runtime Interface Client that **removes the callback-style handler API** and **no longer waits for unresolved promises**. Skipping part 2 produces functions that deploy fine but fail or silently drop work at invocation time.

Run this process **per function**. A repo may contain many functions in different states; do not assume they are uniform.

## Workflow

1. **Detect the Amplify generation and locate the runtime setting** — see [references/amplify-config.md](references/amplify-config.md). Confirm the function is actually on Node 20 (or 18/22) before changing anything.
2. **Audit the handler source for breaking changes** *before* flipping the runtime, so you know the blast radius. Run the audit script:
   ```bash
   scripts/audit_node24.sh <path-to-function-or-repo>
   ```
   It greps for every pattern the new runtime breaks and prints file:line hits. Treat each hit as a required code review, not an auto-fix.
3. **Flip the runtime and shared toolchain — centrally, once.** Do these in the orchestrator (not delegated), because they touch shared files and config that parallel fixers would clobber:
   - Flip the runtime to Node 24 in the Amplify config (Gen 1 or Gen 2 — see amplify-config.md). For Gen 2 this is `runtime: 24`; it is natively supported, so **upgrade `@aws-amplify/backend` rather than dropping to the CDK escape hatch**.
   - `package.json` → `"engines": { "node": ">=24" }` if present; `@types/node` → `^24` (dev dependency); esbuild/bundler `target` → `node24` (or `es2023`+); tsconfig `target`/`lib` if it pins an older version.
4. **Fix each function's source by delegating to a subagent** — don't hand-edit handler code inline. For each function, fill the brief in [references/fix-brief.md](references/fix-brief.md) with that function's directory, its audit hits, and the absolute path to breaking-changes.md, then spawn a subagent (general-purpose) with the filled brief. Each subagent fixes only its own function dir and returns a structured report. The two changes that break the most real Amplify functions, and that the brief makes the subagent hunt for:
   - **Callback-style handlers** → convert to `async`.
   - **Fire-and-forget promises** (logging, metrics, analytics, DynamoDB writes not `await`ed) → `await` them, because Lambda no longer drains the event loop. This one isn't greppable — it requires reading the handler, which is why a focused subagent does it well.

   For a repo with **many** functions and the user opted into orchestration, use the Workflow pipeline variant in fix-brief.md (audit → fix per function, no barrier). Otherwise spawn subagents directly with the Agent tool. Aggregate every report's `verify` and `unresolved` items for the user.
5. **Build and test locally**, then deploy:
   - Gen 2: `npx ampx sandbox` (or the pipeline) — watch for type errors from the new `@types/node`.
   - Gen 1: `amplify push`.
   - Invoke the function (real event or `ampx sandbox` / `amplify mock function`) and confirm any background work (writes, logs, metrics) actually completes — this is where the "no longer waits for promises" change bites and tests must explicitly cover it.
6. **Report** what changed and what the user must verify — fold in every subagent report's `verify` and `unresolved` items (especially async side-effects and any `crypto.createCipher` / `url.parse` usages that need real refactoring).

## Report-only mode (audit any repo, change nothing)

When the goal is just to assess a repo's Node-24 readiness — not to upgrade it — run the audit in report mode and stop:

```bash
scripts/audit_node24.sh --report <repo-path>
```

This makes **zero changes** and spawns **no fixer**. It prints a consolidated rollup — Amplify generation(s) detected, function counts, current runtime inventory (how many on 20 vs 18/22 vs already 24), per-category finding counts, and a verdict — followed by the file:line details. Use it to triage many repos, attach to a ticket/PR, or decide which functions are worth upgrading. To actually upgrade, switch to the full workflow above (steps 3–6); do **not** run the fixer in this mode.

## The non-negotiable breaking changes (Node 24 Lambda)

These come from the new runtime, independent of language version. Full detail + fix patterns in [references/breaking-changes.md](references/breaking-changes.md).

| Removed / changed | Symptom | Fix |
|---|---|---|
| `handler(event, context, callback)` callback signature | `callback is not a function` / function hangs to timeout | Convert to `async (event, context) => { return result }`; `throw` instead of `callback(err)` |
| `context.callbackWaitsForEmptyEventLoop` | Property gone; background work dropped | Remove the line; `await` all async side-effects |
| `context.succeed()` / `context.fail()` / `context.done()` | `not a function` | `return` / `throw` from an async handler |
| Lambda **no longer waits for unresolved promises** | Logs/metrics/DB writes silently missing | `await` every promise whose completion matters before returning |

Response streaming (`awslambda.streamifyResponse(async (event, responseStream, context) => …)`) is unchanged.

## Notes for running across many repos

- **Never blanket-replace.** Changing the runtime string is safe; rewriting handlers is not. Audit first, fix deliberately.
- A function can be **Gen 1 and Gen 2 in the same monorepo** — detect per function (amplify-config.md explains the tells).
- `defineFunction({ runtime: 24 })` is natively supported (`NodeVersion = 18 | 20 | 22 | 24`) on `@aws-amplify/backend-function ≥ 1.17.0`. If `24` is rejected, **upgrade `@aws-amplify/backend` + `@aws-amplify/backend-cli`** — that's the fix, not the CDK escape hatch (which is reserved for custom CDK functions). Never silently downgrade the target.
- ESM/CommonJS, OpenSSL, and AL2023 base-image (`yum`→`dnf`) concerns only matter for container-image functions or functions that pin module type — covered in breaking-changes.md.
