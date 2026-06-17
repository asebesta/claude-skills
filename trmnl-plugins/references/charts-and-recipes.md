# Charts & Dashboard Recipes

## Contents
- [Charts (Highcharts / Chartkick)](#charts-highcharts--chartkick)
- [Recipe: single big metric](#recipe-single-big-metric)
- [Recipe: multi-metric grid](#recipe-multi-metric-grid)
- [Recipe: list / schedule](#recipe-list--schedule)
- [Recipe: mashup of two views](#recipe-mashup-of-two-views)
- [Troubleshooting checklist](#troubleshooting-checklist)

---

## Charts (Highcharts / Chartkick)

TRMNL hosts the libraries. Put `<script>` includes and the init code in the **Shared** tab (or inline in the layout). Charts render once into a screenshot, so **animation must be off**.

**CDN includes:**
```html
<script src="https://trmnl.com/js/highcharts/12.3.0/highcharts.js"></script>
<script src="https://trmnl.com/js/chartkick/5.0.1/chartkick.min.js"></script>
```

**Container** — give it a unique id (`append_random`) and let it fill the layout:
```html
<div class="view view--full">
  <div class="layout layout--col gap--space-between">
    <div class="grid grid--cols-3 gap--small">
      <!-- summary metrics here -->
    </div>
    {% assign chart_id = 'chart-' | append_random %}
    <div id="{{ chart_id }}" class="w--full"></div>
  </div>
  <div class="title_bar"> ... </div>
</div>
```

**Init (e-ink-safe Highcharts):**
```html
<script>
document.addEventListener("DOMContentLoaded", function () {
  Highcharts.chart("{{ chart_id }}", {
    chart:    { animation: false, backgroundColor: 'transparent', height: null, style: { fontFamily: 'inherit' } },
    title:    { text: null },
    credits:  { enabled: false },
    legend:   { enabled: false },
    colors:   ["black"],
    xAxis: {
      categories: {{ labels | json }},
      lineColor: 'black', tickColor: 'black',
      labels: { style: { fontSize: '16px', color: 'black' } }
    },
    yAxis: {
      title: { text: null },
      gridLineDashStyle: 'Dot', gridLineColor: 'black',
      labels: { style: { fontSize: '16px', color: 'black' } }
    },
    plotOptions: { series: { animation: false, marker: { enabled: false } } },
    series: [{ data: {{ values | json }} }]
  });
});
</script>
```

E-ink rules:
- `animation: false` at **both** `chart` and `plotOptions.series` levels — otherwise the screenshot catches a half-drawn chart.
- `backgroundColor: 'transparent'`, `colors: ["black"]`, dashed/dotted grid lines (`gridLineDashStyle: 'Dot'`).
- `height: null` expands to fill; fonts ~16px+ to stay legible.
- On TRMNL X (16-shade) you may add a few gray series colors (e.g. `["black", "#555555", "#999999"]`) — guard with `4bit:` styling where needed.
- Pass Liquid data into JS with `| json` so it becomes valid JSON literals.

Chartkick alternative (simpler):
```html
<div id="{{ chart_id }}" style="height:300px;"></div>
<script>
document.addEventListener("DOMContentLoaded", function () {
  new Chartkick.LineChart("{{ chart_id }}", {{ series | json }}, {
    animation: false, colors: ["black"], legend: false, points: false
  });
});
</script>
```

---

## Recipe: single big metric

```html
<div class="view view--full">
  <div class="layout layout--col gap--space-between">
    <div class="item">
      <div class="content">
        <span class="value value--xlarge value--tnums" data-value-format="true" data-fit-value="true">{{ amount }}</span>
        <span class="label">{{ metric_label }}</span>
      </div>
    </div>
    <div class="progress-bar">
      <div class="content">
        <span class="label">Goal</span>
        <span class="value value--xxsmall">{{ pct }}%</span>
      </div>
      <div class="track"><div class="fill" style="width: {{ pct }}%"></div></div>
    </div>
  </div>
  <div class="title_bar">
    <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
    <span class="title">{{ plugin_title | default: 'Metric' }}</span>
    <span class="instance">{{ trmnl.plugin_settings.instance_name }}</span>
  </div>
</div>
```

## Recipe: multi-metric grid

```html
<div class="view view--full">
  <div class="layout">
    <div class="grid grid--cols-3 gap--small">
      {% for m in metrics limit: 6 %}
        <div class="item">
          <div class="content">
            <span class="value value--large value--tnums" data-value-format="true">{{ m.value }}</span>
            <span class="label" data-clamp="1">{{ m.label }}</span>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>
  <div class="title_bar">
    <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
    <span class="title">Dashboard</span>
  </div>
</div>
```

## Recipe: list / schedule

Loops events, formats dates with `l_date`, limits + clamps to avoid clipping. See also `assets/scaffolds/schedule-full.liquid`.

```html
<div class="view view--full">
  <div class="layout">
    {% if events == empty or events == nil %}
      <div class="richtext richtext--center">
        <div class="content content--center text--center"><p>No upcoming events</p></div>
      </div>
    {% else %}
      <div class="flex flex--col gap--small" data-list-limit="true">
        {% for e in events limit: 8 %}
          <div class="item">
            <div class="meta"><span class="index">{{ e.date | l_date: '%-d', trmnl.user.locale }}</span></div>
            <div class="content">
              <span class="title title--small" data-clamp="1">{{ e.title }}</span>
              <div class="flex gap--small">
                <span class="label label--small label--underline">{{ e.date | l_date: '%a %b %-d', trmnl.user.locale }}</span>
                {% if e.time != "" and e.time %}
                  <span class="label label--small label--underline">{{ e.time }}</span>
                {% endif %}
                {% if e.location != "" and e.location %}
                  <span class="label label--small" data-clamp="1">{{ e.location }}</span>
                {% endif %}
              </div>
            </div>
          </div>
        {% endfor %}
      </div>
    {% endif %}
  </div>
  <div class="title_bar">
    <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
    <span class="title">{{ schedule_title | default: 'Schedule' }}</span>
    <span class="instance">{{ trmnl.plugin_settings.instance_name }}</span>
  </div>
</div>
```

## Recipe: mashup of two views

```html
<div class="mashup mashup--1Lx1R">
  <div class="view view--half_vertical">
    <div class="layout"> <!-- left content --> </div>
    <div class="title_bar"><span class="title">Left</span></div>
  </div>
  <div class="view view--half_vertical">
    <div class="layout"> <!-- right content --> </div>
    <div class="title_bar"><span class="title">Right</span></div>
  </div>
</div>
```

---

## Troubleshooting checklist

| Symptom | Likely cause / fix |
|---------|--------------------|
| Screen didn't update | Merge data unchanged (TRMNL skips identical renders) → **Force Refresh**; or webhook hit the `429` rate limit. |
| Chart half-drawn / blank | Animation still on → set `animation: false` at chart **and** series level; ensure JS is in `DOMContentLoaded`. |
| Content cut off | Add `data-clamp`, `data-list-limit`, `data-table-limit`, or `limit:` in the loop. |
| Variable renders empty | Wrong nesting — read root keys (single URL / webhook `merge_variables`) or `IDX_n` (multiple URLs); don't double-nest under `data`. |
| Data won't parse | JSON-in-a-string field → `| parse_json` first. |
| Looks black-and-white only | Use `gray-*` tokens + `image-dither`; TRMNL X supports 16 shades (`4bit:`). |
| Layout fine on OG, broken on X | Hardcoded px → use `cqw`/`cqh`, `w--full`, and `lg:`/`4bit:` responsive prefixes. |
| Two charts collide | Reuse of element `id` → generate ids with `| append_random`. |
| Title bar instance blank | `{{ trmnl.plugin_settings.instance_name }}` only set once the instance is named. |
