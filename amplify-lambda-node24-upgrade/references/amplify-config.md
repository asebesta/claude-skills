# Locating & changing the Amplify Lambda runtime

First decide **Gen 1 vs Gen 2**, then change the runtime in the right place. Both can coexist in one monorepo — check per function.

## Detecting the generation

| Tell | Generation |
|---|---|
| `amplify/backend/function/<name>/` with a `*-cloudformation-template.json` | **Gen 1** |
| `amplify/backend.ts` and `amplify/functions/<name>/resource.ts` using `defineFunction` | **Gen 2** |
| `amplify/team-provider-info.json`, `amplify/cli.json` present | Gen 1 |
| `@aws-amplify/backend` in `package.json`, `ampx` scripts | Gen 2 |

Quick probe:
```bash
ls amplify/backend.ts 2>/dev/null && echo "Gen 2"
ls amplify/backend/ 2>/dev/null && echo "Gen 1"
grep -rl "defineFunction" amplify 2>/dev/null   # Gen 2 functions
```

---

## Gen 2 — `defineFunction({ runtime })`

The runtime is a **number** (the Node major version) in `amplify/functions/<name>/resource.ts`:

```ts
import { defineFunction } from '@aws-amplify/backend';

export const myFn = defineFunction({
  name: 'my-fn',
  entry: './handler.ts',
  runtime: 24,        // ← was 20; Node major version as a number → nodejs24.x
});
```

**`runtime: 24` is a first-class, supported value — prefer it and do not reach for the CDK escape hatch.** The accepted type is:
```ts
type NodeVersion = 18 | 20 | 22 | 24;   // defineFunction's runtime
```
which maps internally to `Runtime.NODEJS_24_X` (`nodejs24.x`). The only reason `24` would be rejected is an outdated dependency, which is fixable by upgrading — not by escaping to CDK.

**Version requirements (the actual gate):**
- `@aws-amplify/backend-function` **≥ 1.17.0** — the release that added `24` to the `NodeVersion` union (it also moved the default from "oldest LTS" to **22**). This is a transitive dep of `@aws-amplify/backend`.
- `aws-cdk-lib` **≥ 2.225.0** — the release that added `Runtime.NODEJS_24_X`.

**Check before editing, then fix by upgrading (not escaping):**
```bash
npm ls @aws-amplify/backend-function aws-cdk-lib    # see resolved versions
# if either is too old:
npm i @aws-amplify/backend@latest @aws-amplify/backend-cli@latest
```
A type error on `runtime: 24` means "upgrade the package," full stop. Don't silently downgrade the target or hand-roll the runtime.

Other notes:
- Default when omitted is **22** on current versions (historically the oldest supported LTS) — so a function with no `runtime` is *not* necessarily on 20. Set `runtime: 24` explicitly.
- Gen 2 bundles with esbuild internally; still set `@types/node@^24` and any custom esbuild `target` (see breaking-changes.md B6).
- Historical gotcha (now resolved): early `aws-cdk-lib` 2.224–2.225 could fail bundling a `NodejsFunction` by trying to pull a not-yet-published `sam/build-nodejs24.x` image. If a bundle step fails fetching that image, update `aws-cdk-lib` to a current version — it exists now.

### Deployer 2.x ESM module scoping (breaks synth after the package upgrade)

`@aws-amplify/backend-deployer` 2.x (pulled in by `@aws-amplify/backend` ≥ ~1.23) loads `amplify/backend.ts` in-process via tsx's `tsImport` API instead of shelling out. Node/tsx module-scope every file by the **nearest `package.json`**, so a function dir that has its own `package.json` (a documented pattern for per-function dependencies) but no `"type"` field makes its `resource.ts` CommonJS — and its named exports become invisible to the ESM `backend.ts`. Synth then fails with:

```
[SyntaxError] The requested module './<fn>/resource' does not provide an export named '<name>'
```

