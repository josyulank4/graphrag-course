"""Lesson 35 - Fuse Graph and Vector Evidence (hybridfuse) -
START STATE.

The hybrid pipeline, run across every question shape the course
teaches, against both single-retriever scores. The vector side is
Lesson 7's honest baseline, unchanged: keyword top-3 documents.
The graph side dispatches by question shape, as Lesson 34 routed:
a lookup walks named_in edges from the entities the question names;
a multi-hop question runs Lesson 27's seed-and-join traversal; a
global question is answered by Lesson 31's map-reduce themes. The
fusion is reciprocal rank fusion over the two document rankings,
and the verdicts use Lesson 7's answerability rule throughout: a
retriever answers only if its own evidence, as delivered, can state
the answer. The fourth question is the control the single-retriever
scoreboards need: a plain fact in a document that names no resolved
entity, where the graph has no seed and must abstain.
Run: python -m lesson35.hybridfuse
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS, keyword_search, tokenize
from lesson15.extractpipe import GAZETTEER
from lesson19.resolvex import resolve_graph
from lesson27.localsearch import find_seeds, named_entities
from lesson31.globalmap import assemble_answer, partial_answers, rank_partials
from lesson23.communitylens import detect_communities, entity_graph

WORKING_K = 3
RRF_K = 60
BY_ID = {doc_id: (title, text) for doc_id, title, text in DOCUMENTS}

QUESTIONS4 = [
    dict(QUESTIONS[0], fact="1 March 2027"),
    dict(QUESTIONS[1]),
    dict(QUESTIONS[2]),
    {"shape": "lookup",
     "question": "What changes at the cafeteria next month?",
     "evidence_docs": ["d13"], "fact": "millet counter"},
]


def vector_search(question: str) -> list[str]:
    """The vector side, exactly as Lesson 7 measured it."""
    return keyword_search(question, top_k=WORKING_K)


def vector_verdict(q: dict, retrieved: list[str]) -> tuple[bool, str]:
    """Lesson 7's answerability rule, applied to the chunk side."""
    evidence = q["evidence_docs"]
    if q["shape"] == "lookup":
        for doc_id in retrieved:
            if doc_id in evidence and q["fact"] in BY_ID[doc_id][1]:
                return True, f"the fact is stated verbatim in {doc_id}"
        return False, "the answer fact is stated in no retrieved chunk"
    if q["shape"] == "multi-hop":
        return False, ("no single chunk holds the whole evidence; "
                       "the join lives between documents")
    covered = len(set(retrieved) & set(evidence))
    return False, (f"the retrieved set covers {covered} of "
                   f"{len(evidence)} evidence documents")


def question_entities(question: str) -> list[str]:
    """The resolved entities a question names, found with Lesson
    15's own gazetteer (longest surface first, same case rules) -
    the lookup side's seed step, run on the question alone."""
    import re
    surfaces = []
    for name, etype, forms in GAZETTEER:
        for form in forms:
            surfaces.append((form, name, etype))
    surfaces.sort(key=lambda s: -len(s[0]))
    found = []
    for form, name, etype in surfaces:
        flags = 0 if etype in ("Supplier", "Insurer", "Licensor",
                               "Location") else re.IGNORECASE
        if re.search(re.escape(form), question, flags) and name not in found:
            found.append(name)
    return found


def graph_search(graph: dict, q: dict) -> tuple[list[str], str]:
    """The graph side, dispatched by shape (Lesson 34's routing).

    Returns the evidence documents the graph side stands behind, in
    its own ranked order, plus a note naming the method used."""
    if q["shape"] == "multi-hop":
        seeds = find_seeds(q["question"])
        seed_docs = [doc for doc, _t, _ov in seeds]
        hop1 = {doc: named_entities(graph, doc) for doc in seed_docs}
        common = sorted(set.intersection(
            *[set(names) for names in hop1.values()]))
        joins = [name for name in common
                 if graph["entities"][name] == "Supplier"]
        if joins:
            return seed_docs, (f"seed-and-join traversal (Lesson 27): "
                               f"{joins[0]} stands in both seeds")
        return [], "the traversal found no join entity"
    if q["shape"] == "global":
        adj = entity_graph(graph)
        partials = partial_answers(graph, adj, detect_communities(adj))
        themes, _silent = assemble_answer(rank_partials(partials))
        covered = set()
        for p in themes:
            covered |= set(p["incident"])
        return (sorted(covered),
                f"map-reduce over community summaries (Lesson 31): "
                f"{len(themes)} themes")
    # lookup: walk named_in edges from the entities the question names
    names = question_entities(q["question"])
    docs = set()
    for name in names:
        docs |= {o for s, rel, o, _d, _sent in graph["edges"]
                 if rel == "named_in" and s == name}
    if not docs:
        return [], ("no seed: the question names no resolved entity, "
                    "so the graph abstains")
    from lesson7.hopgap import overlap
    ranked = sorted(docs, key=lambda d: (-overlap(q["question"], d),
                                         [x[0] for x in DOCUMENTS].index(d)))
    return ranked, (f"named_in walk from the named entities "
                    f"({', '.join(sorted(names))})")


