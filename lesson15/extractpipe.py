"""Lesson 15 - Extract a Graph From Raw Text (extractpipe) - START STATE.

The full extraction pipeline over the Meridian corpus, in two passes.
The chunker (Lesson 13) and the naive first pass are here, failures
printed, not hidden. The typed pass - the gazetteer built from the
Lesson 11 schema, the mention finder, and the evidence-carrying edge
builder - is built in the lesson; build_graph() below is the honest
stub it replaces.
Run: python -m lesson15.extractpipe
"""
from __future__ import annotations

import re

from graphcommon import DOCUMENTS

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



def build_graph(chunks: list[tuple[str, int, str]]) -> dict:
    raise NotImplementedError("the typed pass is built in the lesson")


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
    build_graph(chunks)
    print("extractpipe demo complete")


if __name__ == "__main__":
    main()
