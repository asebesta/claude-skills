# Liquid Filters for TRMNL

TRMNL templates use standard **Liquid** (Shopify) plus TRMNL-specific custom filters. Syntax: `{{ value | filter: arg }}`. Logic uses `{% if %}`, `{% for %}`, `{% assign %}`, `{% capture %}`.

## Contents
- [TRMNL custom filters](#trmnl-custom-filters)
- [Commonly used standard Liquid filters](#commonly-used-standard-liquid-filters)
- [Date/time formatting (strftime)](#datetime-formatting-strftime)
- [Patterns](#patterns)

---

## TRMNL custom filters

### Data
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `json` | Serialize a variable to JSON | `{{ my_var \| json }}` → `{"foo":"bar"}` |
| `parse_json` | Parse a JSON string into an object | `{% assign parsed = data.stuff \| parse_json %}` then `{{ parsed.num }}` → `5` |

### Collections
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `group_by` | Group array of objects by a key | `{{ people \| group_by: "age" }}` → `{35 => [...], 29 => [...]}` |
| `find_by` | Find first item by key/value (optional fallback arg) | `{{ people \| find_by: "name", "Ryan" }}` → `{"age"=>35,"name"=>"Ryan"}` |
| `where_exp` | Filter array by an expression | `{{ numbers \| where_exp: "n", "n >= 3" }}` → `[3,4,5]` |
| `sample` | Random element | `{{ isbns \| split: ',' \| sample }}` |

### Numbers
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `number_with_delimiter` | Thousands separators | `{{ 1234 \| number_with_delimiter }}` → `1,234` |
| `number_to_currency` | Currency formatting | `{{ 10420 \| number_to_currency }}` → `$10,420.00` |

### Strings / markup
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `pluralize` | Pluralize a word for a count | `{{ "book" \| pluralize: 2 }}` → `2 books` |
| `markdown_to_html` | Render markdown to HTML | `{{ markdown \| markdown_to_html }}` |

### Dates
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `days_ago` | Date N days before today | `{{ 7 \| days_ago }}` → `yyyy-mm-dd` |
| `ordinalize` | strftime with ordinal day | `{{ "2025-10-02" \| ordinalize: "%A, %B <<ordinal_day>>, %Y" }}` → `Thursday, October 2nd, 2025` |
| `l_date` | Localize a date (object or string) | `{{ '2025-01-11' \| l_date: '%y %b', 'ko' }}` → `25 1월` |
| `l_word` | Translate a common word | `{{ "today" \| l_word: 'es-ES' }}` → `hoy` |

### Utility
| Filter | Purpose | Example → Output |
|--------|---------|------------------|
| `append_random` | Append a random suffix (unique element IDs) | `{% assign id = "chart-" \| append_random %}` → `chart-q7x1` |
| `qr_code` | String/URL → scannable QR image (size arg) | `{{ "https://trmnl.ink" \| qr_code: 3 }}` |

> Use `append_random` for any element a script targets (chart containers especially) so multiple instances / mashups don't collide on the same `id`.

---

## Commonly used standard Liquid filters

`upcase` `downcase` `capitalize` `truncate: 15` `truncatewords: 8` `strip` `strip_html`
`split: ','` `join: ', '` `first` `last` `size` `reverse` `sort` `uniq` `map: 'key'`
`where: 'key', value` `slice: 0, 3` `replace: 'a','b'` `default: 'N/A'`
`plus:` `minus:` `times:` `divided_by:` `modulo:` `round:` `ceil` `floor` `abs`
`date: '%b %-d'` `escape` `url_encode`

```liquid
{{ title | truncate: 24 }}
{{ events | map: 'title' | join: ', ' }}
{{ price | default: 0 | number_to_currency }}
{{ events | where: 'status', 'confirmed' | size }}
```

---

## Date/time formatting (strftime)

`l_date`, `ordinalize`, and standard `date` use Ruby strftime tokens:

| Token | Meaning | Example |
|-------|---------|---------|
| `%Y` `%y` | Year (4 / 2 digit) | 2026 / 26 |
| `%B` `%b` | Month name / abbrev | August / Aug |
| `%m` | Month (zero-padded) | 08 |
| `%A` `%a` | Weekday / abbrev | Saturday / Sat |
| `%d` `%-d` | Day (padded / no pad) | 01 / 1 |
| `%H:%M` | 24h time | 17:00 |
| `%-I:%M %p` | 12h time | 5:00 PM |
| `%Z` `%z` | TZ name / offset | CDT / -0500 |

`ordinalize` adds `<<ordinal_day>>` for "1st / 2nd / 3rd". Pass a locale to `l_date` as the 2nd arg, or use `trmnl.user.locale`.

---

## Patterns

```liquid
{# Localize to the user's settings #}
{{ event.date | l_date: '%a %b %-d', trmnl.user.locale }}

{# Parse a JSON string field, then read it #}
{% assign cfg = settings_json | parse_json %}
{{ cfg.threshold }}

{# Find one record, with fallback #}
{% assign me = people | find_by: 'id', user_id %}
{{ me.name | default: 'Unknown' }}

{# Filter + count #}
{% assign open = tickets | where_exp: 't', 't.status != "closed"' %}
{{ open | size }} {{ "ticket" | pluralize: open.size }}

{# Unique chart id (avoid collisions in mashups) #}
{% assign chart_id = 'chart-' | append_random %}
<div id="{{ chart_id }}"></div>
```
