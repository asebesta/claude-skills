---
name: trmnl-plugins
description: Build custom private plugins and dashboards for TRMNL e-ink displays (including the TRMNL X). Covers the data layer (webhook push, polling, plugin-merge strategies), the Liquid templating + custom filters used to render data, and the TRMNL Design Framework 3.1 markup (views, mashups, items, tables, charts, typography, responsive/bit-depth utilities). Use when creating or editing a TRMNL private plugin, designing dashboard layouts, writing plugin markup/Liquid, sending data via webhook or polling, embedding charts, or troubleshooting TRMNL screen rendering. Triggers on TRMNL, TRMNL X, usetrmnl, trmnl.com, private plugins, e-ink dashboards, or "merge variables" templates.
---

# TRMNL Private Plugins & Dashboards

Build custom plugins for TRMNL e-ink displays. A TRMNL plugin = a **data strategy** (how data gets to TRMNL) + **Liquid markup** (how it renders) using the **Design Framework 3.1** CSS.

## Device targets (important)

There is no single screen size. Target the framework's responsive tiers; never hardcode pixels.

| Device | Resolution | Density tier | Breakpoint |
|--------|-----------|--------------|------------|
| TRMNL OG | 800×480 | `1bit:` (2 shades) | `md:` |
| TRMNL OG V2 | 800×480 | `2bit:` (4 shades) | `md:` |
| TRMNL V2 | 1024×758 | `4bit:` (16 shades) | `lg:` |
| **TRMNL X** | **1872×1404, 10.3"** | **`4bit:` (16 shades)** | **`lg:`** |

The user has a **TRMNL X**: high-density, 16-level grayscale. Make the responsive base case work everywhere, then use `lg:` / `4bit:` prefixes to exploit the larger grayscale panel. Use real grayscale (`text--gray-50`, dithered images), not just black/white.

## Workflow for building a plugin

1. **Pick a data strategy** — Webhook (push) or Polling (pull). See `references/data-strategies.md`.
2. **Shape the data** — decide the JSON keys the template reads. Keep merge data flat at the root.
3. **Write markup for each layout** — plugins have four layout tabs: `full`, `half_horizontal`, `half_vertical`, `quadrant`, plus a **Shared** tab for reusable markup/CSS/JS. Start from `assets/scaffolds/`. At minimum fill `full`.
4. **Render data with Liquid** — `{{ variable }}`, loops, custom filters. See `references/liquid-filters.md`.
5. **Style with the framework** — never invent classes. See `references/framework.md`.
6. **Test** — Force Refresh in the editor; verify overflow/clamping on the target device.

A private plugin is created in the TRMNL web UI: device dropdown → gear → **Developer perks** (one-time upgrade) → **Private Plugin**. Markup is entered per layout tab in the "Edit Markup" editor.

## The single most important markup rule

You write **view-level** markup. TRMNL wraps it in the `<html>` / `<body class="environment trmnl">` / `<div class="screen">` shell and injects `plugins.css` + `plugins.js` automatically. Every layout's markup starts at the `view`:

```html
<div class="view view--full">
  <div class="layout">
    <!-- your content -->
  </div>
  <div class="title_bar">
    <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
    <span class="title">My Plugin</span>
    <span class="instance">{{ trmnl.plugin_settings.instance_name }}</span>
  </div>
</div>
```

Match the view modifier to the layout tab: `view--full`, `view--half_horizontal`, `view--half_vertical`, `view--quadrant`.

## Liquid syntax note

TRMNL uses standard **Liquid** (Shopify): data with `{{ variable }}`, logic with `{% ... %}`. Some TRMNL docs render the braces as `##{{ ... }}` — that `##` is **documentation escaping only**; in the editor use plain `{{ ... }}`. Custom form fields interpolate the same way: `{{ api_key }}`.

## Reference files

Read the one matching the task — don't load all of them up front.

- **`references/data-strategies.md`** — Webhook (URL, `merge_variables`, limits, curl) and Polling (`polling_url`, multiple URLs → `IDX_0`/`IDX_1`, headers/body, verbs), Plugin Merge / data-only mode, form fields, and the `trmnl` global object.
- **`references/liquid-filters.md`** — All TRMNL custom Liquid filters (`number_to_currency`, `l_date`, `group_by`, `find_by`, `where_exp`, `qr_code`, `append_random`, `parse_json`, …) plus common Shopify filters, with examples.
- **`references/framework.md`** — Design Framework 3.1 markup: views & mashups, layout/columns/grid/flex, item, table, value/format_value, typography & responsive prefixes, color tokens, image/dithering, progress, rich text, clamp/overflow modulations.
- **`references/charts-and-recipes.md`** — Embedding Highcharts/Chartkick charts (e-ink-safe config), worked dashboard examples (single metric, multi-column, list/schedule), and a troubleshooting checklist.

## Scaffolds

`assets/scaffolds/` holds copy-paste starter markup. Copy the relevant file into the matching layout tab and replace the placeholders:

- `full.liquid`, `half_horizontal.liquid`, `half_vertical.liquid`, `quadrant.liquid` — empty-but-correct shells for each layout.
- `schedule-full.liquid` — a worked list/schedule dashboard (loops over events with date/time formatting and overflow handling).

## Hard-won rules

- **Keep merge data flat.** Send `{ "events": [...] }`, not `{ "data": { "events": [...] } }`. Webhook payloads go under `merge_variables`; polling JSON is read from the root (single URL) or `IDX_n` (multiple URLs).
- **Disable all animation** in charts (`animation: false`) — TRMNL screenshots the page once; animated charts capture half-rendered.
- **Always handle overflow.** Lists/tables clip silently. Use `data-clamp="N"`, `data-list-limit="true"`, `data-table-limit="true"`, or cap items in Liquid (`limit:`).
- **Identical merge data skips re-render.** If a screen doesn't update, the data was unchanged — use Force Refresh.
- **Wrap all client JS** in `document.addEventListener("DOMContentLoaded", function(e){ ... })`.
- **Respect limits.** Webhook: free 2 KB & 12×/hr, TRMNL+ 5 KB & 30×/hr. Polling refresh intervals: 15 / 60 / 360 / 720 / 1440 min.
