# Paligo API Endpoint Reference

Base URL: `https://{instance}.paligoapp.com/api/v2`
Auth: HTTP Basic (`username:apikey`). JSON in/out. Official docs: https://api.paligo.net

## Contents

- [Documents](#documents)
- [Folders](#folders)
- [Forks](#forks)
- [Productions (publishing)](#productions-publishing)
- [Imports](#imports)
- [Translation export / import](#translation-export--import)
- [Taxonomies, Variables, Assignments](#taxonomies-variables-assignments)
- [Search (beta)](#search-beta)
- [Pagination](#pagination)
- [Rate limits](#rate-limits)
- [Errors and conflict handling](#errors-and-conflict-handling)

## Documents

"Documents" covers topics and publications — any content component.

### Document object

```json
{
  "id": 123,
  "name": "My topic",
  "uuid": "UUID-1234-5678",
  "type": "document",
  "creator": 2,
  "owner": 2,
  "author": 2,
  "created_at": 1603622378,
  "modified_at": 1603622378,
  "checkout": false,
  "checkout_user": 2,
  "parent_resource": 456,
  "taxonomies": [{ "id": 603, "title": "My taxonomy", "color": "..." }],
  "content": "<?xml version=\"1.0\"?><section ...>...</section>",
  "languages": ["en", "jp", "sv"],
  "custom_attributes": [{ "name": "...", "value": "..." }]
}
```

Notes:
- `content` is the full source-language XML as a JSON string (normal JSON escaping only — tags are literal, not entity-encoded).
- `languages` lists existing translation locales. There is **no documented query parameter to fetch a specific translation's content** — translated content moves through translation export/import (below).
- `checkout` / `checkout_user` reflect the editing lock.
- The list endpoint returns metadata; request a specific document to get `content`.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/documents` | List documents (paginated, filterable) |
| GET | `/documents/{id}` | Get one document including `content` XML |
| POST | `/documents` | Create a document |
| PUT | `/documents/{id}` | Update (returns 201 with the Document object) |
| DELETE | `/documents/{id}` | Delete |

### GET /documents query parameters

`name`, `parent` (folder id — this is how you list a folder's documents), `created_start_at`, `created_end_at`, `modified_start_at`, `modified_end_at`, `creator`, `owner`, `author`, `checkout`, `page`, `per_page`.

`modified_start_at` enables incremental sync: only pull documents changed since the last run.

### PUT /documents/{id} body fields

All optional; send only what you change:

```json
{
  "name": "My topic",
  "content": "<?xml ...><section>...</section>",
  "checkout": "false",
  "release_status": "STATUS_NOT_RELEASED",
  "taxonomies": [603, 304],
  "custom_attributes": [{ "name": "...", "value": "..." }]
}
```

### release_status values

| Value | Workflow stage |
|-------|----------------|
| `STATUS_NOT_RELEASED` | Work in progress (editable) |
| `STATUS_IN_TECHNICAL_REVIEW` | In review |
| `STATUS_IN_TRANSLATION` | Being translated — do not edit source |
| `STATUS_IN_RELEASE_REVIEW` | Translation/release review |
| `STATUS_RELEASED` | Released — locked/archived; auto-approves completed translations in all languages. Returning to work-in-progress creates a new version |

## Folders

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/folders` | List root folders |
| GET | `/folders/{id}` | Get a folder and its **subfolders** |
| POST | `/folders` | Create: `{"title": "My folder", "parent": 123}` |

```json
{
  "id": 123,
  "name": "My folder",
  "uuid": "UUID-1234-5678",
  "type": "folder",
  "children": [{ "id": "456", "name": "My subfolder", "type": "folder" }]
}
```

**Important:** `children` contains subfolders only. To enumerate the documents inside a folder, call `GET /documents?parent={folderId}`. Full tree walk = recurse folders + list documents per folder (see workflows.md).

## Forks

A fork is a reuse reference — a component placed inside a document structure (e.g., a topic in a publication's table of contents). Forks behave like symbolic links: the publication XML references them; content is not inlined.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/forks?parent={id}` | List forks under a parent (publication or fork) |
| POST | `/forks` | Add: `{"parent": 5421, "document": 3981, "position": null}` |
| DELETE | `/forks/{id}` | Remove from structure |

```json
{
  "id": 8493,
  "uuid": "UUID-1232-1454",
  "parent": 3919,
  "root_document": 3901,
  "position": 7,
  "depth": 4,
  "document": { "id": 123, "name": "My topic" }
}
```

- `parent` — the fork/document this sits under; `root_document` — the top-level publication; `position` — sibling order; `depth` — nesting level.
- To get a forked topic's text: take `document.id` and `GET /documents/{document.id}`.

## Productions (publishing)

Trigger a publish using a saved publish setting (created in the Paligo UI). Output formats (PDF, HTML5, etc.) are determined by the publish setting.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/productions` | Start: `{"publishsetting": "123"}` |
| GET | `/productions/{id}` | Poll status / get output |
| GET | `/productions` | List |

Use a production with a DocBook publish setting when you need **fully resolved** output (forks inlined, variables substituted, filters applied) rather than raw source XML.

## Imports

`POST /imports` ingests external content. Supported `type` values: `paligo`, `db5` (DocBook 5), `db4`, `xhtml`, `confluence`, `dita`, `flare`, `helpandmanual`, `docx`, `authorit`, `zendesk`, `openapi`. Options include matching existing components and generating admonitions. Poll with `GET /imports/{id}`.

## Translation export / import

Translated content is not writable via `PUT /documents`. Use the `translationexport` and `translationimport` resources to round-trip translations (XLIFF-based workflow). Source-language edits via PUT affect translation state at the segment level — see xml-format.md on `xinfo:text`.

## Taxonomies, Variables, Assignments

CRUD endpoints exist for `/taxonomies`, `/variables`, and `/assignments`. Variables are returned unresolved inside topic `content` (as variable references); resolution happens at publish time.

## Search (beta)

`POST` with body:

```json
{
  "resource": "documents",
  "page": 1,
  "per_page": 50,
  "where": [
    { "operator": "...", "property": "...", "value": "...", "values": [], "start": null, "end": null }
  ]
}
```

Searchable resources include documents, taxonomies, forks.

## Pagination

List endpoints accept `page` and `per_page` and return:

```json
{ "page": 1, "next_page": "https://...", "total_pages": 3, "resources": [ ... ] }
```

Iterate until `next_page` is null/absent or `page == total_pages`.

## Rate limits

The REST API is included in both current Paligo plans; only the rates differ ("limited rates on the Business plan, maximum rates on the Enterprise plan"). Limits are per minute, per endpoint+operation:

| Endpoint | Operation | Business | Enterprise |
|----------|-----------|---------:|-----------:|
| Documents | Show/List | 50 | 250 |
| Documents | Update | 10 | 20 |
| Folders | Show/List | 50 | 250 |
| Folders | Update | 10 | 100 |
| Forks | Show/List | 50 | 250 |
| Forks | Create / Delete | 20 | 100 |
| Images | Create / Update | 10 | 20 |
| Imports | Show/List | 50 | 250 |
| Imports | **Create** | **1** | **1** |
| Productions | Show/List | 50 | 250 |
| Productions | **Create** | **1** | **10** |
| Outputs | Show | 10 | 10 |
| Publish Settings | Show/List | 50 | 250 |
| Taxonomies | Show/List | 50 | 250 |
| Taxonomies | Create / Update | 10 | 100 |
| Translation Exports/Imports | Show/List | 50 | 250 |
| Translation Exports/Imports | **Create** | **1** | **10** |
| Variables / Variable Sets / Values | Show/List | 50 | 200 |
| Variables / Variable Sets / Values | Create/Update/Delete | 10 | 20 |

### Staying under the limits

- **Throttle proactively** — don't rely on 429s. Safe pacing with ~10% headroom:
  - Business: reads ≥ 1.3s apart, document writes ≥ 6.5s apart.
  - Enterprise: reads ≥ 0.3s apart, document writes ≥ 3.2s apart.
- **Creates of imports, productions, and translation exports/imports are 1/min on Business** (productions/translations 10/min on Enterprise). Never loop POSTs against these — batch into one production per publish setting and wait ≥60s between creates.
- **Polling productions/imports**: poll the Show endpoint at 30–60s intervals; output downloads (`Outputs Show`) are capped at 10/min on every plan.
- **On 429**, the response carries a `Retry-After` header (seconds the client must wait). Always sleep that long, then retry the same request. Treat a 429 as a signal your pacing is wrong, not as normal flow.
- **Limits are per endpoint+operation**, so interleaving (e.g., reading documents while writing others) doesn't share one bucket — but keep each stream within its own limit.
- **Bulk job time budgeting (Business)**: full-library pull of N topics ≈ N×1.3s (~22 min per 1,000); bulk edit push ≈ N×6.5s (~1h50m per 1,000). Surface these estimates to the user before starting long jobs.

## Errors and conflict handling

- Success codes: 200 (OK), 201 (Created — including PUT), 204 (No Content).
- 401/403 — bad credentials or non-admin account.
- **No ETags / If-Match / optimistic locking.** Concurrency strategy: check `checkout == false`, optionally set checkout during your edit window, compare `modified_at` immediately before PUT, and release checkout after.
