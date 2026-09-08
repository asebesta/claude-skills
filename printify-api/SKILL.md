---
name: printify-api
description: Printify print-on-demand API reference and CLI for building integrations — browsing the catalog (blueprints, print providers, variants, placeholders, shipping), uploading artwork, creating and publishing products, submitting and tracking orders, personalization previews, webhooks, and OAuth for platform apps. Use when writing code against api.printify.com (or the Printful Enterprise mirror), when the user mentions Printify, blueprints/print providers, or wants to read/write Printify shops, products, orders, or uploads. Includes a dependency-free CLI (scripts/printify) for direct calls.
---

# Printify API

Reference for the **Printify Public API** (V1 REST plus V2 json:api catalog shipping). Printify is a print-on-demand platform: you pick a blank **blueprint** from the catalog, choose a **print provider**, place artwork on **placeholders** to make a **product**, then submit **orders** that providers fulfil and ship.

**Every endpoint, request body, and field is documented in the references. Read them before writing code:**

- [references/endpoints.md](references/endpoints.md) — full endpoint catalog with bodies, query params, pagination, rate limits, error codes, OAuth
- [references/schemas.md](references/schemas.md) — object fields, enums (order statuses, shipping methods), image positioning rules
- [references/webhooks.md](references/webhooks.md) — event topics, payloads, retry rules, HMAC verification, receiver skeleton

## Base URL and auth

```
https://api.printify.com/v1/...                          # Printify
https://enterprise.printful.com/api/pfy/public/v1/...    # Printful Enterprise brand (same API)
```

- `Authorization: Bearer {token}` — a **personal access token** (single merchant; generated at My Profile → Connections; valid 1 year; shown once) or an **OAuth access token** (platform apps; expires every 6 hours, refresh with the refresh token).
- A `User-Agent` header is **required** on every request (app name or client type).
- JSON in and out, UTF-8. No CORS: calls must come from a server, never a browser.
- Scopes: `shops.read`, `catalog.read`, `print_providers.read`, `products.read/write`, `orders.read/write`, `uploads.read/write`, `webhooks.read/write`.

Almost every path needs a `{shop_id}`; get it from `GET /v1/shops.json`.

## CLI

`scripts/printify` is a dependency-free Python CLI (stdlib only) that adds the auth and User-Agent headers, retries 429/502/503 with backoff, and can walk paginated lists.

**Token lookup order:** `PRINTIFY_API_TOKEN` env var first (CI, Linux, one-off overrides), then the macOS Keychain item written by `printify auth set`. Prefer the Keychain on a Mac so the token never sits in a file that every tool in the directory can read. Set `PRINTIFY_PROFILE=<name>` to keep tokens for several Printify accounts on one machine.

```bash
scripts/printify auth set             # prompts for the token, stores it in the Keychain (or pipe it on stdin)
scripts/printify auth status          # shows the source and a masked token
scripts/printify auth remove
export PRINTIFY_API_TOKEN=...          # alternative: env var (wins over the Keychain when set)

scripts/printify shops
scripts/printify get /v1/catalog/blueprints/6/print_providers.json
scripts/printify get /v1/shops/5432/products.json -q limit=50 --all      # every page, one array
scripts/printify post /v1/shops/5432/orders.json -f order.json
scripts/printify put  /v1/shops/5432/products/{id}.json -d '{"title":"New title"}'
scripts/printify delete /v1/shops/5432/webhooks/{id}.json -q host=example.com
```

Set `PRINTIFY_API_BASE=https://enterprise.printful.com/api/pfy/public` for the Printful Enterprise brand. Exit code 2 means the API returned 4xx/5xx; the JSON error body is printed.