def graph_verdict(graph: dict, q: dict,
                  docs: list[str]) -> tuple[bool, str]:
    """The graph side can state an answer when its evidence carries
    the fact, the join, or the coverage the shape demands."""
    evidence = q["evidence_docs"]
    if not docs:
        return False, "no evidence: the graph abstains on this question"
    if q["shape"] == "lookup":
        for doc_id in evidence:
            for s, rel, o, _d, sent in graph["edges"]:
                if rel == "named_in" and o == doc_id and q["fact"] in sent:
                    return True, (f"the fact travels on the named_in edge "
                                  f"from {doc_id}: '{sent}'")
        return False, "the named documents do not carry the answer fact"
    if q["shape"] == "multi-hop":
        if set(evidence) <= set(docs):
            return True, ("the join is computed on the graph side; "
                          "both evidence documents stand in the traversal")
        return False, "the traversal does not reach the whole evidence set"
    covered = len(set(docs) & set(evidence))
    if covered == len(evidence):
        return True, (f"the themes cover the incident set "
                      f"{covered} of {len(evidence)}")
    return False, f"the themes cover {covered} of {len(evidence)}"


def fuse(vector_docs: list[str], graph_docs: list[str]) -> list[str]:
    """Reciprocal rank fusion over the two rankings - built in
    Lesson 35. The start state has both retrievers and their
    verdicts; the combination does not exist yet."""
    raise NotImplementedError("the fusion is built in Lesson 35")


def main() -> None:
    graph = resolve_graph()
    print("questions: 4 (the three canonical shapes + one plain fact)")
    print(f"vector baseline: keyword top-{WORKING_K} documents "
          f"(Lesson 7's method, unchanged)")
    print("graph: the resolved graph, dispatched by question shape "
          "(Lessons 27/31)")
    print(f"fusion: reciprocal rank fusion (k={RRF_K}) over the two "
          f"rankings")
    totals = {"vector": 0, "graph": 0, "hybrid": 0}
    for q in QUESTIONS4:
        label = q["shape"].upper()
        if q is QUESTIONS4[3]:
            label = "PLAIN FACT (lookup shape, no resolved entity)"
        v_docs = vector_search(q["question"])
        v_ok, v_why = vector_verdict(q, v_docs)
        g_docs, g_note = graph_search(graph, q)
        g_ok, g_why = graph_verdict(graph, q, g_docs)
        fused = fuse(v_docs, g_docs)
        h_ok = v_ok or g_ok
        carrier = ("both retrievers" if v_ok and g_ok else
                   "the graph side" if g_ok else
                   "the vector side" if v_ok else "neither side")
        totals["vector"] += v_ok
        totals["graph"] += g_ok
        totals["hybrid"] += h_ok
        print()
        print(f"{label}: {q['question']}")
        print(f"  vector: {', '.join(v_docs)} - answered "
              f"{'YES' if v_ok else 'NO'} ({v_why})")
        if q["shape"] == "global":
            print(f"  graph: {len(g_docs)} incident documents via "
                  f"{g_note} - answered {'YES' if g_ok else 'NO'} "
                  f"({g_why})")
            print(f"  fused context: the theme summaries + the top "
                  f"chunks {', '.join(v_docs)}")
        else:
            print(f"  graph: {', '.join(g_docs) if g_docs else '(none)'} "
                  f"[{g_note}] - answered {'YES' if g_ok else 'NO'} "
                  f"({g_why})")
            both = [d for d in fused if d in v_docs and d in g_docs]
            if both:
                print(f"  fused: {', '.join(fused)} - corroborated: "
                      f"{', '.join(both)} (named by both retrievers)")
            else:
                print(f"  fused: {', '.join(fused)}")
        print(f"  hybrid: answered {'YES' if h_ok else 'NO'} "
              f"(carried by {carrier})")
    print()
    print(f"scoreboard: vector {totals['vector']} of 4, "
          f"graph {totals['graph']} of 4, "
          f"hybrid {totals['hybrid']} of 4")
    print("each single retriever has a blind shape; the fusion "
          "covers all four")
    print("hybridfuse demo complete")


if __name__ == "__main__":
    main()
