"""Lesson 15 - Extract a Graph From Raw Text (extractpipe).

The full extraction pipeline over the Meridian corpus, in two passes.
Pass one is the naive extractor most teams ship first: capitalised
phrases become entities, nothing is typed, no edges are built - its
failures are printed, not hidden. Pass two is the pipeline this section
teaches: sentence chunks with provenance (Lesson 13), a gazetteer typed
by the Lesson 11 schema, sentence-level relation patterns (Lesson 14's
output contract, Lesson 16's evidence rule) - every edge carries the
sentence it came from, or it is not an edge.
Run: python -m lesson15.extractpipe
"""
from __future__ import annotations

import re

from graphcommon import DOCUMENTS

INCIDENT_DOCS = ["d01", "d04", "d05", "d06", "d07", "d08", "d09", "d10", "d11"]

INCIDENT_NAMES = {
    "d01": "warehouse scanner outage",
    "d04": "cold-chain temperature excursion",
    "d05": "forklift battery smoke",
    "d06": "customs hold at the border",
    "d07": "label printer faults",
    "d08": "routing software crash",
    "d09": "loading dock door jam",
    "d10": "festival week staffing shortage",
    "d11": "fuel surcharge dispute",
}

# (canonical name, type, surface forms) - the Lesson 11 schema as a
# gazetteer. Longest surface wins, so "Pune warehouse" beats "Pune".
GAZETTEER: list[tuple[str, str, list[str]]] = [
    ("Kestrel Components", "Supplier", ["Kestrel Components"]),
    ("PureFlow", "Supplier", ["PureFlow"]),
    ("Alder Insurance", "Insurer", ["Alder Insurance"]),
    ("Northbeam Analytics", "Licensor", ["Northbeam Analytics"]),
    ("Pune warehouse", "Location", ["Pune warehouse"]),
    ("Hyderabad depot", "Location", ["Hyderabad depot"]),
    ("Pune office", "Location", ["Pune office"]),
    ("handheld scanners", "Equipment",
     ["Handheld scanners", "handheld scanners", "scanners"]),
    ("conveyor controller", "Equipment", ["conveyor controller"]),
    ("power module", "Equipment", ["power module"]),
    ("forklift battery", "Equipment", ["forklift battery"]),
    ("label printers", "Equipment", ["Label printers", "label printers"]),
    ("loading dock door", "Equipment", ["loading dock door"]),
    ("door motor", "Equipment", ["door motor"]),
    ("door seal", "Equipment", ["door seal"]),
    ("Kestrel supply contract", "Contract", ["supply contract"]),
    ("water cooler contract", "Contract", ["water cooler contract"]),
    ("fleet insurance policy", "Contract", ["fleet insurance policy"]),
    ("Pune office lease", "Contract", ["office lease"]),
    ("Northbeam Analytics licence", "Contract", ["licence"]),
]

EQUIPMENT_FORMS = ["handheld scanners", "conveyor controller", "power module",
                   "forklift battery", "label printers", "loading dock door",
                   "door motor", "door seal"]
DATE_WORDS = {"March", "June", "January", "December", "February",
              "Monday", "Sunday", "Diwali"}
STARTERS = {"The", "A", "An"}


def chunk_corpus() -> list[tuple[str, int, str]]:
    """Sentence windows with provenance: (doc_id, sentence_index, text)."""
    chunks = []
    for doc_id, _title, text in DOCUMENTS:
        for i, sent in enumerate(re.split(r"(?<=\.)\s+", text)):
            chunks.append((doc_id, i, sent.strip()))
    return chunks


def naive_pass(chunks: list[tuple[str, int, str]]) -> dict:
    """Pass one: every capitalised phrase is an entity. No schema."""
    entities: set[str] = set()
    mentions = 0
    for _doc, _idx, sent in chunks:
        for m in re.finditer(r"[A-Z][a-z]+(?: [A-Z][a-z]+)*", sent):
            phrase = m.group(0)
            if phrase in STARTERS:
                continue
            entities.add(phrase)
            mentions += 1
    found_equipment = [f for f in EQUIPMENT_FORMS
                       if any(f == e.lower() for e in entities)]
    return {"mentions": mentions, "entities": entities,
            "noise": sorted(e for e in entities if e in DATE_WORDS),
            "equipment_found": found_equipment}