Keychain reads need the `com.apple.SecurityServer` mach service. Sandboxed agents (Codex desktop's workspace-write mode, for example) only allow it when network access is enabled, which any API call needs anyway. If `auth status` reports no token inside a sandbox while it works in a normal shell, enable network for the project or fall back to the env var.

## Resource map

| Resource | Base path | Notes |
|----------|-----------|-------|
| Shops | `/v1/shops.json` | List shops, disconnect |
| Catalog | `/v1/catalog/...` | Blueprints → print providers → variants (with placeholders) → shipping. Separate 100 req/min limit |
| Catalog shipping V2 | `/v2/catalog/.../shipping/{standard\|priority\|express\|economy}.json` | Per-variant, per-country costs and handling time. Economy costs are V2-only |
| Uploads | `/v1/uploads/...` | Media library; upload by URL (preferred over 5 MB) or base64 |
| Products | `/v1/shops/{shop_id}/products/...` | CRUD, GPSR, publish lifecycle |
| Orders | `/v1/shops/{shop_id}/orders/...` | Submit, express submit, shipping cost calc, send to production, cancel, support requests (reprint/refund/address change) |
| Personalization | `/v1/shops/{shop_id}/products/{id}/personalization*` | Buyer text/photo fields, async mockup previews |
| Webhooks | `/v1/shops/{shop_id}/webhooks/...` | Subscribe to shop/product/order/personalization events |

## Core workflow: catalog → product → order

1. **Pick a blueprint and provider.** `GET /v1/catalog/blueprints.json` (large, unpaginated, cache it) → `GET /v1/catalog/blueprints/{id}/print_providers.json`.
2. **Get variants and placeholders.** `GET /v1/catalog/blueprints/{id}/print_providers/{pp}/variants.json`. Each variant lists `placeholders[]` with `position`, `decoration_method`, and pixel `width`/`height`. The position you choose selects the decoration method (e.g. `front` DTG vs `front_dtf` vs `large_center_embroidery`).
3. **Upload artwork.** `POST /v1/uploads/images.json` with `{file_name, url}` → `id`. Artwork should match the placeholder's pixel size; undersized images fail DPI validation (error 8203).
4. **Create the product.** `POST /v1/shops/{shop_id}/products.json` with `title`, `description`, `blueprint_id`, `print_provider_id`, `variants[{id, price, is_enabled}]`, and `print_areas[{variant_ids, placeholders[{position, images[{id, x, y, scale, angle}]}]}]`. Coordinates run 0..1 with the center at (0.5, 0.5); `scale` is image width relative to placeholder width. Mock-ups are generated server-side into `images[]`.
5. **Publish.** For stores on a Printify-managed channel, `POST .../publish.json` pushes the listing. For a **custom API store**, publish only locks the product and fires `product:publish:started`; your code creates the listing on your channel, then calls `publishing_succeeded.json` (with the external id and handle) or `publishing_failed.json` to unlock it.
6. **Quote shipping.** `POST /v1/shops/{shop_id}/orders/shipping.json` with `line_items` + `address_to` → `{standard, priority, express, printify_express, economy}` in cents.
7. **Submit the order.** `POST /v1/shops/{shop_id}/orders.json` with a unique `external_id`, `line_items[{product_id, variant_id, quantity}]` (or `{sku, quantity}`), `shipping_method` (1 standard, 2 priority, 3 Printify Express, 4 economy), and `address_to`. Duplicate `external_id` → 409.
8. **Send to production** with `POST .../orders/{id}/send_to_production.json`, unless the store auto-approves (see gotchas). Track via `order:updated` / `order:shipment:*` webhooks or by polling `status`.

## Gotchas

- **Auto-approval is on by default.** New stores send orders to production automatically after 24 hours. If the integration must control timing, set the store's order approval to Manual in the Printify UI.
- **Cancel only works** while the order is `on-hold` or `payment-not-received`. After that, use the support-request endpoints (reprint, refund, address change).
- **Order list pages are tiny**: `limit` max is 10 (products 50, uploads 100). Prefer webhooks over polling.
- **Updating variants requires all variants** in the PUT body. Products are locked (`is_locked`) during publishing and reject updates.
- **On-the-fly product creation inside an order** (`blueprint_id` + `print_areas` on a line item) is slow, can't use economy shipping, and is slated for deprecation. Create products first.
- **Express and economy orders** must contain only eligible variants; Printify Express also requires `address_to.email` and `phone`. `POST .../orders/express.json` splits mixed carts into two orders.
- **Shipping method naming is mid-rename**: code 2 is `priority` (still returned as `express` in the cost calc), code 3 is Printify Express (returned as `printify_express`, to become `express`). Code by number, not by name.
- **Rate limits**: 600 req/min per account globally, 100 req/min for catalog, 200 publishes per 30 min, and error responses must stay under 5% of traffic. Retry 429/502/503 with backoff.
- **Webhooks block after failures**: 3 retries on non-200, then a 1-hour block. Return 200 fast and verify `X-Pfy-Signature` (HMAC-SHA256 of the raw body, `sha256=` prefix).
- **Webhook delete needs `?host=`** matching the URL's host.
- Money is always integer cents; product timestamps use the misspelled `update_at` field.

## Disclaimer

This skill is not affiliated with, endorsed by, or sponsored by Printify. It is derived from the public documentation at https://developers.printify.com/ and the published OpenAPI specification. Endpoints, error codes, and limits may change; verify against the official docs for anything load-bearing.
