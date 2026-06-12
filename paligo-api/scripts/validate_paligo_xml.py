#!/usr/bin/env python3
"""Validate Paligo topic XML before pushing it back via PUT /documents/{id}.

Modes:
  check   <file.xml>                 Well-formedness only.
  compare <original.xml> <edited.xml>  Full pre-push validation: the edited
          document must preserve every Paligo-managed identifier from the
          original (xinfo:* attributes, xml:id / id values), keep the same
          root element, and remain well-formed.

Exit codes: 0 = OK to push, 1 = validation failed, 2 = usage/parse error.

Only uses the Python standard library.
"""

import sys
import xml.etree.ElementTree as ET
from collections import Counter

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def parse(path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"FAIL [{path}] not well-formed XML: {e}")
        return None


def is_xinfo(attr_name):
    """Paligo internal attributes live in a namespace containing 'xinfo'."""
    return attr_name.startswith("{") and "xinfo" in attr_name.split("}")[0].lower()


def element_ids(elem):
    """All identifier values on one element: xml:id, plain id."""
    ids = []
    for key in (XML_ID, "id"):
        if key in elem.attrib:
            ids.append(elem.attrib[key])
    return ids


def collect(root):
    """Return (id->tag map, duplicate ids, anchored xinfo, loose xinfo).

    xinfo attributes on elements that have their own id are keyed exactly by
    (id, attr) — value must match. xinfo attributes on elements without an id
    are collected as a multiset of (tag, attr, value): the original multiset
    must survive into the edited document, but elements may move and new
    elements may be inserted without false positives.
    """
    ids, dupes, anchored, loose = {}, set(), {}, Counter()

    for elem in root.iter():
        own = element_ids(elem)
        for i in own:
            if i in ids:
                dupes.add(i)
            ids[i] = elem.tag
        for attr, value in elem.attrib.items():
            if is_xinfo(attr):
                if own:
                    anchored[(own[0], attr)] = value
                else:
                    loose[(elem.tag, attr, value)] += 1

    return ids, dupes, anchored, loose


def cmd_check(path):
    root = parse(path)
    if root is None:
        return 1
    _, dupes, _, _ = collect(root)
    if dupes:
        print(f"FAIL duplicate id values: {sorted(dupes)}")
        return 1
    print(f"OK   {path} is well-formed, no duplicate ids")
    return 0


def cmd_compare(orig_path, edit_path):
    orig, edit = parse(orig_path), parse(edit_path)
    if orig is None or edit is None:
        return 1
    failures = []

    if orig.tag != edit.tag:
        failures.append(f"root element changed: {orig.tag} -> {edit.tag}")

    o_ids, _, o_anchored, o_loose = collect(orig)
    e_ids, e_dupes, e_anchored, e_loose = collect(edit)

    missing = sorted(set(o_ids) - set(e_ids))
    if missing:
        failures.append(
            f"{len(missing)} id(s) from original missing in edited "
            f"(breaks xrefs/reuse): {missing[:10]}"
        )
    if e_dupes:
        failures.append(f"duplicate id values in edited: {sorted(e_dupes)[:10]}")
    for i in set(o_ids) & set(e_ids):
        if o_ids[i] != e_ids[i]:
            failures.append(f"element with id {i!r} changed tag: {o_ids[i]} -> {e_ids[i]}")

    lost = sorted(set(o_anchored) - set(e_anchored))
    if lost:
        failures.append(
            f"{len(lost)} xinfo attribute(s) removed from identified "
            f"element(s) (orphans translations/reuse): {lost[:10]}"
        )
    for key in set(o_anchored) & set(e_anchored):
        if o_anchored[key] != e_anchored[key]:
            anchor, attr = key
            failures.append(
                f"xinfo value changed at {anchor} {attr}: "
                f"{o_anchored[key]!r} -> {e_anchored[key]!r}"
            )

    lost_loose = o_loose - e_loose
    if lost_loose:
        items = [(tag, attr, val) for (tag, attr, val), n in lost_loose.items()]
        failures.append(
            f"{sum(lost_loose.values())} xinfo attribute(s) removed or value-changed "
            f"on unidentified element(s) (orphans translations/reuse): {items[:10]}"
        )

    new_ids = len(set(e_ids) - set(o_ids))
    new_xinfo = (len(set(e_anchored) - set(o_anchored))
                 + sum((e_loose - o_loose).values()))

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 1
    total_xinfo = len(o_anchored) + sum(o_loose.values())
    print(
        f"OK   edited document preserves all {len(o_ids)} id(s) and "
        f"{total_xinfo} xinfo attribute(s) from original"
        + (f"; {new_ids} new id(s)" if new_ids else "")
        + (f"; {new_xinfo} new xinfo attr(s) — Paligo normally assigns these "
           f"itself; verify they were intentional" if new_xinfo else "")
    )
    return 0


def main(argv):
    if len(argv) >= 3 and argv[1] == "check":
        return cmd_check(argv[2])
    if len(argv) >= 4 and argv[1] == "compare":
        return cmd_compare(argv[2], argv[3])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
