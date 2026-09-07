# Printify API Endpoint Catalog

Base URL: `https://api.printify.com` (Printful Enterprise brand: `https://enterprise.printful.com/api/pfy/public`). All V1 paths end in `.json` except the webhook `simulate` and the order `support-requests` routes. Auth: `Authorization: Bearer {token}` plus a required `User-Agent` header. JSON in/out (`application/json;charset=utf-8`). Official docs: https://developers.printify.com/ (single page). OpenAPI: https://developers.printify.com/openapi.json.

Object field definitions live in [schemas.md](schemas.md); events, webhook payloads, and signature verification in [webhooks.md](webhooks.md).

## Contents

- [Resource map](#resource-map)
- [Shops](#shops)
- [Catalog (V1)](#catalog-v1)
- [Catalog shipping (V2)](#catalog-shipping-v2)
- [Products](#products)
- [Orders](#orders)
- [Order support requests (reprint, refund, address change)](#order-support-requests)
- [Personalization](#personalization)
- [Uploads (media library)](#uploads-media-library)
- [Webhooks](#webhooks)
- [OAuth 2.0 (platform apps)](#oauth-20-platform-apps)
- [Pagination](#pagination)
- [Rate limits](#rate-limits)
- [Errors](#errors)

## Resource map

| Resource | Scope(s) | Endpoints |
|----------|----------|-----------|
| Shops | `shops.read` | list, disconnect |
| Catalog | `catalog.read`, `print_providers.read` | blueprints, print providers, variants, shipping (V1 flat, V2 per-method) |
| Products | `products.read` / `products.write` | list, get, GPSR, create, update, delete, publish, publishing_succeeded, publishing_failed, unpublish |
| Orders | `orders.read` / `orders.write` | list, get, submit, express submit, send to production, shipping cost calc, cancel, support requests |
| Personalization | `products.*` | options, create config, request preview, preview task status |
| Uploads | `uploads.read` / `uploads.write` | list, get, upload (URL or base64), archive |
| Webhooks | `webhooks.read` / `webhooks.write` | list, create, update, delete, simulate |

All shop-scoped paths need `{shop_id}` from `GET /v1/shops.json`.

## Shops

```
GET    /v1/shops.json                       # [{id, title, sales_channel}] — sales_channel is "disconnected" if none
DELETE /v1/shops/{shop_id}/connection.json  # disconnect shop from account → {}
```

## Catalog (V1)

Products in the catalog are **blueprints** (blank goods). Each blueprint is offered by several **print providers**; each provider's offering has its own **variants** (color/size combos, up to 3 option dimensions), **placeholders** (printable positions with pixel dimensions and a decoration method), and shipping profiles.

```
GET /v1/catalog/blueprints.json                                   # [{id, title, description, brand, model, images[]}]
GET /v1/catalog/blueprints/{blueprint_id}.json                    # same + tags[] (tags only on single-get)
GET /v1/catalog/blueprints/{blueprint_id}/print_providers.json    # [{id, title, decoration_methods[]}]
GET /v1/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json
      ?show-out-of-stock=0|1     # default omits out-of-stock; 1 returns all
      # → {id, title, variants: [{id, title, options{}, placeholders[], decoration_methods[]}]}
GET /v1/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json
      # → {handling_time{value,unit}, profiles: [{variant_ids[], first_item{currency,cost}, additional_items{}, countries[]}]}
GET /v1/catalog/print_providers.json                              # [{id, title, location{}}]
GET /v1/catalog/print_providers/{print_provider_id}.json          # + blueprints[] offered by this provider
```

Catalog endpoints have their own rate limit (100 req/min per account) on top of the global limit. The blueprint list is large and unpaginated; cache it.

## Catalog shipping (V2)

V2 follows json:api (`{data: [{type, id, attributes}], links}`). Economy shipping costs are **only** exposed in V2.

```
GET /v2/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json
      # → data: [{type:"shipping_method", id:"1".."4", attributes:{name}}], links: {standard, priority, express, economy}
GET /v2/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping/standard.json
GET /v2/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping/priority.json
GET /v2/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping/express.json
GET /v2/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping/economy.json
      # → data: [{type:"variant_shipping_{method}_{cc}", id:"{variant_id}", attributes:{shippingType, country{code},
      #           variantId, shippingPlanId, handlingTime{from,to}, shippingCost{firstItem{amount,currency}, additionalItems{}}}}]
```

`country.code` may be `REST_OF_THE_WORLD`. Amounts are cents. `handlingTime` is in days.

## Products

```
GET    /v1/shops/{shop_id}/products.json?limit=10&page=1      # limit max 50 (was 100 before Oct 2024); paginated envelope
GET    /v1/shops/{shop_id}/products/{product_id}.json
GET    /v1/shops/{shop_id}/products/{product_id}/gpsr.json    # [{title, text}] EU GPSR safety blocks
POST   /v1/shops/{shop_id}/products.json                      # create → full product
PUT    /v1/shops/{shop_id}/products/{product_id}.json         # partial or whole update → full product
DELETE /v1/shops/{shop_id}/products/{product_id}.json         # → {}
POST   /v1/shops/{shop_id}/products/{product_id}/publish.json
POST   /v1/shops/{shop_id}/products/{product_id}/publishing_succeeded.json
POST   /v1/shops/{shop_id}/products/{product_id}/publishing_failed.json
POST   /v1/shops/{shop_id}/products/{product_id}/unpublish.json
```

### Create body (minimum)

```json
{
  "title": "Product",
  "description": "Good product",
  "blueprint_id": 384,
  "print_provider_id": 1,
  "variants": [
    { "id": 45740, "price": 400, "is_enabled": true },
    { "id": 45742, "price": 400, "is_enabled": false }
  ],
  "print_areas": [
    {
      "variant_ids": [45740, 45742],
      "placeholders": [
        {
          "position": "front",
          "images": [
            { "id": "5d15ca551163cde90d7b2203", "x": 0.5, "y": 0.5, "scale": 1, "angle": 0 }
          ]
        }
      ]
    }
  ]
}
```

Optional on create/update: `tags[]`, `safety_information`, `print_details{print_on_side}`, `is_printify_express_enabled`, `sales_channel_properties{}`, `external{shipping_template_id}`, per-variant `sku`, `is_default`. Image `pattern{spacing_x, spacing_y, angle, offset}` makes a repeating tile. `images[].id` is an upload ID from the Uploads resource.

**Update rule:** when `variants` is present in a PUT, *all* variants must be present. Products with `is_locked: true` (mid-publish) reject updates.

### Publish body

```json
{ "title": true, "description": true, "images": true, "variants": true, "tags": true, "keyFeatures": true, "shipping_template": true }
```

For a store connected to a Printify-managed channel (Shopify, Etsy, ...) this pushes the product. For a **custom API store** it only locks the product and emits `product:publish:started`; the integration must create the listing itself, then call:

```json
POST .../publishing_succeeded.json   { "external": { "id": "5941187eb8e7e37b3f0e62e5", "handle": "https://example.com/path/to/product" } }
POST .../publishing_failed.json      { "reason": "Request timed out" }
POST .../unpublish.json              (no body)
```

Both `publishing_succeeded` and `publishing_failed` unlock the product.

## Orders

```
GET  /v1/shops/{shop_id}/orders.json?limit=10&page=1&status=&sku=   # limit max 10; status filters by order status; sku matches any line item
GET  /v1/shops/{shop_id}/orders/{order_id}.json
POST /v1/shops/{shop_id}/orders.json                                # submit → {id}
POST /v1/shops/{shop_id}/orders/express.json                        # submit with Printify Express splitting → json:api data[]
POST /v1/shops/{shop_id}/orders/{order_id}/send_to_production.json  # → {id}
POST /v1/shops/{shop_id}/orders/shipping.json                       # cost calc → {standard, express, priority, printify_express, economy} (cents)
POST /v1/shops/{shop_id}/orders/{order_id}/cancel.json              # only when status is on-hold or payment-not-received → full order
```

### Submit body

```json
{
  "external_id": "2750e210-39bb-11e9-a503-452618153e4a",
  "label": "00012",
  "line_items": [ ... ],
  "shipping_method": 1,
  "is_printify_express": false,
  "is_economy_shipping": false,
  "send_shipping_notification": false,
  "address_to": {
    "first_name": "John", "last_name": "Smith",
    "email": "john@example.com", "phone": "0574 69 21 90",
    "country": "BE", "region": "", "address1": "ExampleBaan 121", "address2": "45",
    "city": "Retie", "zip": "2470"
  }
}
```

`external_id` must be unique per shop; a duplicate returns **409** with error code 8503 and the existing order's id. Three line-item shapes are accepted (mix freely):

```json
{ "product_id": "5bfd0b66a342bcc9b5563216", "variant_id": 17887, "quantity": 1, "external_id": "line-1" }
{ "sku": "MY-SKU", "quantity": 1, "external_id": "line-2" }
{ "print_provider_id": 5, "blueprint_id": 9, "variant_id": 17887, "quantity": 1,
  "print_areas": { "front": "https://images.example.com/image.png" },
  "print_details": { "print_on_side": "mirror" } }
```

The third shape creates a product on the fly. It is slow, may time out, cannot use economy shipping (method 4), and Printify says it will be deprecated; prefer creating the product first. `print_areas` values may also be arrays of `{src, x, y, scale, angle}` for positioning. A line item may carry a `personalisation` object (see [Personalization](#personalization)).

**Shipping method codes:** `1` standard, `2` priority (currently returned as `express` in cost calc, being renamed), `3` Printify Express (returned as `printify_express`, to be renamed `express`), `4` economy. Express and economy orders may only contain eligible variants (`is_printify_express_eligible` / `is_economy_shipping_eligible`). `address_to.email` and `phone` are required for Printify Express.

### Express submit

`POST /v1/shops/{shop_id}/orders/express.json` takes the same body (`shipping_method` optional) and returns one or two orders: all eligible → one order with `fulfilment_type: "express"`; none → one `"ordinary"`; mixed → two orders, split. Response is `{data: [{type:"order", id, attributes:{app_order_id, fulfilment_type, line_items[]}}]}`.

### Auto-approval warning

New stores default to **automatic order approval after 24 hours**. If auto-approval is on, submitted orders go to production without a `send_to_production` call. Set the store's order approval to Manual in the Printify UI if the integration needs to control production timing.

## Order support requests

Not in the HTML docs; from the OpenAPI spec. Paths have **no `.json` suffix**.

```
POST /v1/shops/{shop_id}/orders/{order_id}/support-requests/reprint          # → 201 support request
POST /v1/shops/{shop_id}/orders/{order_id}/support-requests/refund           # → 201 support request
POST /v1/shops/{shop_id}/orders/{order_id}/support-requests/address-change   # → 200 {resolution:"updated_directly", order_id, address_to} or 201 {resolution:"support_request_created", ...}
GET  /v1/shops/{shop_id}/orders/{order_id}/support-requests                  # → {data: [support request]}
GET  /v1/shops/{shop_id}/orders/{order_id}/support-requests/{supportRequestId}  # → {data: support request}
```

Reprint / refund body:

```json
{
  "reason": "wrong_design",
  "description": "The design printed on the wrong side.",
  "image_urls": ["https://example.com/photo-of-issue.png"],
  "line_items": [{ "line_item_id": "5b05842f3921c9547531758d", "quantity": 1 }]
}
```

`reason` enum: `image_quality`, `incorrect_item`, `shipping_issues`, `stained_or_damaged_item`, `wrong_color_or_size`, `wrong_design`. `description` max 400 chars. `image_urls` max 5 (Printify re-hosts them). Address-change body is an `address_to` shape (`first_name`, `last_name`, `address1`, `city`, `country`, `zip` required; `address2`, `region`, `email`, `phone` optional). Support request object: `{id, order_id, type (order_reprint | order_refund | order_address_editing), status, status_details, outcome, line_item_ids[], created_at, updated_at}`.

## Personalization

Per-buyer text/photo fields on a product, with async mockup previews. Previews require the feature to be enabled on the shop (403 otherwise).

```
GET  /v1/shops/{shop_id}/products/{product_id}/personalization_options.json
      # → [{field_id, label, type: "textbox"|"image", text_options{character_limit}?}]
POST /v1/shops/{shop_id}/products/{product_id}/personalization.json
      # body {variant_id, items:[{field_id, type, input:{text}|{image_id}}]}
      # → {personalisation_strategy, personalisation_instructions}   (opaque; pass through to the order line item)
POST /v1/shops/{shop_id}/products/{product_id}/personalization_previews.json
      # body {external_id, variant_ids:[...], personalization:[{field_id, type, input}]}
      # → {task_id, status:"pending", external_id}          (400 validation, 403 not enabled, 422 unknown field/variant, 503)
GET  /v1/shops/{shop_id}/products/{product_id}/personalization_previews/tasks/{task_id}.json
      # → {task_id, status, preview_count?, mockups?:[{variant_id, mockup_id, src}], error?:{message, code}}
```

Task statuses: `pending`, `processing`, `completed`, `failed` (transient, resubmit), `corrupt` (bad input, terminal). The `personalization-preview-task:processed` webhook fires on terminal states. Order line item usage:

```json
{ "product_id": "...", "variant_id": 17887, "quantity": 1,
  "personalisation": {
    "personalisation_strategy": "pstudio_pre_order_headless",
    "personalisation_instructions": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "buyer_request": "Please use John as first name",
    "layers": [{ "personalisation_id": "front_text", "name": "front", "layer_type": "text", "text_input": "John" }],
    "personalisation_buyer_confirmation": { "approved": true, "source": "storefront", "date": "2017-04-18T13:24:28+00:00" }
  } }
```

A strategy value of `manual` means the personalizable product changed and the order needs merchant intervention; it will not auto-send to production.

## Uploads (media library)

```
GET  /v1/uploads.json?limit=10&page=1      # limit max 100; paginated envelope
GET  /v1/uploads/{image_id}.json
POST /v1/uploads/images.json               # {file_name, url} or {file_name, contents:"<base64>"} → image object
POST /v1/uploads/{image_id}/archive.json   # → {}
```

Use `url` uploads for anything over 5 MB; base64 uploads above 5 MB are slated for removal. Accepted types: PNG, JPG/JPEG. Errors: 10300 download failure (`cURL error ...`), 8201 size limit (`error.file.size.limit.exceeded`) or wrong format (`error.file.wrong.format`).

## Webhooks

```
GET    /v1/shops/{shop_id}/webhooks.json                          # [{id, topic, url, shop_id}]
POST   /v1/shops/{shop_id}/webhooks.json                          # {topic, url, secret?} → webhook
PUT    /v1/shops/{shop_id}/webhooks/{webhook_id}.json             # {url} (topic is immutable)
DELETE /v1/shops/{shop_id}/webhooks/{webhook_id}.json?host=example.com   # host must match the webhook URL's host → {id}
POST   /v1/shops/{shop_id}/webhooks/{webhook_id}/simulate         # any JSON body is echoed back inside resource; no .json suffix
```

Delivery: POST with JSON event payload; respond 200. On 4xx/5xx Printify retries up to 3 times, then blocks the URL for 1 hour. Topics and payloads: [webhooks.md](webhooks.md).

## OAuth 2.0 (platform apps)

Requires an approved app registration (review takes up to a week) which yields an `app_id` and scopes.

```
GET  https://printify.com/app/authorize?app_id=X&accept_url=https://...&decline_url=https://...&state=123
      # merchant grants → redirect to accept_url?code=...   (errors: ?error=...&error_description=...)
POST https://api.printify.com/v1/app/oauth/tokens            # form params app_id, code → {access_token, refresh_token, expire_at}
POST https://api.printify.com/v1/app/oauth/tokens/refresh    # form params app_id, refresh_token → same shape
```

Access tokens expire after **6 hours**; store the refresh token. Allow up to 3,000 characters for tokens. `accept_url`/`decline_url` must be https in production (http allowed on localhost), and must be domains, not IPs. Personal access tokens (single merchant) are generated at My Profile → Connections, last **1 year**, and are shown only once.

## Pagination

List endpoints (`products`, `orders`, `uploads`) return a Laravel-style envelope:

```json
{ "current_page": 1, "data": [...], "first_page_url": "/?page=1", "from": 1, "last_page": 5, "last_page_url": "/?page=5",
  "next_page_url": "/?page=2", "path": "/", "per_page": 10, "prev_page_url": null, "to": 10, "total": 49 }
```

Iterate `page=1..last_page` (or until `next_page_url` is null). Per-page maximums: products 50, orders 10, uploads 100. Catalog and webhook lists are plain arrays with no pagination.

## Rate limits

| Limit | Value |
|-------|-------|
| Global | 600 requests / minute per account (not per token) |
| Catalog endpoints | additional 100 requests / minute |
| Product publish endpoint | 200 requests / 30 minutes |
| Error budget | error responses must stay under 5% of total requests |

Exceeding a limit returns 429. Back off and retry; 502/503 are also safe to retry.

## Errors

Validation and operation failures return 400/422 with:

```json
{ "status": "error", "code": 8203, "message": "Validation failed.", "errors": { "reason": "Image has low quality", "code": 8203 } }
```

`errors.reason` may itself be a JSON string of field errors (e.g. `{"zip":["The zip field is required."]}`). Known codes (subject to change): 8103 order validation, 8201 upload validation, 8203 image DPI too low for the print area, 8503 duplicate order `external_id` (HTTP 409), 10300 image download failed. Auth failures return `{"error":"Unauthenticated","request_id":"..."}` with 401. Other statuses: 402 plan quota, 403 scope/resource forbidden, 404 unknown route or deleted resource, 413 payload too large, 429 rate limited, 5xx server side.
