"""Lesson 19 - Resolve Duplicates, Keep the Receipts (resolvex) -
START STATE.

Entity resolution over the Lesson 15 extraction. The surface-keyed
graph is here: mentions keyed by the name the text actually used, the
fragmentation report printed honestly. The resolution itself - the
scored merge decisions, the normalisations, the refusals, the
reversible merge log - is built in the lesson; resolve() below is
the honest stub it replaces.
Run: python -m lesson19.resolvex
"""
from __future__ import annotations

import re

from graphcommon import DOCUMENTS
from lesson15.extractpipe import (GAZETTEER, INCIDENT_DOCS, INCIDENT_NAMES,
                                  build_graph, chunk_corpus)


def surface_mentions(chunks: list[tuple[str, int, str]]) -> list[dict]:
    """Typed mentions keyed by the surface text actually matched.

    Mirrors extractpipe.find_mentions (same gazetteer, same span
    claims) but records the literal surface string as the entity key:
    this is the fragmented graph a real run hands to resolution.
    """
    surfaces = []
    for name, etype, forms in GAZETTEER:
        for form in forms:
            surfaces.append((form, name, etype))
    surfaces.sort(key=lambda s: -len(s[0]))
    mentions = []
    for doc_id, idx, sent in chunks:
        used: list[tuple[tuple[int, int], str]] = []
        for form, name, etype in surfaces:
            flags = 0 if etype in ("Supplier", "Insurer", "Licensor",
                                   "Location") else re.IGNORECASE
            for m in re.finditer(re.escape(form), sent, flags):
                span = (m.start(), m.end())
                if any(span[0] < u[0][1] and u[0][0] < span[1]
                       and u[1] == name for u in used):
                    continue
                used.append((span, name))
                mentions.append({"surface": sent[m.start():m.end()],
                                 "entity": name, "type": etype,
                                 "doc": doc_id, "sent_idx": idx,
                                 "sentence": sent})
    for doc_id in INCIDENT_DOCS:
        sent = next(s for d, i, s in chunks if d == doc_id and i == 0)
        mentions.append({"surface": INCIDENT_NAMES[doc_id],
                         "entity": INCIDENT_NAMES[doc_id],
                         "type": "Incident", "doc": doc_id, "sent_idx": 0,
                         "sentence": sent})
    return mentions


def surface_graph(chunks: list[tuple[str, int, str]]) -> dict:
    """The fragmented graph: entities and edges keyed by surface form."""
    mentions = surface_mentions(chunks)
    entities: dict[str, str] = {}
    for m in mentions:
        entities[m["surface"]] = m["type"]
    edges: list[tuple[str, str, str, str, str]] = []
    seen: set = set()

    def add(subj: str, rel: str, obj: str, m: dict) -> None:
        if rel == "named_in":
            key = (subj, rel, obj, m["doc"], m["sentence"])
        else:
            key = (subj, rel, obj, m["doc"])
        if key not in seen:
            seen.add(key)
            edges.append((subj, rel, obj, m["doc"], m["sentence"]))

    by_doc: dict[str, list[dict]] = {}
    for m in mentions:
        by_doc.setdefault(m["doc"], []).append(m)
        add(m["surface"], "named_in", m["doc"], m)
    for doc_id, ms in by_doc.items():
        sup = [m for m in ms if m["type"] == "Supplier"]
        ins = [m for m in ms if m["type"] == "Insurer"]
        lic = [m for m in ms if m["type"] == "Licensor"]
        con = [m for m in ms if m["type"] == "Contract"]
        for m in ms:
            if "supplied by" in m["sentence"] and m["type"] == "Equipment":
                for s in sup:
                    if s["sent_idx"] == m["sent_idx"]:
                        add(m["surface"], "supplied_by", s["surface"], m)
        if doc_id in INCIDENT_DOCS:
            inc = INCIDENT_NAMES[doc_id]
            for m in ms:
                if m["type"] == "Location":
                    add(inc, "occurred_at", m["surface"], m)
                if m["type"] == "Equipment":
                    add(inc, "involved", m["surface"], m)
        for c in con:
            for s in sup + lic:
                add(s["surface"], "party_to", c["surface"], c)
            for i in ins:
                add(c["surface"], "held_by", i["surface"], c)
    return {"entities": entities, "edges": edges, "mentions": mentions}


def _tokens(name: str) -> set:
    return set(name.lower().split())


def _neighbours(edges: list, node: str) -> set:
    out = set()
    for s, _r, o, _d, _sent in edges:
        if s == node:
            out.add(o)
        if o == node:
            out.add(s)
    return out


def resolve(graph: dict) -> dict:
    raise NotImplementedError("the resolution pass is built in the lesson")


def resolve_graph() -> dict:
    """The resolved graph (Lesson 19's output, Lesson 23's input)."""
    return resolve(surface_graph(chunk_corpus()))


def main() -> None:
    chunks = chunk_corpus()
    graph = surface_graph(chunks)
    entities, edges = graph["entities"], graph["edges"]
    canon_of = {m["surface"]: m["entity"] for m in graph["mentions"]}
    frag: dict[str, list[str]] = {}
    for surf in entities:
        frag.setdefault(canon_of[surf], []).append(surf)
    split = {c: sorted(s) for c, s in frag.items() if len(s) > 1}
    print(f"documents: {len(DOCUMENTS)}")
    print(f"surface entities: {len(entities)} "
          f"(keyed by the name the text used)")
    for canon, members in sorted(split.items()):
        print(f"  fragmented: {canon} appears as "
              f"{' / '.join(members)}")
    print(f"edges keyed by surface: {len(edges)}")
    result = resolve(graph)
    for line in result["log"]:
        print(f"  {line}")
    for line in result["refusals"]:
        print(f"  {line}")
    rent = result["entities"]
    redges = result["edges"]
    named_in = sum(1 for e in redges if e[1] == "named_in")
    surface_named = sum(1 for e in edges if e[1] == "named_in")
    print(f"merge log: {result['decisions']} decisions, "
          f"{len(result['refusals'])} refusals - every merge reversible")
    print(f"resolved entities: {len(rent)}")
    print(f"resolved edges: {len(redges)} "
          f"(duplicate claims folded: {result['folded']})")
    print(f"evidence preserved: named_in {named_in} of {surface_named}")
    canon = build_graph(chunks)
    same_entities = rent == canon["entities"]
    same_edges = {(s, r, o, d) for s, r, o, d, _ in redges} == \
        {(s, r, o, d) for s, r, o, d, _ in canon["edges"]}
    print(f"resolved graph matches Lesson 15 canonical graph: "
          f"{'YES' if same_entities and same_edges else 'NO'} "
          f"({len(canon['entities'])} entities, {len(canon['edges'])} edges)")
    print("resolvex demo complete")


if __name__ == "__main__":
    main()
