# Node 20 → 24 breaking changes & fix patterns

Two layers of change apply when moving an Amplify Lambda from `nodejs20.x` to `nodejs24.x`:

- **A. Lambda runtime API changes** — from Lambda's new TypeScript Runtime Interface Client (RIC) in `nodejs24.x`. These break code that ran fine on `nodejs20.x`. **Highest priority.**
- **B. Node.js language / V8 changes** — Node 24 ships V8 13.6, npm 11, and removes/deprecates several APIs vs Node 20.

## Table of contents
- [A1. Callback-style handlers removed](#a1-callback-style-handlers-removed)
- [A2. Lambda no longer waits for unresolved promises](#a2-lambda-no-longer-waits-for-unresolved-promises)
- [A3. context.succeed / fail / done removed](#a3-contextsucceed--fail--done-removed)
- [A4. callbackWaitsForEmptyEventLoop removed](#a4-callbackwaitsforemptyeventloop-removed)
- [A5. Response streaming (unchanged)](#a5-response-streaming-unchanged)
- [B1. crypto.createCipher / createDecipher removed](#b1-cryptocreatecipher--createdecipher-removed)
- [B2. url.parse() runtime-deprecated](#b2-urlparse-runtime-deprecated)
- [B3. SlowBuffer / new Buffer() / tls.createSecurePair removed](#b3-slowbuffer--new-buffer--tlscreatesecurepair-removed)
- [B4. AL2023 base image (container functions only)](#b4-al2023-base-image-container-functions-only)
- [B5. ESM / require(esm) / module type](#b5-esm--requireesm--module-type)
- [B6. Toolchain: @types/node, esbuild target, engines](#b6-toolchain-typesnode-esbuild-target-engines)
- [B7. AWS SDK version](#b7-aws-sdk-version)

---

## A1. Callback-style handlers removed

The new RIC **removes the 3-argument callback signature** `handler(event, context, callback)`. There is no `callback` to invoke — calls throw `callback is not a function`, or the function hangs until timeout.

**Before (CommonJS callback):**
```js
exports.handler = (event, context, callback) => {
  doWork(event, (err, result) => {
    if (err) return callback(err);
    callback(null, { statusCode: 200, body: JSON.stringify(result) });
  });
};
```

**After (async):**
```js
exports.handler = async (event, context) => {
  const result = await doWorkAsync(event); // promisify if the dep is callback-only
  return { statusCode: 200, body: JSON.stringify(result) };
};
```

Rules:
- `callback(null, x)` → `return x`.
- `callback(err)` → `throw err` (Lambda marks the invocation failed and serializes the error).
- A callback-only dependency: wrap with `util.promisify`, or `await new Promise((resolve, reject) => fn((e, r) => e ? reject(e) : resolve(r)))`.
- ESM equivalent: `export const handler = async (event, context) => { … }`.
- A **synchronous** handler `(event, context) => result` is still valid for purely-sync work — but most handlers do I/O and should be `async`.

## A2. Lambda no longer waits for unresolved promises

On `nodejs24.x`, once the handler returns (or the response stream ends), Lambda **freezes the execution environment immediately**. It does not wait for the event loop to drain. Any promise not `await`ed may never finish — and may resume on a *later, unrelated* invocation (frozen/thawed sandbox), corrupting that invocation.

This is the most insidious change because it deploys cleanly and only manifests as **missing side-effects**: analytics events, structured logs, metric flushes, SNS/SQS/EventBridge publishes, DynamoDB/RDS writes, cache warms.

**Before (fire-and-forget — silently dropped):**
```js
exports.handler = async (event) => {
  logger.flush();                 // returns a promise, not awaited
  analytics.track('invoked');     // returns a promise, not awaited
  return respond(event);
};
```

**After:**
```js
exports.handler = async (event) => {
  const result = await respond(event);
  await Promise.all([logger.flush(), analytics.track('invoked')]); // await what must complete
  return result;
};
```

Audit every call that returns a promise and is not `await`ed / `return`ed. If completion genuinely doesn't matter, leave it but add a comment so the next reader knows it's intentional.

> Historically this was masked by `context.callbackWaitsForEmptyEventLoop = true` (the default). That property is gone (A4) and the wait behavior with it.

## A3. context.succeed / fail / done removed

Legacy terminators `context.succeed(result)`, `context.fail(error)`, `context.done(err, result)` are removed (`not a function`).

| Old | New (inside `async` handler) |
|---|---|
| `context.succeed(result)` | `return result` |
| `context.fail(error)` | `throw error` |
| `context.done(null, result)` | `return result` |
| `context.done(error)` | `throw error` |

## A4. callbackWaitsForEmptyEventLoop removed

`context.callbackWaitsForEmptyEventLoop` no longer exists. Delete any assignment to it (commonly `context.callbackWaitsForEmptyEventLoop = false`, often paired with DB connection reuse). Removing the line is safe; just ensure side-effects you care about are `await`ed (A2). Reading the property yields `undefined` — code branching on it should be removed.

## A5. Response streaming (unchanged)

`awslambda.streamifyResponse(async (event, responseStream, context) => { … responseStream.end(); })` works the same on `nodejs24.x`. Background work after `responseStream.end()` is **not** awaited — same rule as A2.

---

## B1. crypto.createCipher / createDecipher removed

`crypto.createCipher()` / `crypto.createDecipher()` (password-derived, no explicit IV) are removed and throw. Migrate to the IV-based APIs:

```js
// Before
const cipher = crypto.createCipher('aes-256-cbc', password);
// After — derive a key + random IV explicitly
const key = crypto.scryptSync(password, salt, 32);
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv); // store/transmit iv with ciphertext
```
This is a **real refactor** (the wire format changes — old ciphertext won't decrypt with the new API). Flag it to the user rather than mechanically swapping.

## B2. url.parse() runtime-deprecated

The legacy `url.parse()` still works on Node 24 but emits a `DeprecationWarning` to stderr on every call (log noise on hot paths). Prefer the WHATWG `URL`:
```js
// Before
const { hostname, pathname, query } = url.parse(input, true);
// After
const u = new URL(input);                    // requires an absolute URL or a base
const params = u.searchParams;               // replaces parsed `query`
```
Note semantic differences: `new URL()` requires an absolute URL (or a base), and `query` becomes `URLSearchParams`. Not a hard break — fix opportunistically, especially in high-volume handlers.

## B3. SlowBuffer / new Buffer() / tls.createSecurePair removed

- `SlowBuffer` is removed → use `Buffer.allocUnsafeSlow(size)`.
- `new Buffer(...)` (already deprecated) → `Buffer.from(...)` / `Buffer.alloc(...)`.
- `tls.createSecurePair` removed → use `tls.TLSSocket`.

These are rare in app code but common in older transitive deps — if a dep throws on one of these, bump the dep.

## B4. AL2023 base image (container functions only)

`nodejs24.x` is based on **Amazon Linux 2023**. Only relevant if the function is packaged as a **container image** (custom `Dockerfile` from `public.ecr.aws/lambda/nodejs:24`) — not for standard zip-based Amplify functions. In a Dockerfile, replace `yum` with `dnf`/`microdnf`, and re-verify any native binaries/`.so` deps against AL2023's glibc. Standard Amplify `defineFunction` / Gen 1 zip functions are unaffected.

## B5. ESM / require(esm) / module type

- Node 24 can `require()` synchronous ES modules, easing mixed CJS/ESM repos — generally a non-event for migration.
- If a handler file uses `import`/`export`, ensure it's resolved as ESM: package.json `"type": "module"`, a `.mjs` extension, or the bundler emits ESM. Mismatches surface as `Cannot use import statement outside a module` or `require is not defined`.
- Don't switch a working CJS function to ESM as part of a runtime bump — keep changes minimal.

## B6. Toolchain: @types/node, esbuild target, engines

Align build tooling with the runtime, or you get phantom type errors / down-leveled output:
- `@types/node` → `^24` (devDependency). The new types are what surface removed-API usage at compile time.
- esbuild / bundler `target` → `node24` (Amplify Gen 2 bundles with esbuild under the hood; for custom build steps set `--target=node24`).
- tsconfig `target`/`lib` → at least `ES2023` if currently pinned lower (so `using`, `Float16Array`, `RegExp.escape`, etc. type-check).
- `package.json` `"engines": { "node": ">=24" }` if the field exists.
- npm 11 ships with the runtime; if you pin npm in CI, verify compatibility.

## B7. AWS SDK version

`nodejs20.x` and `nodejs24.x` both bundle **AWS SDK for JavaScript v3** — no v2→v3 migration is introduced by this bump (that only applies coming from nodejs16.x or earlier). Best practice remains: **bundle your own `@aws-sdk/*` dependencies** rather than relying on the runtime-provided copy, so the SDK version is pinned and deterministic across runtime updates. If the function still imports the v2 `aws-sdk` package, that's a separate (larger) migration — call it out.
