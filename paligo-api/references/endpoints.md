# Paligo API Endpoint Reference

Base URL: `https://{instance}.paligoapp.com/api/v2`
Auth: HTTP Basic (`username:apikey`, Base64-encoded). JSON in/out unless noted (image/import/translation-import uploads are `multipart/form-data`). Official docs: https://api.paligo.net (single-page, `index-en.html`).

This file is the **complete endpoint catalog** for the Paligo CCMS REST API v2. Every resource family the API exposes is below. For the content round-trip editing workflow specifically, see [workflows.md](workflows.md); for the XML format, see [xml-format.md](xml-format.md).

## Contents

- [Resource map (everything at a glance)](#resource-map-everything-at-a-glance)
- [Documents](#documents)
- [Folders](#folders)
- [Forks](#forks)
- [Images](#images)
- [Search (beta)](#search-beta)
- [Imports](#imports)
- [Outputs](#outputs)
- [Productions (publishing)](#productions-publishing)
- [Publish settings](#publish-settings)
- [Translation export / import](#translation-export--import)
- [Taxonomies](#taxonomies)
- [Variables (sets, variants, variables, values)](#variables)
- [Groups](#groups)
- [Users](#users)
- [Assignments](#assignments)
- [Pagination](#pagination)
- [Rate limits](#rate-limits)
- [Errors and conflict handling](#errors-and-conflict-handling)
- [Confidence notes](#confidence-notes)

## Resource map (everything at a glance)

| Resource | Base path | Verbs | Notes |
|----------|-----------|-------|-------|
| Documents | `/documents` | GET list, GET id, POST, PUT, DELETE | Topics + publications; `content` holds XML |
| Folders | `/folders` | GET list, GET id, POST | `children` = subfolders only |
| Forks | `/forks` | GET list, GET id, POST, DELETE | Reuse references inside structures |
| Images | `/images` | GET list, GET id, POST, PUT | Binary upload via `multipart/form-data` |
| Search | `/search` | POST | Beta; documents/taxonomies/forks |
| Imports | `/imports` | GET list, GET id, POST | `multipart/form-data`; **create 1/min** |
| Outputs | `/outputs/{name}` | GET | Returns `application/zip` archive |
| Productions | `/productions` | GET list, GET id, POST | Publish job; **create 1/min Business** |
| Publish settings | `/publishsetting` | GET list, GET id | Read-only; created in UI |
| Translation export | `/translationexport` | GET list, GET id, POST | JSON create; **create 1/min Business** |
| Translation import | `/translationimport` | GET list, GET id, POST | `multipart/form-data`; **create 1/min Business** |
| Taxonomies | `/taxonomies` | GET list, GET id, POST, PUT, DELETE | Hierarchical labels |
| Variable sets | `/variables/sets` | GET list, GET id, POST, PUT, DELETE | Container of variants/variables |
| Variable variants | `/variables/variants` | GET list, GET id, POST, PUT, DELETE | Conditional value sets |
| Variables | `/variables` | GET list, GET id, POST, PUT, DELETE | Individual variable keys |
| Variable values | `/variables/values` | GET list, GET id, POST, PUT | Text / image / translation values |
| Groups | `/group` | GET list, GET id | **singular** path |
| Users | `/users` | GET list, GET id | Read-only |
| Assignments | `/assignments` | GET list, GET id, POST, PUT, DELETE | Workflow task assignments |

Trailing slashes: the docs write create paths with a trailing slash (`POST /documents/`). Both forms generally work; match the docs if you hit a 404.

## Documents

"Documents" covers topics and publications — any content component.

### Document object

Real shape from a live instance (`GET /documents/12`):

```json
{
  "id": 12,
  "name": "Create Your First Publication",
  "uuid": "UUID-f8a9de46-...",
  "type": "component",
  "subtype": "component",
  "creator": 2,
  "owner": 2,
  "author": 2,
  "created_at": 1757575805,
  "modified_at": 1730393287,
  "checkout": false,
  "checkout_user": "",
  "parent_resource": 317,
  "taxonomies": [],
  "release_status": "Work in progress",
  "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>...<section ...>...</section>",
  "languages": ["en", "es"],
  "external": [],
  "custom_attributes": [{ "name": "...", "value": "..." }]
}
```

Notes (✅ = verified live):
- ✅ `type` is **`"component"`** for topics/components (the docs' generic "document" is not the literal value). `subtype` also seen as `"component"`.
- ✅ `content` is the full source-language XML as a JSON string — but **only on the show (single-document) endpoint**. In the **list endpoint `content` is `""`** (empty); pull the document by id to get XML.
- ✅ `checkout_user` is **`""`** (empty string) when not checked out — not an integer/null.
- ✅ `external` is a real field (array; empty when the component isn't an external reference). Not in the published docs.
- ✅ `release_status` is returned as a **human-readable label** (e.g. `"Work in progress"`), which does **not** match the `STATUS_*` constants the docs say PUT accepts — see the release_status table below.
- `languages` lists existing translation locales. There is **no documented query parameter to fetch a specific translation's content** — translated content moves through translation export/import (below).

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

### POST /documents body fields

```json
{
  "name": "My topic",
  "parent": 456,
  "subtype": "section",
  "content": "<?xml ...><section>...</section>",
  "custom_attributes": [{ "name": "...", "value": "..." }]
}
```

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

⚠️ **Read vs write mismatch (verified live):** GET returns a *human-readable label* (e.g. `"Work in progress"`), while the docs say PUT expects the `STATUS_*` constant. So the value you read back is not the value you write. The likely mapping is `STATUS_NOT_RELEASED` ↔ "Work in progress", etc., but the full label↔constant mapping is **unconfirmed** — verify with a controlled write test on a throwaway topic before automating status changes.

| Value (write / PUT) | Workflow stage (read label) |
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
| GET | `/forks/{id}` | Show a fork |
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

## Images

Image assets stored in the Content Manager. **Uploads and updates use `multipart/form-data`**, not JSON.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/images` | List images (paginated, filterable) |
| GET | `/images/{id}` | Show one image (metadata + download URL) |
| POST | `/images` | Upload a new image (`multipart/form-data`) |
| PUT | `/images/{id}` | Replace/update an image (`multipart/form-data`) |

### Image object

```json
{
  "id": 123,
  "name": "diagram.png",
  "uuid": "UUID-1234-5678",
  "type": "image",
  "creator": 2,
  "owner": 2,
  "author": 2,
  "created_at": 1603622378,
  "content_url": "https://example.paligoapp.com/.../diagram.png",
  "description": "..."
}
```

### GET query parameters (list and show)

`name`, `parent` (folder id), `size`, `variant` (language/variant code), `download` (boolean — when true, return the binary file instead of metadata), `page`, `per_page`.

### POST / PUT form fields

`image` (binary file, required on create), `parent` (folder id), `variant` (language/variant code), `size`, `trim` (boolean — whitespace removal for PDF). On PUT all fields are optional.

### Image size codes

| Code | Meaning |
|------|---------|
| `pre` | Preview |
| `scr` | Screen |
| `lpr` | Low print resolution |
| `hpr` | High print resolution |
| `icn` | Icon |
| `spr` | Small print |

To download an image binary: either `GET /images/{id}?download=true`, or read `content_url` from the image object and GET that.

## Search (beta)

`POST /search` runs a structured query. **Beta** — interface may change.

### Request body

```json
{
  "resource": "documents",
  "page": 1,
  "per_page": 50,
  "where": [
    {
      "operator": "equals",
      "property": "name",
      "value": "Installation",
      "values": [],
      "start": null,
      "end": null
    }
  ]
}
```

`resource` is one of `documents`, `taxonomies`, `forks`. `where` is an array of conditions (AND-combined).

### Operators

| Operator | Use | Applies to |
|----------|-----|------------|
| `equals` | Exact match | string / numeric properties |
| `has` | Membership in an array property | array properties (e.g. `languages`) |
| `before` | Timestamp earlier than `value` | `created_at`, `modified_at` |
| `after` | Timestamp later than `value` | `created_at`, `modified_at` |
| `between` | Timestamp within `start`..`end` | `created_at`, `modified_at` |
| `containsblockelement` | XML contains a given block element | document `content` |

### Properties NOT searchable (beta limitations)

- Documents: `subtype`, `owner`, `creator`, `checkout`, `checkout_user`, `external`
- Forks: `position`, `depth`
- Taxonomies: `color`

### Response

The search response returns paged results. Result items carry the resource's metadata fields (id, name, uuid, type, timestamps, etc.). The list key has been observed as `items` in the search response (other list endpoints use `resources`) — confirm against your instance and code defensively for both.

### Examples

```jsonc
// Documents with an English translation
{ "resource": "documents", "where": [{ "operator": "has", "property": "languages", "value": "en" }] }

// Documents modified between two timestamps
{ "resource": "documents", "where": [{ "operator": "between", "property": "modified_at", "start": "1600000000", "end": "1610000000" }] }

// Documents whose XML contains a <table>
{ "resource": "documents", "where": [{ "operator": "containsblockelement", "property": "content", "value": "table" }] }
```

## Imports

`POST /imports` ingests external content. **`multipart/form-data`.** Asynchronous — poll `GET /imports/{id}`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/imports` | List imports (query: `user`, `status`, `page`, `per_page`) |
| GET | `/imports/{id}` | Poll one import |
| POST | `/imports` | Start an import (`multipart/form-data`) |

### Create form fields

| Field | Type | Purpose |
|-------|------|---------|
| `archive` | binary | The source file/archive to import (required) |
| `type` | enum | Source format (see below) |
| `parent` | integer | Target folder id |
| `match_components` | boolean | Reuse/match against existing components |
| `generate_hazard` | boolean | Generate hazard/admonition statements |
| `ignore_warnings` | boolean | Proceed despite import warnings |
| `import_missing_images` | boolean | Pull in referenced images |
| `title_prefix` | string | Prefix added to imported topic titles |
| `folder_numbering` | boolean | Number generated folders |
| `folder_levels` | integer | How many heading levels become folders |
| `use_varset_id` | integer | Variable set to apply |
| `zendesk_category` | string | (Zendesk import) category |
| `openapi_languages` | string[] | (OpenAPI import) languages |
| `openapi_maxdepth` | integer | (OpenAPI import) max nesting depth |

### Import `type` values

`paligo`, `db5` (DocBook 5), `db4` (DocBook 4), `xhtml`, `confluence`, `dita`, `flare` (MadCap Flare), `helpandmanual`, `docx`, `authorit`, `zendesk`, `openapi`.

### Import response object

```json
{
  "id": 123,
  "status": "running",
  "message": "Importing topics…",
  "steps": { "total": 20, "count": 3 },
  "user": 2
}
```

`status`: `running` | `done` | `cancelled`. Use `steps.count`/`steps.total` for progress.

## Outputs

`GET /outputs/{name}` downloads a finished publication archive. The `{name}` comes from a completed production (`url`/output name on the Production object).

- Returns binary `application/zip` (the rendered output: PDF, HTML5 bundle, etc., per the publish setting).
- Rate limited to 10/min on every plan — don't poll it; fetch once the production is `done`.

## Productions (publishing)

Trigger a publish using a saved publish setting (created in the Paligo UI). Output formats (PDF, HTML5, etc.) are determined by the publish setting. Asynchronous — poll `GET /productions/{id}`.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/productions` | Start: `{"publishsetting": "123"}` |
| GET | `/productions/{id}` | Poll status / get output |
| GET | `/productions` | List (query: `page`, `per_page`) |

### Production response object

```json
{
  "id": "123",
  "document_name": "User Guide",
  "document_id": 3901,
  "format": "pdf",
  "status": "running",
  "message": "Rendering PDF…",
  "steps": { "total": 12, "count": 5 },
  "url": "user-guide-20240101.zip",
  "log_url": "https://example.paligoapp.com/.../log.txt",
  "started_at": 1603622378,
  "ended_at": 1603622999
}
```

`status`: `running` | `done` | `cancelled`. When `done`, `url` names the output archive — fetch it via `GET /outputs/{url-or-name}`. `log_url` holds the build log (useful on failures).

Use a production with a DocBook publish setting when you need **fully resolved** output (forks inlined, variables substituted, filters applied) rather than raw source XML.

## Publish settings

Read-only catalog of publish settings configured in the Paligo UI. Use these ids when creating a production.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/publishsetting` | List publish settings |
| GET | `/publishsetting/{id}` | Show one |

```json
{
  "id": 123,
  "name": "PDF — Customer Manual",
  "uuid": "UUID-1234-5678",
  "type": "publishsetting",
  "document_id": 3901,
  "format": "pdf"
}
```

Path is **singular** (`/publishsetting`). `document_id` is the publication the setting targets; `format` is the output type.

## Translation export / import

Translated content is **not** writable via `PUT /documents`. Round-trip translations through these resources (XLIFF-based). Both creates are asynchronous and heavily rate-limited (1/min create on Business).

### translationexport

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/translationexport` | List exports |
| GET | `/translationexport/{id}` | Poll one export |
| POST | `/translationexport` | Create (JSON) |

Create body:

```json
{ "document": 123, "languages": ["jp", "sv"], "format": "xliff" }
```

Response:

```json
{
  "id": "123",
  "status": "running",
  "document_id": 123,
  "languages": ["jp", "sv"],
  "format": "xliff",
  "message": "Exporting…",
  "steps": { "total": 20, "count": 3 },
  "output_url": "https://example.paligoapp.com/export-file.xliff",
  "created_at": 1603622378
}
```

When `done`, download the file at `output_url`.

### translationimport

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/translationimport` | List imports |
| GET | `/translationimport/{id}` | Poll one import |
| POST | `/translationimport` | Create (`multipart/form-data`) |

Create form fields: `archive` (binary, the completed translation file), `document` (integer, target document id), `language` (string, target locale), `update_existing` (boolean).

Response mirrors the export shape with a single `language` field and a `steps` progress counter; `status` is `running` | `done` | `cancelled`.

### End-to-end translation round-trip

1. `POST /translationexport` with the document and target languages → poll until `done` → download `output_url` (XLIFF).
2. Translate the XLIFF (external TMS / translator).
3. `POST /translationimport` with the completed file, document id, and language → poll until `done`.
4. Releasing the source document (`STATUS_RELEASED`) auto-approves completed translations.

## Taxonomies

Hierarchical labels (categories) you can attach to documents.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/taxonomies` | List |
| GET | `/taxonomies/{id}` | Show (with hierarchy) |
| POST | `/taxonomies` | Create |
| PUT | `/taxonomies/{id}` | Update |
| DELETE | `/taxonomies/{id}` | Delete |

Object / create+update body:

```json
{
  "id": 603,
  "title": "Hardware",
  "color": 2,
  "parent": 600
}
```

- `title` — label text. `color` — integer `0`–`4` (UI swatch). `parent` — parent taxonomy id (omit/null for a root).
- Attach to a document by sending taxonomy ids in the document's `taxonomies` array on PUT.

## Variables

Paligo variables let you reuse short strings/images that resolve at publish time. The API splits them into four sub-resources under `/variables`:

- **Variable sets** (`/variables/sets`) — top-level container.
- **Variable variants** (`/variables/variants`) — conditional alternatives within a set.
- **Variables** (`/variables`) — the named keys.
- **Variable values** (`/variables/values`) — the actual content for a variable in a variant.

Each supports the standard CRUD verbs (values are List/Create/Show/Update — no documented delete).

| Sub-resource | List | Create | Show | Update | Delete |
|--------------|------|--------|------|--------|--------|
| Sets | `GET /variables/sets` | `POST /variables/sets` | `GET /variables/sets/{id}` | `PUT /variables/sets/{id}` | `DELETE /variables/sets/{id}` |
| Variants | `GET /variables/variants` | `POST /variables/variants` | `GET /variables/variants/{id}` | `PUT /variables/variants/{id}` | `DELETE /variables/variants/{id}` |
| Variables | `GET /variables` | `POST /variables` | `GET /variables/{id}` | `PUT /variables/{id}` | `DELETE /variables/{id}` |
| Values | `GET /variables/values` | `POST /variables/values` | `GET /variables/values/{id}` | `PUT /variables/values/{id}` | — |

Common object shape: `{ "id", "name", "uuid", "type" }`. Variable **values** come in three subtypes — text, image, and translation (the create payload differs accordingly: a text value carries a string, an image value references an image id, a translation value carries a per-language value). Resolution happens at publish time; topic `content` holds variable *references*, not resolved text.

## Groups

Read-only. **Path is singular: `/group`.**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/group` | List groups |
| GET | `/group/{id}` | Show one group |

```json
{ "id": 12, "name": "Writers", "uuid": "UUID-…", "type": "group" }
```

## Users

Read-only.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/users` | List users |
| GET | `/users/{id}` | Show one user |

Real shape from a live instance (list key is `users`):

```json
{ "id": 3, "username": "jane@example.com", "name": "Jane Doe", "email": "jane@example.com", "type": "admin" }
```

- ✅ Fields are `username`, `name`, `email`, `type` — there is **no `role` field**; `type` *is* the role. Seen values: `admin`, `contributor` (others likely exist, e.g. author/reviewer).
- Use `id` values here to interpret `creator`/`owner`/`author`/`checkout_user` on other resources.

## Assignments

Workflow task assignments (who is assigned to do what on a document).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/assignments` | List |
| GET | `/assignments/{id}` | Show |
| POST | `/assignments` | Create |
| PUT | `/assignments/{id}` | Update |
| DELETE | `/assignments/{id}` | Delete |

Object carries `id`, a `type` (AssignmentTypes) and a `status` (AssignmentStatus), plus the target document and assigned user(s). The exact AssignmentTypes/AssignmentStatus enum values are referenced in the docs' Schemas section but not enumerated there — read one live assignment to discover the values for your instance before relying on specific strings.

## Pagination

List endpoints accept `page` and `per_page` and return a wrapper whose **result array is keyed by the resource name** — verified on a live instance:

```json
{ "page": 1, "next_page": "https://...", "total_pages": 3, "documents": [ ... ] }
```

**The list key is NOT a generic `resources`.** It matches the endpoint: `documents`, `folders`, `forks`, `images`, `users`, `taxonomies`, etc. (Search returns its hits under `items`.) Code defensively: pick the first array-valued key in the response rather than hardcoding one.

`next_page` is the **empty string `""`** (not null/absent) when there are no more pages. Iterate until `next_page == ""` (or `page == total_pages`).

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

Groups, Users, Assignments and Search are not separately listed in the published table; treat them as Show/List-class (≈50/min Business) and pace conservatively.

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

- Success codes: 200 (OK), 201 (Created — including PUT), 204 (No Content — including DELETE).
- 401/403 — bad credentials or non-admin account.
- 404 — wrong id, or trailing-slash mismatch on a create path (try `POST /documents/`).
- 429 — rate limited; honor `Retry-After`.
- **No ETags / If-Match / optimistic locking.** Concurrency strategy: check `checkout == false`, optionally set checkout during your edit window, compare `modified_at` immediately before PUT, and release checkout after.

## Confidence notes

This reference is compiled from the public Paligo API docs (a single rendered page) and partially verified against a live Paligo instance.

**Verified live (✅):** auth; pagination wrapper keyed by resource name with `next_page == ""` at the end; folder tree walk; document object shape (`type: "component"`, empty `content` in list view, `checkout_user: ""`, `external` field, `release_status` as a read label); user object (`username`/`name`/`email`/`type`); the topic XML format (`xinfo` namespace `http://ns.expertinfo.se/cms/xmlns/1.0`, `docbookxi-5.1-xinfo.rng` schema, integer `xinfo:text` segment ids).

**Still unverified — confirm before depending on exact shapes:**
- `release_status` read-label ↔ write-constant mapping (needs a controlled write test).
- Behavior of a write (PUT) round-trip generally — nothing has been written to the instance yet.
- Exact response field lists for groups/publish settings/assignments (docs show minimal schemas; not yet pulled live).
- AssignmentTypes / AssignmentStatus enum values (referenced but not enumerated).
- Variable values payload subtypes (text/image/translation) and variable sub-resource nesting.

When a real response contradicts this file, trust the instance and update this file.
