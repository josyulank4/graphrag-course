"""Lesson 27 - Answer a Multi-Hop Question by Traversal
(localsearch) - START STATE.

Local search over the resolved Meridian graph (Lesson 19's output).
The seed machinery is here: the documents the question points at are
found by title evidence, and hop 1 - the entities each seed names -
is read straight off the named_in edges. The traversal itself is
built in the lesson; traverse() below is the honest stub it
replaces, and the answer machinery waits downstream of it.
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS, tokenize
from lesson19.resolvex import resolve_graph

QUESTION = QUESTIONS[1]  # the canonical multi-hop question
MAX_DEPTH = 2
NODE_BUDGET = 48
ASKED_TYPE = "Supplier"  # the question asks "which supplier ..."


def find_seeds(question: str) -> list[tuple[str, str, int]]:
    """Seed documents: the two documents whose titles best match the
    question's own words. A title is a document's address; overlap is
    counted on title tokens only, ties break by document order, and a
    document the question does not point at is never seeded."""
    q = tokenize(question)
    scored = []
    for idx, (doc_id, title, _text) in enumerate(DOCUMENTS):
        overlap = len(q & tokenize(title))
        if overlap:
            scored.append((-overlap, idx, doc_id, title, overlap))
    scored.sort()
    return [(doc_id, title, overlap)
            for _neg, _idx, doc_id, title, overlap in scored[:2]]


def named_entities(graph: dict, doc: str) -> list[str]:
    """Hop 1 from a document seed: the entities it names, via the
    named_in edges read backwards (entity -> named_in -> document)."""
    return sorted({s for s, rel, o, _d, _sent in graph["edges"]
                   if rel == "named_in" and o == doc})


def adjacency(graph: dict) -> dict[str, set]:
    """Undirected adjacency over entities and documents alike: every
    edge is walkable both ways, because a citation path may be read
    from either end."""
    adj: dict[str, set] = {}
    for s, _rel, o, _d, _sent in graph["edges"]:
        adj.setdefault(s, set()).add(o)
        adj.setdefault(o, set()).add(s)
    return adj


def traverse(graph: dict, seed_docs: list[str]) -> list[set]:
    raise NotImplementedError("traversal is built in the lesson")


def evidence_for(graph: dict, entity: str, doc: str) -> str:
    """The sentence that supports one hop: the provenance stored on
    the named_in edge between this entity and this document."""
    for s, rel, o, _d, sent in graph["edges"]:
        if rel == "named_in" and s == entity and o == doc:
            return sent
    return ""


def main() -> None:
    graph = resolve_graph()
    entities, edges = graph["entities"], graph["edges"]
    question = QUESTION["question"]
    print(f"question: {question} (multi-hop)")
    print(f"resolved graph: {len(entities)} entities, {len(edges)} edges "
          f"(Lesson 19 output)")

    seeds = find_seeds(question)
    seed_docs = [doc for doc, _title, _ov in seeds]
    print("seed documents: " + ", ".join(
        f"{doc} (title overlap {ov})" for doc, _t, ov in seeds))

    hop1 = {doc: named_entities(graph, doc) for doc in seed_docs}
    print("hop 1: " + "; ".join(
        f"{doc} names {len(names)} entities" for doc, names in hop1.items()))

    layers = traverse(graph, seed_docs)
    visited = sum(len(layer) for layer in layers)
    print(f"hop 2: neighbourhood grows to {visited} nodes "
          f"(depth {MAX_DEPTH}, budget {NODE_BUDGET}: respected)")

    common = sorted(set.intersection(
        *[set(names) for names in hop1.values()]))
    print("named in both seed documents: " + ", ".join(common))
    answer = next(name for name in common
                  if entities[name] == ASKED_TYPE)
    print(f"answer: {answer} ({entities[answer]})")

    titles = {doc_id: title for doc_id, title, _t in DOCUMENTS}
    print("citation path (the path is the citation):")
    for doc in seed_docs:
        print(f"  {doc} \"{titles[doc]}\" <- {answer}: "
              f"\"{evidence_for(graph, answer, doc)}\"")
    print(f"one seed alone: {seed_docs[0]} names {answer}, but 'both' "
          f"needs the second seed - the join is the answer")
    print("localsearch demo complete")


if __name__ == "__main__":
    main()
