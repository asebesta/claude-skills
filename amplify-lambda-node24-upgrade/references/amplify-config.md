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
