# Printify API Object Schemas

Field-level reference for the objects the API returns and accepts. Endpoints and request bodies are in [endpoints.md](endpoints.md). All money values are integer **cents**. Timestamps are UTC strings like `2017-04-18 13:24:28+00:00`. Catalog IDs (blueprint, print provider, variant, option value) are integers; product, order, image, webhook, and event IDs are 24-hex-char strings.

## Contents

- [Shop](#shop)
- [Blueprint, print provider, catalog variant, placeholder](#catalog-objects)
- [Catalog shipping (V1 profiles)](#catalog-shipping-v1-profiles)
- [Product](#product)
- [Product variant](#product-variant)
- [Print area, placeholder, image layer, pattern](#print-area-placeholder-image-layer-pattern)
- [Image positioning coordinate system](#image-positioning-coordinate-system)
- [Mock-up image, option, view](#mock-up-image-option-view)
- [Sales channel properties](#sales-channel-properties)
- [Publishing flags](#publishing-flags)
- [Order](#order)
- [Order status enum](#order-status-enum)
- [Line item](#line-item)
- [Address](#address)
- [Shipment](#shipment)
- [Personalization objects](#personalization-objects)
- [Uploaded image](#uploaded-image)
- [Webhook](#webhook)
- [Support request](#support-request)

## Shop

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Use as `{shop_id}` |
| `title` | string | |
| `sales_channel` | string | Channel name, or `"disconnected"` |

## Catalog objects

**Blueprint** — `id`, `title`, `description`, `brand` (blank manufacturer), `model` (manufacturer style code), `images[]` (URLs), `tags[]` (single-get only, e.g. `"Early Access"`).

**Print provider** — `id`, `title`, `location{address1, address2, city, country, region, zip}` (return address). In the per-blueprint list, providers carry `decoration_methods[]` instead of location. In the single-get, `blueprints[]` lists what the provider offers.

**Catalog variant** (from `.../variants.json`):

| Field | Notes |
|-------|-------|
| `id` | Variant id used in product `variants[].id`, `print_areas[].variant_ids`, and order `variant_id` |
| `title` | e.g. `"Heather Grey / XS"` |
| `options` | Object of up to 3 option name→value, e.g. `{color, size}` |
| `placeholders[]` | Printable positions, see below |
| `decoration_methods[]` | e.g. `dtg`, `dtf`, `embroidery`, `sublimation` |

**Placeholder** (catalog) — `position` (e.g. `front`, `back`, `front_dtf`, `large_center_embroidery`), `decoration_method`, `height`, `width` (pixels). Choosing a position also chooses the decoration method; a blueprint may expose several front positions, one per method.

## Catalog shipping (V1 profiles)

`handling_time{value, unit}` plus `profiles[]`, each `{variant_ids[], first_item{currency, cost}, additional_items{currency, cost}, countries[]}`. `countries` may contain `REST_OF_THE_WORLD`. `first_item` applies to the first line item of that blueprint+provider in an order; `additional_items` to every further unit.

## Product

| Field | R/W | Notes |
|-------|-----|-------|
| `id` | RO | |
| `title` | required | |
| `description` | required | HTML allowed for channels that support it |
| `safety_information` | optional | GPSR text; also readable as structured blocks via the `gpsr.json` endpoint |
| `tags[]` | optional | Published to the sales channel |
| `options[]` | RO | `[{name, type, values:[{id, title, colors[]?}]}]`, up to 3 |
| `variants[]` | required | See [Product variant](#product-variant); on create only `id` and `price` are needed |
| `images[]` | RO | Mock-ups, see below |
| `created_at`, `update_at` | RO | Note the API's `update_at` spelling |
| `visible` | RO | Visibility in the sales channel, default true |
| `blueprint_id`, `print_provider_id` | required on create, RO after | |
| `user_id`, `shop_id` | RO | |
| `print_areas[]` | required | See below |
| `print_details` | optional | `{print_on_side: regular \| mirror \| off}` for canvases; clocks also take `separator_type` (`Numbers`, `Lines`, `None`) + `separator_color` hex |
| `external[]` | conditional | `[{id, handle, shipping_template_id?}]`; `id`/`handle` set via `publishing_succeeded`; `shipping_template_id` may be passed on create/update |
| `is_locked` | RO | True while publishing; updates rejected |
| `is_printify_express_eligible`, `is_economy_shipping_eligible` | RO | Any variant eligible |
| `is_printify_express_enabled` | optional | Only settable when eligible; default false |
| `is_economy_shipping_enabled` | RO | |
| `sales_channel_properties` | optional | Channel-specific object, see below; null or `[]` for custom API stores |
| `views[]` | RO | `[{id, label, position, files:[{src, variant_ids[]}]}]` blank product art with print areas |

## Product variant

| Field | R/W | Notes |
|-------|-----|-------|
| `id` | required | Catalog variant id |
| `price` | required | Retail price, cents |
| `sku` | optional | Generated if omitted; usable as an order line-item key |
| `cost` | RO | Fulfillment cost, cents |
| `title`, `grams` | RO | |
| `is_enabled` | optional | Offered/published; default true |
| `is_default` | optional | Exactly one; its mock-up becomes the title image |
| `is_available` | RO | Stock status |
| `is_printify_express_eligible` | RO | |
| `options[]` | RO | Option value ids |

## Print area, placeholder, image layer, pattern

```json
"print_areas": [{
  "variant_ids": [123, 124],
  "placeholders": [{
    "position": "front",
    "decoration_method": "dtg",        // read-only, derived from position
    "images": [{
      "id": "5d15ca551163cde90d7b2203",  // upload id (required)
      "x": 0.5, "y": 0.5, "scale": 1, "angle": 0,   // required
      "pattern": { "spacing_x": 1, "spacing_y": 1, "angle": 0, "offset": 0 }   // optional repeat tile
    }]
  }]
}]
```

Every print area lists the variants it covers; a variant should appear in exactly one print area. Read-only image fields returned on GET: `src`, `name`, `type` (`image/png`, `image/jpg`, `image/jpeg`), `height`, `width`, and text-layer fields (`font_family`, `font_size`, `font_weight`, `font_color`, `font_style`, `input_text`, `text_align`) for layers created in the Printify designer.

**Pattern:** `spacing_x`/`spacing_y` are relative to image width/height (1 = edge to edge, 0.5 = overlap by half, 1.5 = 50% gap); `angle` in −45..45; `offset` in −1..1 (0.5 gives a brick layout).

## Image positioning coordinate system

- Placeholder space is `[0,0]..[1,1]` with the center at `x=0.5, y=0.5`.
- `scale` is image width relative to placeholder width: `1` fills the width, `0.5` fills half. Any positive float.
- `angle` is degrees, 0..360.
- Artwork at placeholder width with `scale=1, x=0.5, y=0.5, angle=0` fills the print area exactly.
- Printify validates effective DPI; too-small artwork fails with error 8203 "Image has low quality". Match the placeholder's pixel `width`/`height` from the catalog.

## Mock-up image, option, view

**Mock-up** (`product.images[]`) — `src`, `variant_ids[]`, `position` (camera angle), `is_default` (title image). Mock-ups are generated server-side after create/update and may take a moment to appear.

**Option** — `{name, type (color | size | surface | ...), values:[{id, title, colors:[hex]?}]}`.

**View** — `{id, label, position, files:[{src, variant_ids[]}]}` blank-product SVG/PNG with print area outlines.

## Sales channel properties

Only populated for Printify-managed channels:

| Channel | Fields |
|---------|--------|
| Amazon | `free_shipping`, `bullet_points[]`, `no_variation_parent`, `brand_name` |
| Etsy | `free_shipping`, `personalisation{instructions, buyer_response_limit}` |
| BigCommerce | `categories[]`, `free_shipping` |
| eBay | `free_shipping` |
| Shopify | `collections[]`, `free_shipping` |
| Squarespace | `store_page` |
| TikTok | `delivery_service_id`, `warehouse_id`, `free_shipping`, `personalisation` |

## Publishing flags

Body of `publish.json` and `publish_details` in the `product:publish:started` event: `title`, `description`, `images`, `variants`, `tags` (all boolean, required), `keyFeatures` (request) / `key_features` (event), `shipping_template` (Etsy and Amazon only). `false` means "leave that attribute alone on the channel".

## Order

| Field | Notes |
|-------|-------|
| `id` | |
| `app_order_id` | Printify web-app order number (e.g. `"215014.44"`), read-only, not filterable |
| `address_to` | See [Address](#address); response adds `company` |
| `line_items[]` | See [Line item](#line-item) |
| `metadata` | `{order_type: external \| manual \| sample \| api, shop_order_id, shop_order_label, shop_fulfilled_at, is_reprint, reprinted_order_ids[], child_reprinted_order_ids[]}` |
| `total_price`, `total_shipping`, `total_tax` | cents |
| `status` | See enum below |
| `shipping_method` | 1 standard, 2 priority, 3 Printify Express, 4 economy |
| `is_printify_express`, `is_economy_shipping` | booleans |
| `shipments[]` | See [Shipment](#shipment) |
| `created_at`, `sent_to_production_at`, `fulfilled_at` | |
| `printify_connect` | `{url, id}` buyer-facing order page |

Submit-only fields: `external_id` (required, unique per shop), `label` (optional display label), `send_shipping_notification` (bool).

## Order status enum

| Status | Meaning |
|--------|---------|
| `pending` | Just created; should not linger |
| `on-hold` | Awaiting merchant action (discontinued/out-of-stock items, shipping restrictions, or created with manual approval). Editable. Cancelable. |
| `cost-calculation` | Cost calculation in progress |
| `payment-not-received` | Charge failed; merchant can retry. Cancelable. |
| `sending-to-production` | Picked for dispatch to providers |
| `in-production` | Providers accepted the order |
| `partially-fulfilled` | Some line items fulfilled |
| `fulfilled` | Terminal success |
| `canceled` | Terminal |
| `has-issues` | e.g. invalid address |
| `unfulfillable` | Inventory or technical failure |
| `source-check-failed` | Source file validation failed |
| `sending_to_production_delegate`, `sending_to_production_delegate_sync` | Delegated external production |

Line item statuses are a subset: `on-hold`, `sending-to-production`, `in-production`, `fulfilled`, `canceled`, `has-issues`.

## Line item

| Field | Notes |
|-------|-------|
| `product_id`, `variant_id`, `print_provider_id` | |
| `external_id` | Your line id; echoed in `metadata.external_id`; preserved through reprints/routing |
| `quantity` | |
| `cost`, `shipping_cost` | cents |
| `status` | see above |
| `metadata` | `{title, price, variant_label, sku, country (provider location), external_id}` |
| `sent_to_production_at`, `fulfilled_at` | |

## Address

`first_name`, `last_name`, `email`, `phone`, `country` (ISO-2), `region`, `address1`, `address2`, `city`, `zip`. Required on submit: name, `address1`, `city`, `country`, `zip` (region may be `""`). `email` and `phone` are required for Printify Express.

## Shipment

`{carrier, number, url, delivered_at}`. Carrier codes are lowercase in order responses (`usps`) and uppercase in webhook payloads (`USPS`).

## Personalization objects

**Option** — `{field_id, label, type: "textbox" | "image", text_options{character_limit}?}`.

**Config request item** — `{field_id, type, input: {text} | {image_id}}`; response `{personalisation_strategy, personalisation_instructions}` (opaque tokens).

**Preview task** — `{task_id, status, external_id?, preview_count?, mockups?:[{variant_id, mockup_id ("Front"/"Back"), src}], error?:{message, code}}`. Statuses: `pending`, `processing`, `completed`, `failed` (retry), `corrupt` (terminal).

**Line item personalisation** — `{personalisation_strategy, personalisation_instructions, buyer_request?, layers?:[{personalisation_id, name, layer_type: text | image, text_input?, image_id?}], personalisation_buyer_confirmation?:{approved, source, date, ip_address?, user_agent?}}`. A deprecated top-level `line_items[].personalisation_instructions` is still accepted but overridden by the nested one.

## Uploaded image

`{id, file_name, height, width, size (bytes), mime_type, preview_url, upload_time}`. Use `id` in product `print_areas[].placeholders[].images[].id`.

## Webhook

`{id, topic, url, shop_id, secret?}`. `topic` is immutable after creation. `secret` is write-only and used for the `X-Pfy-Signature` HMAC.

## Support request

`{id, order_id, type: order_reprint | order_refund | order_address_editing, status (pending | processing | in_progress | ...), status_details, outcome (unresolved | ...), line_item_ids[], created_at, updated_at}`. The enum values beyond those seen in the OpenAPI examples are not documented.
