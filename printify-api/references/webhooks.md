# Printify Events and Webhooks

Webhook CRUD endpoints are in [endpoints.md](endpoints.md#webhooks). This file covers event topics, payload shapes, delivery rules, and signature verification.

## Contents

- [Event topics](#event-topics)
- [Event envelope](#event-envelope)
- [Resource data by topic](#resource-data-by-topic)
- [Delivery and retries](#delivery-and-retries)
- [Verifying signatures](#verifying-signatures)
- [Receiver skeleton](#receiver-skeleton)

## Event topics

| Topic | Fires when |
|-------|-----------|
| `shop:disconnected` | The shop was disconnected from the account |
| `product:created` | Product created |
| `product:updated` | Product updated |
| `product:deleted` | Product deleted |
| `product:publish:started` | Publish requested (API or the Printify app's Publish button); product is now locked |
| `order:created` | Order created |
| `order:updated` | Order status changed |
| `order:sent-to-production` | Order dispatched to print providers |
| `order:shipment:created` | Some or all items shipped (tracking available) |
| `order:shipment:delivered` | Some or all items delivered |
| `personalization-preview-task:processed` | A preview task reached `completed`, `failed`, or `corrupt` |

## Event envelope

```json
{
  "id": "653b6be8-2ff7-4ab5-a7a6-6889a8b3bbf5",
  "type": "order:shipment:created",
  "created_at": "2022-05-17 15:00:00+00:00",
  "resource": {
    "id": "5cb87a8cd490a2ccb256cec4",
    "type": "order",
    "data": { ... }
  }
}
```

`resource.type` is one of `shop`, `product`, `order`, `personalization-preview-task`. `resource.id` is the affected object's id (an int for shops). Payloads carry only ids and small deltas; fetch the full object with the REST API when needed.

## Resource data by topic

| Topic | `resource.data` |
|-------|-----------------|
| `shop:disconnected` | `null` |
| `product:created` / `updated` / `deleted` | `{shop_id}` |
| `product:publish:started` | `{shop_id, action: "create" \| "update", publish_details: {title, description, images, variants, tags, key_features, shipping_template}}` or `{action: "delete"}` |
| `order:created` | none |
| `order:updated` | `{shop_id, status}` (see order status enum in schemas.md) |
| `order:sent-to-production` | none |
| `order:shipment:created` | `{shop_id, shipped_at, carrier: {code, tracking_number}, skus[]}` |
| `order:shipment:delivered` | `{shop_id, delivered_at, carrier: {code, tracking_number}, skus[]}` |
| `personalization-preview-task:processed` | `{task_id, status, shop_id, preview_count?, mockups?:[{variant_id, mockup_id, src}], error?:{message, code}}` |

Publish flow for a custom store: on `product:publish:started`, read `publish_details` to learn which attributes to sync, build the listing on your channel, then call `publishing_succeeded.json` with the external id/handle (or `publishing_failed.json`) to unlock the product. Shipment events identify items by SKU, so set meaningful `sku` values on product variants.

## Delivery and retries

- Printify sends `POST {url}` with the JSON envelope; reply `200` quickly and process asynchronously.
- On any 4xx/5xx Printify retries up to 3 times, then **blocks the webhook for 1 hour**. Deliveries during the block are lost.
- Deliveries are not guaranteed to be ordered or unique; dedupe on the event `id`.
- Deleting a webhook requires `?host=` matching the URL's host as a safeguard.
- `POST .../webhooks/{id}/simulate` sends a test delivery; whatever JSON you post is echoed in `resource`.

## Verifying signatures

Set `secret` when creating the webhook (generate with `openssl rand -hex 20`). Printify signs the raw request body with HMAC-SHA256 and sends `X-Pfy-Signature: sha256={hexdigest}`. Compare in constant time.

```python
import hmac, hashlib, os

def verify(raw_body: bytes, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        os.environ["PRINTIFY_WEBHOOK_SECRET"].encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")
```

```js
import crypto from "node:crypto";

export function verify(rawBody, signatureHeader) {
  const expected = "sha256=" + crypto
    .createHmac("sha256", process.env.PRINTIFY_WEBHOOK_SECRET)
    .update(rawBody)
    .digest("hex");
  const a = Buffer.from(expected), b = Buffer.from(signatureHeader || "");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}
```

Hash the **raw** bytes, not a re-serialized JSON object; frameworks that parse the body first must expose the original buffer.

## Receiver skeleton

```python
from flask import Flask, request, abort

app = Flask(__name__)

@app.post("/printify/webhook")
def printify_webhook():
    if not verify(request.get_data(), request.headers.get("X-Pfy-Signature")):
        abort(401)
    event = request.get_json()
    topic, resource = event["type"], event["resource"]
    if topic == "order:shipment:created":
        enqueue_tracking_email(order_id=resource["id"], **resource["data"]["carrier"])
    elif topic == "product:publish:started":
        enqueue_publish(product_id=resource["id"], details=resource["data"].get("publish_details"))
    return "", 200
```

Register one webhook per topic; a single URL may serve all of them.
