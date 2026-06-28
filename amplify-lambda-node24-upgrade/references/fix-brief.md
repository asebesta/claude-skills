# Fix brief — hand this to a per-function fix subagent

This is a **template the orchestrator fills in and passes to a subagent** (one subagent per function). It packages the requisite info so the subagent can fix one function's source without re-reading the whole skill or guessing scope. The fixes are judgment calls — the brief gives the subagent the rules and guardrails, not a find-and-replace script.

## Why delegate instead of fixing inline

- **Isolation of context.** Each function's audit hits, handler code, and verification notes stay in their own agent — the orchestrator keeps only the structured report, not every file dump.
- **Scope safety across a repo.** The orchestrator owns shared files (root `package.json`, `amplify/backend.ts`) and config flips; each subagent touches only its function's source. This prevents parallel agents from clobbering each other's edits to shared files.
- **Parallelism.** Many functions → many subagents (or a Workflow pipeline) at once.

## How the orchestrator uses it

1. Do the **shared/config work once, centrally** (don't delegate these): flip the runtime (`runtime: 24` / `nodejs24.x`), bump `@types/node@^24`, `engines.node`, esbuild `target`, and verify `@aws-amplify/backend-function ≥ 1.17.0` (see amplify-config.md).
2. For each function, fill the placeholders below and spawn a subagent (general-purpose) with the filled brief as its prompt. Pass the **absolute path** to `breaking-changes.md` so the subagent reads the full catalog.
3. Collect each subagent's structured report; aggregate the `verify` and `unresolved` items into the final summary to the user.

---

## Brief template (fill the `{{…}}` placeholders, then send as the subagent prompt)

> **Task: migrate one AWS Amplify Lambda's source for the Node.js 24 runtime.**
>
> You are fixing the source code of a single Lambda function so it runs correctly on the `nodejs24.x` runtime. The runtime/config and shared toolchain files have already been updated by the orchestrator — **do not edit** `{{REPO_ROOT}}/package.json`, `{{AMPLIFY_BACKEND_TS}}`, or any file outside the function directory. Scope every edit to:
>
> - Function directory: `{{FUNCTION_DIR}}`
> - Amplify generation: `{{GEN}}` (Gen 1 / Gen 2)
>
> **Read first:** the complete breaking-changes catalog at `{{BREAKING_CHANGES_ABS_PATH}}`. It has the before→after fix patterns for every item below.
>
> **Audit hits already found in this function** (each is a required review, line numbers may shift as you edit):
> ```
> {{AUDIT_OUTPUT_FOR_THIS_FUNCTION}}
> ```
>
> **Apply these fixes, preserving existing behavior:**
> 1. **Callback handlers** → convert `handler(event, context, callback)` to `async (event, context)`. `callback(null, x)` → `return x`; `callback(err)` → `throw err`. Promisify any callback-only dependency the handler awaits.
> 2. **Unresolved promises (most important, not greppable)** — read the handler end-to-end and find every promise that is NOT awaited or returned: logging/flush, analytics/metrics, SNS/SQS/EventBridge publishes, DynamoDB/RDS writes, cache warms. `await` everything whose completion matters; Lambda no longer drains the event loop, so unawaited work is silently dropped. If a fire-and-forget is genuinely intentional, leave it and add a one-line comment saying so.
> 3. **Removed `context` APIs** — delete `context.callbackWaitsForEmptyEventLoop = …`; replace `context.succeed(x)`→`return x`, `context.fail(e)`→`throw e`, `context.done(e,x)`→`throw e`/`return x`.
> 4. **Removed/deprecated Node APIs** — `crypto.createCipher`/`createDecipher` (DO NOT mechanically swap — the wire format changes; flag as unresolved with a proposed `createCipheriv` approach), `new Buffer()`→`Buffer.from`/`alloc`, `SlowBuffer`, `tls.createSecurePair`, and `url.parse()`→`new URL()` where low-risk.
>
> **Guardrails:**
> - Make the **minimum** change that satisfies each rule. Do not refactor unrelated code, reformat, or "modernize" beyond what the runtime requires.
> - Do not change the handler's public contract (event shape in, response shape out).
> - If a fix requires a behavioral decision you can't make safely (e.g. encryption format, whether a side-effect must block the response), DON'T guess — record it under `unresolved`.
> - After editing, run the function's typecheck/build if one exists (`tsc --noEmit`, the package's build script, or `npx ampx sandbox` is too heavy — prefer typecheck). Report the result; do not deploy.
>
> **Return ONLY this report (no prose preamble):**
> ```
> function: {{FUNCTION_DIR}}
> changes:
>   - file: <path>  rule: <A1|A2|A3|A4|B1|B2|B3>  summary: <what changed, one line>
> unresolved:        # decisions for a human — empty list if none
>   - file: <path>  issue: <why it needs a human>  proposal: <suggested fix>
> verify:            # what the user must confirm at runtime
>   - <side-effect / behavior to test, e.g. "analytics.track now awaited — confirm events still emit">
> build: <pass | fail: summary | not-run: reason>
> ```

---

## Many functions: Workflow variant

When a repo has many functions and the user has opted into orchestration, pipeline the work instead of spawning agents one by one. Audit and fix flow per-function with no barrier; shared/config edits stay in the orchestrator before the pipeline runs.

```js
// sketch — fill auditOutput per function from scripts/audit_node24.sh
const reports = await pipeline(
  functionDirs,
  dir => agent(auditPromptFor(dir), { label: `audit:${dir}`, phase: 'Audit', schema: AUDIT_SCHEMA }),
  (audit, dir) => agent(fillBrief(dir, audit), { label: `fix:${dir}`, phase: 'Fix', schema: REPORT_SCHEMA }),
);
// orchestrator aggregates reports[].verify and reports[].unresolved for the user
```

Worktree isolation is NOT needed: each subagent edits only its own function directory, and the orchestrator already handled the shared files.
