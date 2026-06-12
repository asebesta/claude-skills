# Paligo API Workflows

Worked recipes for common operations. All examples use Python + `requests`. Define once:

```python
import requests, time

BASE = "https://INSTANCE.paligoapp.com/api/v2"
AUTH = ("user@example.com", "API_KEY")

def api(method, path, **kwargs):
    while True:
        r = requests.request(method, f"{BASE}{path}", auth=AUTH, **kwargs)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "30")))
            continue
        r.raise_for_status()
        return r.json() if r.content else None
```

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

Folders list subfolders only; documents per folder come from `GET /documents?parent=`.

```python
def paginate(path, params=None):
    params = dict(params or {}, page=1, per_page=100)
    while True:
        data = api("GET", path, params=params)
        yield from data.get("resources", [])
        if params["page"] >= data.get("total_pages", 1):
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
        folders = folder.get("children", [])
        yield from ((path, d) for d in paginate("/documents", {"parent": folder_id}))
    for f in folders:
        yield from walk_tree(f["id"], f"{path}/{f['name']}")
```

Verify the root-level behavior (`/folders` response shape, unfiled documents) against the live instance — adjust if the instance returns a wrapper object.

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
    time.sleep(1.3)   # ~46/min, under the 50/min Business read limit
```

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

- Write limit is ~10/min (Business): sleep ≥6s between PUTs, and expect a 1,000-topic job to take ~2h.
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