Two things to know about this error:
- It surfaces on the **deepest module-graph edge first**, so the dir it names may not be the only one affected — audit **every** function dir that has its own `package.json`.
- `tsc --noEmit` passes; only synth (module execution) catches it.

**Fix (do it for all affected dirs in one pass):**
1. Add `"type": "module"` to each function dir's `package.json` (this matches what current Gen 2 scaffolding generates).
2. Rename any CommonJS `jest.config.js` in those dirs to `jest.config.cjs` (jest auto-discovers `.cjs`; after the rescope, a `.js` config using `module.exports` throws `module is not defined in ES module scope`). Then re-run the tests — jest treats `.ts` files per `extensionsToTreatAsEsm`, not per package.json `type`, so ts-jest suites are otherwise unaffected.

**Local repro without AWS credentials:** `npx tsx amplify/backend.ts` from the project root. Module-scoping errors surface immediately; success looks like failing *only* with `No context value present for amplify-backend-namespace key` (the CDK context that `ampx` normally injects).

### Build machine Node version (separate from the Lambda runtime)

`runtime: 24` changes what the **deployed functions** run on — not what the **Amplify CI build** runs on. The build machine's Node comes from, in ascending precedence:
1. The build image default.
2. The Amplify console live-package override (an app environment variable named `_LIVE_UPDATES`, e.g. `[{"pkg":"node","type":"nvm","version":"20"}]`) — console-side, invisible in the repo.
3. Commands in the build spec itself — a repo-root `amplify.yml` overrides the console build spec, and an `nvm` call in it overrides `_LIVE_UPDATES`.

To pin the build to Node 24 from the repo (works even without console access), put this first in **both** `backend.phases.preBuild` and `frontend.phases.preBuild` (backend and frontend phases run in one shell for fullstack builds, but frontend-only rebuilds exist):

```yaml
- nvm install 24 && nvm use 24
- node -v && npm -v
```

If you rely on the console override instead, remember someone with console access must update `_LIVE_UPDATES` — and until then the build synthesizes/bundles on old Node while deploying `nodejs24.x` functions.

### CDK escape hatch — last resort only

Only needed for a **custom CDK function** (defined directly with `aws-cdk-lib/aws-lambda`'s `Function`, not `defineFunction`), or a genuinely un-upgradable pinned dependency. For a standard `defineFunction`, use `runtime: 24` instead of this.

```ts
// Custom CDK Function — set runtime directly in its props:
import { Runtime } from 'aws-cdk-lib/aws-lambda';
new Function(stack, 'MyFn', { runtime: Runtime.NODEJS_24_X, /* … */ });

// Override on a defineFunction resource (avoid unless runtime: 24 is truly unavailable):
const cfnFn = backend.myFn.resources.lambda.node.defaultChild as
  import('aws-cdk-lib/aws-lambda').CfnFunction;
cfnFn.runtime = Runtime.NODEJS_24_X.name; // 'nodejs24.x'
```

---

## Gen 1 — CloudFormation template

The runtime lives in the function's CloudFormation template:

```
amplify/backend/function/<name>/<name>-cloudformation-template.json
```

Find the `Runtime` property on the Lambda resource and change it:

```json
"Resources": {
  "LambdaFunction": {
    "Type": "AWS::Lambda::Function",
    "Properties": {
      "Runtime": "nodejs24.x"   // ← was "nodejs20.x"
    }
  }
}
```

Then:
- If a `amplify/backend/function/<name>/src/package.json` has an `"engines"` field, bump it to `>=24`.
- Run `amplify push` to deploy. (`amplify update function` may rewrite the template; editing the JSON directly is reliable for a runtime bump.)
- Some Gen 1 functions are written as Lambda **layers** or use a `parameters.json`; the `Runtime` string is still the CloudFormation property to change.

---

## After changing the runtime (both gens)

The config change alone is insufficient — apply the source-code fixes in [breaking-changes.md](breaking-changes.md) (callback handlers, unresolved promises, removed `context.*`). Deploy, then invoke and confirm background side-effects complete.
