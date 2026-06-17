# TRMNL Design Framework 3.1 — Markup Reference

Use these classes; do not invent class names. The framework's `plugins.css`/`plugins.js` are auto-injected by TRMNL. Canonical docs: https://trmnl.com/framework/docs/3.1

## Contents
- [Structural scaffold](#structural-scaffold)
- [Views & layout tabs](#views--layout-tabs)
- [Mashups](#mashups)
- [Layout, columns, grid, flex](#layout-columns-grid-flex)
- [Title bar](#title-bar)
- [Item](#item)
- [Value & Format Value](#value--format-value)
- [Table](#table)
- [Progress](#progress)
- [Rich text](#rich-text)
- [Typography](#typography)
- [Color tokens](#color-tokens)
- [Images & dithering](#images--dithering)
- [Spacing & sizing utilities](#spacing--sizing-utilities)
- [Responsive & bit-depth prefixes](#responsive--bit-depth-prefixes)
- [Overflow / clamp modulations](#overflow--clamp-modulations)

---

## Structural scaffold

Fixed hierarchy: **Screen → View → Layout → (content) → Title Bar**. You write from the `view` down (TRMNL provides `screen`):

```html
<div class="view view--full">
  <div class="layout">
    <!-- content -->
  </div>
  <div class="title_bar">
    <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
    <span class="title">Plugin Title</span>
    <span class="instance">{{ trmnl.plugin_settings.instance_name }}</span>
  </div>
</div>
```

## Views & layout tabs

One view modifier per layout tab:

| Tab | View class | Approx. footprint |
|-----|-----------|-------------------|
| full | `view--full` | whole screen |
| half_horizontal | `view--half_horizontal` | top or bottom half |
| half_vertical | `view--half_vertical` | left or right half |
| quadrant | `view--quadrant` | one quarter |

## Mashups

A mashup arranges multiple views on one screen. The mashup modifier sets the arrangement; each child view's own modifier sets its footprint.

```html
<div class="mashup mashup--1Lx1R">
  <div class="view view--half_vertical"> ... </div>
  <div class="view view--half_vertical"> ... </div>
</div>
```

Modifiers: `mashup--1Lx1R` (1 left, 1 right), `mashup--1Tx1B` (top/bottom), `mashup--1Lx2R`, `mashup--2Lx1R`, `mashup--2Tx1B`, `mashup--1Tx2B`, `mashup--2x2`.

## Layout, columns, grid, flex

**Layout** is the primary content container inside a view:
```html
<div class="layout layout--col gap--space-between"> ... </div>
```
- `layout--col` stacks children vertically; combine with `gap--*` (e.g. `gap--space-between`).

**Columns** (legacy column system):
```html
<div class="columns"><div class="column"> ... </div><div class="column"> ... </div></div>
```

**Grid** (preferred for tiled metrics):
- `grid` + `grid--cols-{1..N}` — fixed column count.
- `grid--wrap` — responsive wrapping; `grid--min-{n}` sets a minimum track size (`grid--min-32`, `grid--min-56`).
- Cells: `col` (vertical), `col--span-{n}`, alignment `col--start|col--center|col--end`; `row` with `row--start|row--center|row--end`.

```html
<div class="grid grid--cols-3 gap--small">
  <div class="item"> ... </div>
  <div class="item"> ... </div>
  <div class="item"> ... </div>
</div>
```

**Flex:** `flex` with `gap--*`; combine with the spacing/alignment utilities below.

## Title bar

```html
<div class="title_bar">
  <img class="image" src="/images/plugins/trmnl--render.svg">
  <span class="title">Calendar</span>
  <span class="instance">Production</span>   <!-- optional instance label -->
</div>
```
Classes: `title_bar`, `image`, `title`, `instance`.

## Item

A list row with optional meta (index/icon), title, description, and labels.

```html
<div class="item">
  <div class="meta"><span class="index">1</span></div>   <!-- meta optional; index optional -->
  <div class="content">
    <span class="title title--small">Team Meeting</span>
    <span class="description">Weekly team sync-up</span>
    <div class="flex gap--small">
      <span class="label label--small label--underline">9:00 AM – 10:00 AM</span>
      <span class="label label--small label--underline">Confirmed</span>
    </div>
  </div>
</div>
```

With an icon instead of an index:
```html
<div class="item">
  <div class="meta"></div>
  <div class="icon"><img src="icon.svg" class="w--[6cqw] h--[6cqw]" /></div>
  <div class="content">
    <span class="value value--small">72°</span>
    <span class="label">Temperature</span>
  </div>
</div>
```

Classes: `item`, `meta`, `content`, `icon`, `index`; children `title`/`title--small`, `description`, `label`/`label--small`/`label--underline`, `value`/`value--small`. Emphasis modifiers: `item--emphasis-1|2|3`.

## Value & Format Value

Big numbers. Add `data-value-format="true"` to auto-format, `value--tnums` for tabular (aligned) digits.

```html
<span class="value value--xlarge value--tnums" data-value-format="true">2345678</span>
<span class="value value--large  value--tnums" data-value-format="true" data-fit-value="true">$456789</span>
<span class="value value--small  value--tnums" data-value-format="true" data-value-locale="de-DE">€123456.78</span>
```
- Sizes: `value--small`, (default), `value--large`, `value--xlarge` (plus `value--xxsmall`/`value--xsmall` for captions).
- Attributes: `data-value-format="true"`, `data-fit-value="true"` (shrink to fit width), `data-value-locale="en-US|de-DE|fr-FR|en-GB|ja-JP"`.
- Pair with a `label` for a captioned metric.

## Table

```html
<table class="table" data-table-limit="true">
  <thead>
    <tr><th><span class="title title--small">Header</span></th></tr>
  </thead>
  <tbody>
    <tr><td><span class="label">Cell</span></td></tr>
  </tbody>
</table>
```
- Base: `table`; index column: `table--indexed` (cells use `meta` + `index`).
- Size modifiers: `table--xsmall`, `table--small` (alias `table--condensed`), `table--base`, `table--large`, `table--xlarge`.
- Headers use `title`/`title--small`; cells use `label`/`label--small`.
- `data-table-limit="true"` enables overflow handling; `data-clamp="1"` truncates a cell to one line.

## Progress

Bar:
```html
<div class="progress-bar">
  <div class="content">
    <span class="label">Regular Progress</span>
    <span class="value value--xxsmall">50%</span>
  </div>
  <div class="track"><div class="fill" style="width: 50%"></div></div>
</div>
```
Dots:
```html
<div class="progress-dots">
  <div class="track">
    <div class="dot dot--filled"></div>
    <div class="dot dot--filled"></div>
    <div class="dot dot--current"></div>
    <div class="dot"></div>
  </div>
</div>
```
Sizes: `progress-bar--xsmall|small|base|large`, `progress-dots--xsmall|small|base|large`. Emphasis: `progress-bar--emphasis-2|3`. Parts: bar = `content`/`track`/`fill`; dots = `track`/`dot`/`dot--filled`/`dot--current`.

## Rich text

Center/align prose and markdown blocks:
```html
<div class="richtext richtext--center gap--large">
  <img class="image" src="/assets/trmnl--glyph-black-large.svg">
  <div class="content content--center gap text--center">
    <p>Center-aligned rich text content.</p>
  </div>
</div>
```
- Container align: `richtext--left|center|right`.
- Content size: `content--small|base|large|xlarge|xxlarge|xxxlarge`; align `content--left|center|right`.
- Auto-fit: `data-content-limiter="true"` (+ optional `data-content-max-height="140"`), `data-pixel-perfect="true"`.

## Typography

`text--{size}` sets font family, size, line-height, and smoothing per density tier:

| Class | Size / line-height |
|-------|--------------------|
| `text--small` | 12 / 1 |
| `text--base` | 16 / 1.25 |
| `text--large` | 21 / 1 |
| `text--xlarge` | 26 / 29 |
| `text--xxlarge` | 38 / 42 |
| `text--xxxlarge` | 58 / 70 |
| `text--mega` | 74 / 86 |
| `text--giga` | 96 / 108 |
| `text--tera` | 128 / 128 |
| `text--peta` | 170 / 180 |

Also: weight `font--bold`; alignment `text--left|center|right`; color via `text--{token}` (see below). On the high-density TRMNL X these use Inter Variable; on low-density panels a pixel font.

## Color tokens

CSS-variable tokens (use the utility classes, not raw vars):
- **Grayscale:** `--black`, `--gray-10` … `--gray-75`, `--white`. Classes: `text--gray-50`, `bg--gray-20`, etc.
- **Chromatic:** red, orange, yellow, lime, green, cyan, blue, violet, purple, pink — each with lightness steps 10–75 (e.g. `text--blue-60`, `bg--red-40`).
- **Semantic:** `--color-primary` (blue), `--color-success` (green), `--color-error` (red), `--color-warning` (orange) → `text--primary`, `bg--success`, etc.
- Backgrounds: `bg--{token}`; text color: `text--{token}` incl. `text--white` / `text--black`.

Note: TRMNL dark mode inverts the whole screen except images, so the palette can look inverted. On TRMNL X (16-shade) you have real grays — use `gray-*` for hierarchy instead of only black/white. (Legacy `gray-1`…`gray-7` map to `gray-10`…`gray-70`.)

## Images & dithering

```html
<img class="image image-dither rounded" src="path.png">
```
- `image` base; `image-dither` simulates grayscale via dither patterns (essential on 1-bit, still helps on grayscale); `rounded` optional.
- Object-fit: `image--fill`, `image--contain`, `image--cover`.

## Spacing & sizing utilities

- Gap: `gap`, `gap--small`, `gap--large`, `gap--space-between`.
- Arbitrary sizing (container-query units recommended): `w--[240px]`, `w--[6cqw]`, `h--[6cqw]`, `w--full`. `cqw`/`cqh` (% of container) scale across devices better than fixed px.

## Responsive & bit-depth prefixes

Mobile-first. Prefix order: **`size:orientation:bit-depth:utility`**.

| Kind | Prefixes | Activates |
|------|----------|-----------|
| Size | `sm:` / `md:` / `lg:` | ≥600px (Kindle) / ≥800px (TRMNL OG) / ≥1024px (TRMNL V2, **TRMNL X**) |
| Orientation | `portrait:` | portrait only (landscape is default, no prefix) |
| Bit-depth | `1bit:` / `2bit:` / `4bit:` | 2 / 4 / **16 (TRMNL X)** shades — NOT progressive, each targets one depth only |

```html
<span class="value value--large lg:value--xlarge 4bit:text--gray-60">42</span>
<div class="gap--small md:portrait:gap--large"> ... </div>
```

For TRMNL X, lean on `lg:` (bigger type/denser grids) and `4bit:` (grayscale depth).

## Overflow / clamp modulations

E-ink silently clips overflow — always constrain content.

- **`data-clamp="N"`** — clamp any text to N lines (engine re-applies on layout change). Responsive variants: `data-clamp-sm`, `data-clamp-md`, `data-clamp-lg`, `data-clamp-portrait`, `data-clamp-md-portrait`. (Legacy classes `clamp--1`…`clamp--50`, `clamp--none`.)
- **`data-list-limit="true"`** — auto-limit list items to what fits.
- **`data-table-limit="true"`** — auto-limit table rows to what fits.
- **`data-content-limiter="true"`** (+ `data-content-max-height`) — shrink rich text to fit.
- **`data-pixel-perfect="true"`** — snap text to the pixel grid for crisp e-ink rendering.

Also cap in Liquid as a backstop: `{% for x in items limit: 8 %}`.
