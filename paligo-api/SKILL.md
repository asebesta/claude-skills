---
name: paligo-api
description: Paligo CCMS REST API (v2) integration reference covering the entire API surface. Use when writing code that interacts with the Paligo API for ANY resource — documents/topics/publications, folders, forks, images, search, imports, productions/publishing, publish settings, translation export/import, taxonomies, variables (sets/variants/values), groups, users, and assignments. Includes the content round-trip workflow (walk the tree, pull topic XML, edit DocBook XML, validate, push back), publishing, translation round-trips, asset and metadata management, plus auth, pagination, rate limits, checkout/release-status/versioning rules. Triggers on Paligo, paligoapp.com, api.paligo.net, Paligo topics/publications/forks, or any CCMS content/publishing/translation API task.
---

# Paligo REST API

Reference for integrating with the **Paligo CCMS REST API (v2)**. Paligo stores structured documentation as reusable components (topics) in a DocBook 5.x–based XML format. The API covers content (documents, folders, forks), assets (images), discovery (search), ingestion (imports), publishing (productions, publish settings, outputs), localization (translation export/import), metadata (taxonomies, variables), and administration (groups, users, assignments). The flagship workflow is the content round trip: enumerate content, pull topic XML, edit it, validate, and push it back.

**For any endpoint, object shape, query parameter, or enum, [references/endpoints.md](references/endpoints.md) is the complete catalog of every resource the API exposes** — start there when the task isn't a content edit (e.g. publishing, translations, users, taxonomies, variables, images).

## Base URL and Authentication

```
https://{instance}.paligoapp.com/api/v2
```

`{instance}` is the customer's Paligo instance name. Authentication is HTTP Basic: `username:apikey` Base64-encoded. The API key is generated per-user in Paligo (user settings → API). **The user account must have admin privileges.**

```bash
curl -u "user@example.com:API_KEY" "https://example.paligoapp.com/api/v2/documents/123"
```

All requests/responses are JSON. Timestamps are Unix epoch integers.

## Core Concepts

| Concept | Meaning |
|---------|---------|
| **Document** | Any content component: topics, publications. `GET /documents/{id}` returns full XML in the `content` field |
| **Folder** | Organizational tree in the Content Manager. Folder children list subfolders only; use `GET /documents?parent={folderId}` to list documents in a folder |
| **Fork** | A reuse reference ("symbolic link") placing a document inside a publication/structure. Forks are NOT resolved inline in `content` — walk them explicitly |
| **Checkout** | Lock state on a document. Check `checkout == false` before editing; a checked-out doc is being edited by someone |
| **Release status** | Workflow state. `STATUS_RELEASED` content is locked/archived — must return to work-in-progress (creates a new version) before editing |
| **Languages** | `languages` array lists translation locales. `content` is the source language. Translations are managed via translation export/import, not direct PUT |

## The Round-Trip Workflow (pull → edit → validate → push)

This is the core workflow. Full detail and code in [references/workflows.md](references/workflows.md).

1. **Walk the tree** — enumerate folders (`GET /folders`), list documents per folder (`GET /documents?parent=`), or walk a publication's structure via `GET /forks?parent=`. A folder's `children` mixes subfolders *and* documents — recurse only `type == "folder"`. For a full inventory snapshot, run `scripts/walk_paligo.py` (paced, fault-tolerant; writes tree + flat doc list + readable outline).
2. **Pull** — `GET /documents/{id}`; save the original `content` XML and `modified_at` verbatim (needed for validation and conflict detection).
3. **Pre-flight checks** — refuse to edit if `checkout` is true (someone else is editing), `release_status` is `STATUS_RELEASED` (locked; needs a new version) or `STATUS_IN_TRANSLATION` (edits will diverge from in-flight translation). If `languages` has entries, warn: text edits invalidate existing translations for changed segments.
4. **Edit** — operate on the XML tree, never on the string. **Never add, remove, or modify `xinfo:*` attributes or `xml:id`/`id` attributes** — these are Paligo-managed identifiers binding elements to reuse and translation memory. See [references/xml-format.md](references/xml-format.md) for the format and editing rules.
5. **Validate** — run `scripts/validate_paligo_xml.py compare original.xml edited.xml` to verify well-formedness and that all Paligo identifiers survived the edit. See [Validation](#validation) below.
6. **Push** — re-check `modified_at` hasn't changed (no ETags/If-Match exist; this is the only conflict detection available), then `PUT /documents/{id}` with `{"content": "<edited xml>"}`.

Before the first real edit on any instance, run a **no-op round trip** on a throwaway topic: GET → PUT the content back unchanged → GET again → confirm the XML is semantically identical. This verifies the instance round-trips cleanly before touching real content.

## Validation

There is no documented server-side schema validation on PUT — malformed pushes are your problem. Validate locally before every push:

```bash
# Well-formedness only
python3 scripts/validate_paligo_xml.py check edited.xml

# Full pre-push validation: well-formedness + ID/structure preservation vs the original
python3 scripts/validate_paligo_xml.py compare original.xml edited.xml
```

The `compare` mode enforces the invariants that matter to Paligo: root element and namespaces unchanged, every `xml:id`/`id` from the original still present exactly once, every `xinfo:*` attribute preserved with its original value on the same element. Exit code 0 = safe to push.

For deeper structural validation, Paligo XML is close to DocBook 5.x — the DocBook RELAX NG schema can catch invalid nesting, but expect false positives on Paligo extensions (`xinfo:*` attributes, internal namespaces). Treat DocBook RNG validation as advisory, ID preservation as mandatory.

## Versioning, Status, and Translations — Rules That Bite

- **Released content is locked.** Editing requires moving the document back to work in progress, which creates a new version in Paligo. Don't silently flip `release_status` on released content — surface it to the user.
- **Releasing auto-approves translations.** Setting `STATUS_RELEASED` approves completed translations in all languages.
- **Translations align at the element level** via `xinfo:text` attributes. Editing a paragraph's text marks that segment as needing re-translation (expected and visible). Removing or changing its `xinfo:text` attribute orphans the existing translation entirely (silent data loss). This is why the validator treats `xinfo:*` as immutable.
- **No optimistic locking.** The API has no ETags. Use `checkout` as an advisory lock and compare `modified_at` before PUT.
- **Write rate limits are low** (document updates 10/min Business, 20/min Enterprise; reads 50/250 per minute) and **production/import/translation creates are 1/min on Business** — never loop those POSTs. Throttle proactively (pacing helper in workflows.md), honor `Retry-After` on 429, and give the user a time estimate before bulk jobs (full table and per-1,000-topic budgets in endpoints.md → Rate limits).

## Reference Files

- **[references/endpoints.md](references/endpoints.md)** — Complete endpoint catalog for the entire API: documents, folders, forks, images, search, imports, outputs, productions, publish settings, translation export/import, taxonomies, variables (sets/variants/variables/values), groups, users, assignments, plus pagination, rate limits, and error handling. Opens with a resource map of every path and verb.
- **[references/xml-format.md](references/xml-format.md)** — Paligo XML format: DocBook element vocabulary, `xinfo:*` attributes, cross-references, reuse mechanics, editing rules.
- **[references/workflows.md](references/workflows.md)** — Worked recipes: tree walking, full-library export, round-trip editing with conflict handling, publication traversal, translation-aware editing, triggering publishes.

## Disclaimer

This skill is not affiliated with, endorsed by, or sponsored by Paligo. It references publicly available API documentation for educational and integration purposes. The information may be outdated or incomplete. Always refer to the official Paligo documentation (https://api.paligo.net) for the most current API specifications.
