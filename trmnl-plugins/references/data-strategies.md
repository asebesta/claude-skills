# TRMNL Data Strategies

How data reaches a private plugin and becomes merge variables in the template. Choose one strategy per plugin.

## Contents
- [Webhook (push)](#webhook-push)
- [Polling (pull)](#polling-pull)
- [Plugin Merge / data-only](#plugin-merge--data-only)
- [Form fields (custom settings)](#form-fields-custom-settings)
- [The `trmnl` global object](#the-trmnl-global-object)
- [Reading data in the template](#reading-data-in-the-template)

---

## Webhook (push)

You POST JSON to TRMNL. No server required — drive it from a cron job, Apple Shortcut, Google Apps Script, Cloudflare Worker, GitHub Action, etc.

**Endpoint** (the plugin's Webhook URL, shown in the plugin's settings form):
```
POST https://usetrmnl.com/api/custom_plugins/{PLUGIN_SETTINGS_UUID}
```
(Older docs use `trmnl.com`; both resolve. The UUID is the plugin instance's Plugin Settings UUID.)

**Body** — data MUST be wrapped in `merge_variables`, kept flat:
```json
{ "merge_variables": { "text": "You can do it!", "author": "Rob Schneider" } }
```

**Full example:**
```bash
curl "https://usetrmnl.com/api/custom_plugins/asdfqwerty1234" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"merge_variables": {"text":"You can do it!", "author": "Rob Schneider"}}'
```

In the template these are read at the root: `{{ text }}`, `{{ author }}`.

**Read back current data:** `GET` the same URL.

**Limits:**
| | Free | TRMNL+ |
|---|---|---|
| Payload size | 2 KB | 5 KB |
| Requests/hour | 12 | 30 |

Exceeding the rate returns HTTP `429`. To send more than 2/5 KB, switch to Polling. Each POST **replaces** the stored merge variables (it is not append/merge), so send the complete payload each time.

---

## Polling (pull)

TRMNL fetches URL(s) you control on an interval. Best when you already have an API/feed, or need larger payloads than webhook allows.

**Configuration fields:**
- **Polling URL(s)** — one or more URLs, line-break separated. Each may return JSON, RSS, XML, plaintext, or CSV.
- **Polling Verb** — `GET` (default) or `POST`.
- **Polling Headers** — ampersand-joined `key=value` pairs:
  ```
  authorization=bearer xxx&content-type=application/json
  ```
- **Polling Body** — JSON object (for POST). Interpolate form fields with `{{ form_field_keyname }}`.
- **Refresh interval** — 15, 60, 360, 720, or 1440 minutes.

**Accessing the response:**
- **Single URL** → response is read directly at the root: `{{ field_name }}`, `{{ items[0].name }}`.
- **Multiple URLs** → each response is namespaced by index: `{{ IDX_0.field_name }}`, `{{ IDX_1.field_name }}` (in URL order).

Interpolate form-field values into the URL/headers/body for secrets and per-instance config:
```
https://api.example.com/v1/data?key={{ api_key }}
```

---

## Plugin Merge / data-only

Use the **Plugin Merge** strategy to combine/transform data already produced by other plugin instances, or to use a plugin purely as a data source (data-only mode).

- All connected plugin data becomes available in the template under the **"Your Variables"** dropdown.
- For data-only: connect a plugin instance to your Playlist and hide it (eyeball icon). Parsed data appears under a `<plugin_keyname>_<plugin_setting_id>` node in the Merge Variables dropdown.
- Preview parsed data at `https://usetrmnl.com/plugins/demo?data=true&plugin_setting_id=<id>`.

---

## Form fields (custom settings)

Define GUI inputs on the plugin so each instance can be configured without editing markup. Field types include text, number, select, etc. Each has a **keyname**.

Reference a field anywhere — markup, polling URL, headers, or body — by keyname:
```
{{ api_key }}        {{ city }}        {{ units }}
```

Use form fields for API keys, locations, thresholds, display toggles — anything that varies per instance.

---

## The `trmnl` global object

Always available in templates regardless of strategy. Common paths:

| Path | Value |
|------|-------|
| `trmnl.user.first_name` | User's first name |
| `trmnl.user.name` | Full name |
| `trmnl.user.locale` | Locale (e.g. `en`) |
| `trmnl.user.time_zone` / `trmnl.user.utc_offset` | Timezone info |
| `trmnl.plugin_settings.instance_name` | This instance's name (good for the `title_bar` `instance` span) |
| `trmnl.plugin_settings.custom_fields_values.<keyname>` | A form field value (alternative to bare `{{ keyname }}`) |

Use these to localize dates (`l_date` with `trmnl.user.locale`) and label the title bar.

---

## Reading data in the template

```liquid
{# webhook or single polling URL: root access #}
<span class="value">{{ temperature }}</span>

{# loop a collection #}
{% for event in events limit: 6 %}
  <div class="item">{{ event.title }} — {{ event.date | l_date: '%b %-d' }}</div>
{% endfor %}

{# multiple polling URLs #}
<span>{{ IDX_0.weather.temp }}</span>
<span>{{ IDX_1.headlines[0].title }}</span>

{# guard for missing data #}
{% if events == empty or events == nil %}
  <span class="label">No upcoming events</span>
{% endif %}
```

Tip: a string of JSON inside a field can be turned into an object with `| parse_json` (see `liquid-filters.md`).
