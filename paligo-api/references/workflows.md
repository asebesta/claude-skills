# Paligo API Workflows

Worked recipes for common operations. All examples use Python + `requests`. Define once:

```python
import requests, time

BASE = "https://INSTANCE.paligoapp.com/api/v2"
AUTH = ("user@example.com", "API_KEY")

# Proactive pacing: seconds between calls per (method, resource), with ~10%
# headroom under the documented per-minute limits. Values below are for the
# BUSINESS plan — on Enterprise use reads 0.3, document writes 3.2.
# See endpoints.md "Rate limits" for the full table.
PACE = {
    ("GET", "*"): 1.3,            # show/list: 50/min
    ("PUT", "documents"): 6.5,    # update: 10/min
    ("POST", "forks"): 3.3,       # create: 20/min
    ("DELETE", "forks"): 3.3,
    ("POST", "productions"): 66,  # create: 1/min (!)
    ("POST", "imports"): 66,      # create: 1/min (!)
    ("PUT", "*"): 6.5,            # other updates: 10/min
    ("POST", "*"): 6.5,
    ("DELETE", "*"): 6.5,
}
_last = {}

def api(method, path, **kwargs):
    resource = path.strip("/").split("/")[0].split("?")[0]
    key = (method, resource) if (method, resource) in PACE else (method, "*")
    wait = PACE.get(key, 1.3) - (time.monotonic() - _last.get(key, 0))
    if wait > 0:
        time.sleep(wait)
    while True:
        _last[key] = time.monotonic()
        r = requests.request(method, f"{BASE}{path}", auth=AUTH, **kwargs)
        if r.status_code == 429:  # pacing was wrong — honor Retry-After exactly
            time.sleep(int(r.headers.get("Retry-After", "60")))
            continue
        r.raise_for_status()
        return r.json() if r.content else None
```

Rate-limit buckets are per endpoint+operation, so the per-key pacing above lets reads and writes interleave at full speed without tripping either bucket.

## Contents

