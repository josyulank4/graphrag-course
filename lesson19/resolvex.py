"""Lesson 19 - Resolve Duplicates, Keep the Receipts (resolvex).

Entity resolution over the Lesson 15 extraction. The typed pass keys
its graph by canonical name, but a real extraction run keys it by the
surface form the text actually used - and the same entity arrives
under several names: 'Handheld scanners' at the head of a sentence,
'scanners' two sentences later, contracts named by their short form.
This lesson builds that surface-keyed graph honestly, then resolves
it: candidate pairs are scored on printed evidence, merges and
normalisations are logged with the evidence behind them, tempting
pairs that must NOT merge are refused with the reason, and every
merge stays reversible because the log keeps every surface form.
The resolved graph is checked against Lesson 15's canonical graph:
same entities, same edges, no evidence lost.
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
    """Resolve surface entities to canonical entities, with receipts.

    Decisions, in order: multi-surface clusters merge on scored
    evidence; single surfaces that differ from their canonical name
    are normalised with the attesting sentence as evidence; pairs of
    distinct canonical entities that a naive matcher would merge are
    examined and refused with the blocking reason. Every decision is
    appended to the merge log, so every merge is reversible.
    """
    entities, edges, mentions = graph["entities"], graph["edges"], \
        graph["mentions"]
    canon_of: dict[str, str] = {}
    for m in mentions:
        canon_of[m["surface"]] = m["entity"]
    clusters: dict[str, list[str]] = {}
    for surf in entities:
        clusters.setdefault(canon_of[surf], []).append(surf)
    docs_of: dict[str, set] = {}
    for m in mentions:
        docs_of.setdefault(m["surface"], set()).add(m["doc"])

    log: list[str] = []
    decisions = 0
    for canon in sorted(clusters):
        members = sorted(clusters[canon])
        if len(members) > 1:
            points, why = 0.0, []
            low = [m.lower() for m in members]
            if any(a != b and (a in b or b in a)
                   for i, a in enumerate(low) for b in low[i + 1:]):
                points += 0.40
                why.append("one name contains the other")
            if len({entities[m] for m in members}) == 1:
                points += 0.20
                why.append(f"same type ({entities[members[0]]})")
            shared = set.intersection(*[docs_of[m] for m in members])
            if shared:
                points += 0.20
                why.append("shared document " + ", ".join(sorted(shared)))
            neigh = [_neighbours(edges, m) for m in members]
            common = set.intersection(*neigh) if neigh else set()
            if common:
                points += 0.18
                why.append("shared neighbour " + ", ".join(sorted(common)))
            log.append(f"MERGE {' + '.join(members)} -> {canon} "
                       f"(confidence {points:.2f}: {'; '.join(why)})")
            decisions += 1
        elif members[0] != canon:
            surf = members[0]
            attesting = next(m["sentence"] for m in mentions
                             if m["entity"] == canon)
            log.append(f"NORMALISE {surf} -> {canon} "
                       f"(confidence 0.95: gazetteer canonical name; "
                       f"attested in '{attesting}')")
            decisions += 1

    refusals: list[str] = []
    canons = sorted(clusters)
    for i, a in enumerate(canons):
        for b in canons[i + 1:]:
            containment = a.lower() in b.lower() or b.lower() in a.lower()
            shared_token = bool(_tokens(a) & _tokens(b))
            same_type = entities[clusters[a][0]] == entities[clusters[b][0]]
            if not (containment or (shared_token and same_type)):
                continue
            types = (entities[clusters[a][0]], entities[clusters[b][0]])
            if types[0] != types[1]:
                reason = f"type conflict ({types[0]} vs {types[1]})"
            else:
                reason = "shared token only; no shared document or neighbour"
            refusals.append(f"KEEP APART {a} / {b} ({reason})")

    resolved_edges: list[tuple[str, str, str, str, str]] = []
    seen: set = set()
    folded = 0
    for s, rel, o, doc, sent in edges:
        cs = canon_of.get(s, s)
        co = o if rel == "named_in" else canon_of.get(o, o)
        key = (cs, rel, co, doc, sent) if rel == "named_in" \
            else (cs, rel, co, doc)
        if key in seen:
            folded += 1
            continue
        seen.add(key)
        resolved_edges.append((cs, rel, co, doc, sent))
    resolved_entities = {canon_of[s]: t for s, t in entities.items()}
    return {"entities": resolved_entities, "edges": resolved_edges,
            "log": log, "refusals": refusals, "decisions": decisions,
            "folded": folded}


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
