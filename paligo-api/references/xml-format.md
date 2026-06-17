# Paligo XML Format and Editing Rules

Paligo's content model is based on **DocBook 5.x**. The `content` field returned by `GET /documents/{id}` is the raw source XML of the component in the source language.

## Contents

- [Topic shape](#topic-shape)
- [Common elements](#common-elements)
- [Paligo-managed identifiers (the critical part)](#paligo-managed-identifiers-the-critical-part)
- [Editing rules](#editing-rules)
- [What you will NOT see in source XML](#what-you-will-not-see-in-source-xml)
- [Working with the tree in Python](#working-with-the-tree-in-python)

## Topic shape

A topic is a `<section>` with a `<title>` and block content. This is a **real topic** pulled from a live instance (`GET /documents/12`), header and all:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="https://resources.paligo.net/schema/docbookxi-5.1-xinfo.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<section xmlns="http://docbook.org/ns/docbook"
         xmlns:xinfo="http://ns.expertinfo.se/cms/xmlns/1.0"
         xmlns:xi="http://www.w3.org/2001/XInclude"
         xmlns:mml="http://www.w3.org/1998/Math/MathML"
         xmlns:xlink="http://www.w3.org/1999/xlink"
         xmlns:t="http://ns.expertinfo.se/translation/xmlns/1.0"
         version="5.0"
         xinfo:resource="UUID-f8a9de46-..." xinfo:resource-id="12"
         xinfo:resource-title="Create Your First Publication"
         xinfo:resource-type="component"
         xinfo:version-major="1" xinfo:version-minor="0"
         xml:id="UUID-f8a9de46-..." xml:lang="en">
  <title xinfo:text="60">Create Your First Publication</title>
  <para xinfo:text="61">The publication is where you drag and drop your topics…</para>
  <procedure>
    <step>
      <para xinfo:text="62">Creating a Publication resource is similar to creating a topic…</para>
    </step>
  </procedure>
</section>
```

Verified facts from the live instance (Paligo serves **DocBook XI 5.1 + the `xinfo` extension**, schema `docbookxi-5.1-xinfo.rng`):
- `xinfo` namespace URI is **`http://ns.expertinfo.se/cms/xmlns/1.0`** (Paligo's vendor is "Expert Info" — that's why it's not a `paligo.net` URI). The translation namespace `t` is `http://ns.expertinfo.se/translation/xmlns/1.0`.
- The root `<section>` carries `xinfo:resource*` / `xinfo:version-*` bookkeeping attributes and `xml:id` = the resource UUID, `xml:lang` = source language.
- Segment IDs are small integers: `xinfo:text="60"`, `"61"`, … (not UUIDs).

Namespace URIs and attribute shapes can still vary by instance/version — inspect a real topic from the target instance before writing transformation code, but the URIs above hold on current Paligo.

## Common elements

| Purpose | DocBook element |
|---------|-----------------|
| Topic root / heading | `<section>` / `<title>` |
| Paragraph | `<para>` |
| Bold | `<emphasis role="bold">` |
| Italic | `<emphasis>` |
| UI label | `<guilabel>`, `<guibutton>`, `<guimenu>` |
| Inline code | `<code>`, `<literal>`, `<filename>`, `<command>` |
| Code block | `<programlisting>` (preserve whitespace!) |
| Bullet / numbered list | `<itemizedlist>` / `<orderedlist>` + `<listitem>` |
| Step-by-step | `<procedure>` + `<step>` |
| Admonitions | `<note>`, `<warning>`, `<caution>`, `<tip>`, `<important>` |
| Cross-reference | `<xref linkend="UUID-..."/>`, `<link linkend=...>` |
| External link | `<link xlink:href="https://..."/>` |
| Image | `<mediaobject><imageobject><imagedata fileref=.../></imageobject></mediaobject>` |
| Table | CALS table: `<table>/<tgroup>/<tbody>/<row>/<entry>` |

## Paligo-managed identifiers (the critical part)

Paligo stores content in a database; the XML you see is a serialization. Elements carry identifiers that bind them to Paligo's reuse system and translation memory:

- **`xinfo:*` attributes** (e.g., `xinfo:text`, `xinfo:image`, `xinfo:resource`) — internal attributes created and maintained automatically by Paligo. `xinfo:text` identifies a text fragment: it links a paragraph/title to its translations and to every place that fragment is reused. Paligo's own docs: do not edit these.
- **`xml:id` / `id` attributes** — element IDs (often `UUID-...`). Used as cross-reference targets (`linkend`) and reuse anchors. Removing one breaks every `xref` pointing at it — possibly in *other* topics you haven't pulled.

Consequences of breaking them:

| Action | Consequence |
|--------|-------------|
| Edit text, leave `xinfo:text` intact | Correct: segment is flagged for re-translation; translation memory keeps history |
| Remove/change `xinfo:text` | Paligo treats it as a brand-new text fragment — **existing translations of that segment are orphaned/lost** |
| Remove an `xml:id` | Cross-references elsewhere break (`linkend` targets vanish) |
| Duplicate an `xml:id` | Invalid document; ambiguous link targets |
| Re-generate the whole XML from scratch (e.g., markdown → XML) | All of the above at once. Never do this to an existing topic |

## Editing rules

1. **Parse, modify, serialize — never string-replace or regenerate.** Load into an XML tree, make targeted changes, serialize back.
2. **Treat `xinfo:*` and `xml:id`/`id` as read-only.** Copy them through untouched. New elements you add simply have no `xinfo` attributes — Paligo assigns them on save.
3. **Edit at the lowest level that achieves the change.** Changing wording → edit text nodes inside the existing `<para>`. Adding a step → insert a new `<step>` between existing ones, don't rebuild the `<procedure>`.
4. **Preserve namespaces exactly** — same URIs, same declarations. Don't let your serializer rewrite prefixes or drop "unused" namespace declarations.
5. **Don't pretty-print.** Re-indenting changes text nodes in mixed content (`<para>text <emphasis>…</emphasis> text</para>`), which alters the actual content and churns translation segments. Serialize with no whitespace manipulation. `<programlisting>` is whitespace-significant.
6. **Keep the XML declaration and root element** as received.
7. **Translation-aware editing:** every text segment you touch will need re-translation (correct behavior). Minimize churn — don't reflow or normalize whitespace in segments you aren't deliberately changing, or you'll flag the whole topic for re-translation.

## What you will NOT see in source XML

The API returns *source* content. These are resolved only at publish time (use a Production for resolved output):

- **Forks/reused components** — referenced, not inlined.
- **Variables** — appear as variable references, not values.
- **Filters/profiling** — conditional attributes (`condition`, audience, etc.) present but not applied.
- **Translations** — `content` is the source language only.

## Working with the tree in Python

`lxml` round-trips more faithfully than stdlib `xml.etree` (preserves comments, CDATA, attribute order is stable enough). Pattern:

```python
from lxml import etree

parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
root = etree.fromstring(content_xml.encode("utf-8"), parser)

ns = {"db": "http://docbook.org/ns/docbook"}  # confirm URI from the actual document: root.nsmap

# Targeted text edit — xinfo/xml:id attributes ride along untouched
for para in root.iter("{http://docbook.org/ns/docbook}para"):
    if para.text and "old product name" in para.text:
        para.text = para.text.replace("old product name", "New Name")
        # NOTE: .text is only the text before the first child; check child .tail too

new_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8").decode("utf-8")
```

Mixed-content gotcha: in `<para>A <emphasis>B</emphasis> C</para>`, "A" is `para.text`, "C" is `emphasis.tail`. Full-text operations must walk `.text` and every child's `.tail` (or use `"".join(el.itertext())` for read-only extraction).

After any edit, run `scripts/validate_paligo_xml.py compare original.xml edited.xml` before pushing.