- [Walk the folder tree (full library inventory)](#walk-the-folder-tree-full-library-inventory)
- [Walk a publication structure (forks)](#walk-a-publication-structure-forks)
- [Pull full text of every topic](#pull-full-text-of-every-topic)
- [Round-trip edit a single topic (the safe sequence)](#round-trip-edit-a-single-topic-the-safe-sequence)
- [Bulk edit across many topics](#bulk-edit-across-many-topics)
- [Incremental sync](#incremental-sync)
- [Translation-aware editing decisions](#translation-aware-editing-decisions)
- [Get fully resolved content (publish-time view)](#get-fully-resolved-content-publish-time-view)

## Walk the folder tree (full library inventory)

A folder's `children` is a **mixed list** of subfolders *and* documents — recurse only the `type == "folder"` entries (calling `GET /folders/{id}` on a component/publication id returns 404). Documents per folder come from `GET /documents?parent=` (paginated, authoritative — includes publications).

```python
def paginate(path, params=None):
    params = dict(params or {}, page=1, per_page=100)
    while True:
        data = api("GET", path, params=params)
        # Result array is keyed by resource name (documents/folders/forks/...),
        # NOT a generic "resources" key — pick the first array-valued key.
        items = next((v for v in data.values() if isinstance(v, list)), [])
        yield from items
        # next_page is "" (empty string) on the last page.
        if data.get("next_page", "") == "" or params["page"] >= data.get("total_pages", 1):
            break
        params["page"] += 1

def walk_tree(folder_id=None, path=""):
    """Yield (path, document_stub) for every document in the library."""
    if folder_id is None:
        folders = list(paginate("/folders"))
        # documents not in any folder:
        yield from ((path, d) for d in paginate("/documents") if not d.get("parent_resource"))
    else:
        folder = api("GET", f"/folders/{folder_id}")
        # children mixes folders + documents; recurse folders only.
        folders = [c for c in folder.get("children", []) if c.get("type") == "folder"]
        yield from ((path, d) for d in paginate("/documents", {"parent": folder_id}))
    for f in folders:
        yield from walk_tree(f["id"], f"{path}/{f['name']}")
```

Make per-folder fetches resilient: wrap `GET /folders/{id}` in try/except and record-and-skip on error rather than aborting the whole walk. A ready-to-run, paced, fault-tolerant implementation is at `scripts/walk_paligo.py` — it writes a tree + flat document inventory + a readable text outline and respects the read rate limit.

## Walk a publication structure (forks)

A publication's TOC is a fork tree. Each fork's `document.id` is the real topic.

```python
def walk_publication(pub_id, depth=0):
    for fork in paginate("/forks", {"parent": pub_id}):
        yield depth, fork["document"]["id"], fork["document"]["name"]
        yield from walk_publication(fork["id"], depth + 1)  # children hang off the fork
```

If recursion by fork id returns nothing, try `parent=document.id` — confirm parent semantics on the live instance once.

## Pull full text of every topic

```python
import json, pathlib

out = pathlib.Path("paligo_export"); out.mkdir(exist_ok=True)
for path, stub in walk_tree():
    doc = api("GET", f"/documents/{stub['id']}")      # full object incl. content
    (out / f"{doc['id']}.xml").write_text(doc["content"])
    (out / f"{doc['id']}.meta.json").write_text(json.dumps(
        {k: doc[k] for k in ("id","name","uuid","modified_at","checkout","languages")}))
```

Pacing comes from the `api()` helper (1.3s/read on Business → ~22 min per 1,000 topics).

Plain-text extraction from a topic: `"".join(el.itertext())` over the parsed XML, or per-element for structure-aware chunking (one chunk per `section`/`para` works well for RAG).

## Round-trip edit a single topic (the safe sequence)

```python
def edit_topic(doc_id, transform):
    doc = api("GET", f"/documents/{doc_id}")

    # --- pre-flight ---
    if doc["checkout"]:
        raise RuntimeError(f"{doc_id} is checked out by user {doc['checkout_user']}; skip")
    # If the instance exposes release_status on GET, gate on it here as well:
    # STATUS_RELEASED -> needs explicit decision to create a new version
    # STATUS_IN_TRANSLATION -> do not edit; edits diverge from in-flight translation
    if doc.get("languages"):
        print(f"WARNING: {doc_id} has translations {doc['languages']}; "
              f"edited segments will need re-translation")

    original = doc["content"]
    edited = transform(original)            # parse-tree edit, see xml-format.md

    # --- validate (see scripts/validate_paligo_xml.py; same checks importable) ---
    # subprocess.run([..., "compare", orig_path, edited_path], check=True)

    # --- conflict check: modified_at must be unchanged since pull ---
    fresh = api("GET", f"/documents/{doc_id}")
    if fresh["modified_at"] != doc["modified_at"]:
        raise RuntimeError(f"{doc_id} changed on server during edit; re-pull")

    api("PUT", f"/documents/{doc_id}", json={"content": edited})
```

For longer edit windows, take the lock first: `PUT {"checkout": "true"}` → edit → `PUT {"content": ..., "checkout": "false"}`. Always release the checkout in a `finally` block.

First run on any instance: do a **no-op round trip** (transform = identity) on a throwaway topic and diff GET-after vs GET-before to confirm the server doesn't mangle anything.

## Bulk edit across many topics

- Document writes are 10/min on Business (20/min Enterprise) — the `api()` helper paces this automatically. Budget ~1h50m per 1,000 topics on Business (~55 min Enterprise) and tell the user the estimate before starting.
- Process as: pull all → edit all → validate all → review (show the user a sample of diffs) → push all. Don't interleave pull/push per topic; a validation bug discovered halfway through leaves the library half-migrated.
- Keep every original XML on disk until the job is verified — it's your rollback (re-PUT the original `content`).
- Log `(doc_id, modified_at_before, pushed_at)` for every write.
- Skip, don't force: checked-out, released, and in-translation topics go to a report for human follow-up.

## Incremental sync

`GET /documents?modified_start_at={last_run_epoch}` returns only changed documents. Store the run timestamp; re-pull only those ids.

## Translation-aware editing decisions

| Situation | Action |
|-----------|--------|
| `languages` empty | Edit freely |
| Has translations, fixing a typo that doesn't change meaning | Edit; segment gets flagged for re-translation — flag to the translation manager. (In-UI Paligo has "minor change" handling; the API has no documented equivalent) |
| Has translations, substantial rewrite | Edit source, then plan a translation cycle (translationexport → translate → translationimport) |
| `release_status == STATUS_IN_TRANSLATION` | Do not edit. Wait for the cycle or coordinate with the translation manager |
| `release_status == STATUS_RELEASED` | Locked. Requires reverting to work-in-progress (creates a new version) — get explicit user sign-off before doing this via `PUT {"release_status": "STATUS_NOT_RELEASED"}` |
| Tempted to touch `xinfo:text` | Don't. Existing translation of that segment is lost (see xml-format.md) |

Releasing (`STATUS_RELEASED`) auto-approves completed translations in all languages — only set it when that's intended.

## Get fully resolved content (publish-time view)

Raw `content` has unresolved forks/variables/filters. When the *reader-facing* text is needed:

1. Create (in the Paligo UI) a publish setting for DocBook 5 or HTML output, scoped to the publication.
2. `POST /productions {"publishsetting": "<id>"}`.
3. Poll `GET /productions/{id}` until done; download the output.

DocBook export inlines reused content, applies filters, and substitutes variables — use it for search indexes/RAG over final-form documentation; use raw API content for editing workflows.