def find_mentions(chunks: list[tuple[str, int, str]]) -> list[dict]:
    """Typed mentions: gazetteer surfaces, longest first, no overlaps."""
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
                # A span is claimed per entity: the same entity may not
                # double-claim ("scanners" inside "Handheld scanners"),
                # but different entities may share a word - "Pune office"
                # the location lives inside "Pune office lease" the
                # contract, and both mentions are real.
                if any(span[0] < u[0][1] and u[0][0] < span[1]
                       and u[1] == name for u in used):
                    continue
                used.append((span, name))
                mentions.append({"entity": name, "type": etype,
                                 "doc": doc_id, "sent_idx": idx,
                                 "sentence": sent})
    for doc_id in INCIDENT_DOCS:
        sent = next(s for d, i, s in chunks if d == doc_id and i == 0)
        mentions.append({"entity": INCIDENT_NAMES[doc_id], "type": "Incident",
                         "doc": doc_id, "sent_idx": 0, "sentence": sent})
    return mentions


def build_graph(chunks: list[tuple[str, int, str]]) -> dict:
    """Pass two: typed entities and evidence-carrying edges."""
    mentions = find_mentions(chunks)
    entities: dict[str, str] = {}
    for m in mentions:
        entities[m["entity"]] = m["type"]
    edges: list[tuple[str, str, str, str, str]] = []

    seen: set = set()

    def add(subj: str, rel: str, obj: str, m: dict) -> None:
        # named_in is a per-mention provenance record, so each mention
        # is its own edge; a relationship edge is one claim per document
        # - a second evidence sentence supports it, it does not clone it.
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
        add(m["entity"], "named_in", m["doc"], m)
    for doc_id, ms in by_doc.items():
        sup = [m for m in ms if m["type"] == "Supplier"]
        ins = [m for m in ms if m["type"] == "Insurer"]
        lic = [m for m in ms if m["type"] == "Licensor"]
        con = [m for m in ms if m["type"] == "Contract"]
        for m in ms:
            if "supplied by" in m["sentence"] and m["type"] == "Equipment":
                for s in sup:
                    if s["sent_idx"] == m["sent_idx"]:
                        add(m["entity"], "supplied_by", s["entity"], m)
        if doc_id in INCIDENT_DOCS:
            inc = INCIDENT_NAMES[doc_id]
            for m in ms:
                if m["type"] == "Location":
                    add(inc, "occurred_at", m["entity"], m)
                if m["type"] == "Equipment":
                    add(inc, "involved", m["entity"], m)
        for c in con:
            for s in sup + lic:
                add(s["entity"], "party_to", c["entity"], c)
            for i in ins:
                add(c["entity"], "held_by", i["entity"], c)
    return {"entities": entities, "edges": edges, "mentions": mentions}


def main() -> None:
    chunks = chunk_corpus()
    print(f"documents: {len(DOCUMENTS)}")
    print(f"chunks: {len(chunks)} (sentence windows, provenance kept)")
    naive = naive_pass(chunks)
    print("naive pass (capitalised phrases, no schema):")
    print(f"  mentions: {naive['mentions']}")
    print(f"  distinct entities: {len(naive['entities'])} (all typed 'Entity')")
    print(f"  date and festival words typed as entities: "
          f"{len(naive['noise'])} ({', '.join(naive['noise'])})")
    print(f"  equipment mentions found: {len(naive['equipment_found'])} "
          f"of {len(EQUIPMENT_FORMS)}")
    print("  edges built: 0")
    graph = build_graph(chunks)
    entities, edges = graph["entities"], graph["edges"]
    by_type: dict[str, int] = {}
    for t in entities.values():
        by_type[t] = by_type.get(t, 0) + 1
    census = ", ".join(f"{t} {by_type[t]}" for t in
                       ["Supplier", "Insurer", "Licensor", "Location",
                        "Equipment", "Contract", "Incident"])
    rel_counts: dict[str, int] = {}
    for _s, rel, _o, _d, _sent in edges:
        rel_counts[rel] = rel_counts.get(rel, 0) + 1
    rels = ", ".join(f"{r} {rel_counts[r]}" for r in
                     ["named_in", "supplied_by", "occurred_at", "involved",
                      "party_to", "held_by"])
    with_evidence = sum(1 for e in edges if e[4])
    linked = {e[0] for e in edges}
    orphans = [e for e in entities if e not in linked]
    ex = next(e for e in edges if e[1] == "supplied_by")
    print("typed pass (Lesson 11 schema + gazetteer):")
    print(f"  entities: {len(entities)} ({census})")
    print(f"  equipment recovered: {by_type['Equipment']} of "
          f"{len(EQUIPMENT_FORMS)} forms")
    print(f"  edges: {len(edges)} ({rels})")
    print(f"  example edge: {ex[0]} -{ex[1]}-> {ex[2]} "
          f"({ex[3]}: '{ex[4]}')")
    print(f"  edges with evidence: {with_evidence} of {len(edges)} "
          f"({with_evidence / len(edges):.0%})")
    print(f"  entities with no edges: {len(orphans)}")
    print("  noise entities: 0")
    print("extractpipe demo complete")


if __name__ == "__main__":
    main()
