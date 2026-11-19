"""Lesson 50/51 capstone: graphstack - the full GraphRAG stack, composed.

The capstone contract (fixed in Lesson 49, before any code): one corpus -
the frozen Meridian 24, unchanged since Lesson 1; both retrievers - the
vector baseline is built in and scored alongside the graph, never hidden;
every claim from a run - each stage re-derives the receipt its own lesson
taught it to print, and the receipts are checked against the record.

Lesson 50 (build_stack) composes the five stages the course built one at
a time - extraction (Lesson 15), resolution (Lesson 19), communities and
summaries (Lesson 23), search in both directions (Lessons 27 + 31), index
economics (Lesson 39) - and grades the composition on Lesson 43's
twenty-question set and Lesson 35's hybrid set. Lesson 51 (review) grades
the stack against the ship bar fixed in Lesson 49 and computes the
verdict from the lines. Fully offline, standard library only.
"""
from graphcommon import DOCUMENTS
from lesson15.extractpipe import INCIDENT_DOCS, build_graph, chunk_corpus
from lesson19.resolvex import resolve, surface_graph
from lesson23.communitylens import (check_claims, detect_communities,
                                    entity_graph, summarise)
from lesson27 import localsearch
from lesson27.localsearch import find_seeds, named_entities, traverse
from lesson31 import globalmap
from lesson31.globalmap import assemble_answer, partial_answers, rank_partials
from lesson35.hybridfuse import (QUESTIONS4, graph_search, graph_verdict,
                                 vector_search, vector_verdict)
from lesson39.indexledger import (ARRIVALS_PER_DAY, REBUILD_CYCLE_DAYS,
                                  build_ledger, update_ledger)
from lesson43.grapheval import by_shape, eval_set, score_graph, score_vector


def build_stack() -> dict:
    """Compose the five stages in dependency order, print every stage's
    receipt, and return the measured values for the Lesson 51 review."""
    print("graphstack: the full GraphRAG stack, composed (Lesson 50)")
    print("contract: one corpus, both retrievers, every claim from a run")
    print()

    chunks = chunk_corpus()
    print("== stage 0: the frozen corpus (Lesson 1) ==")
    print(f"documents: {len(DOCUMENTS)}, chunks: {len(chunks)} "
          f"- unchanged since Lesson 1")
    print()

    canon = build_graph(chunks)
    entities, edges = canon["entities"], canon["edges"]
    attested = sum(1 for e in edges if e[4])
    print("== stage 1: extraction (Lesson 15) ==")
    print(f"entities: {len(entities)}, edges: {len(edges)}")
    print(f"evidence: {attested} of {len(edges)} edges carry their sentence")
    print()

    surface = surface_graph(chunks)
    result = resolve(surface)
    graph = result
    rent, redges = result["entities"], result["edges"]
    named_res = sum(1 for e in redges if e[1] == "named_in")
    named_surf = sum(1 for e in surface["edges"] if e[1] == "named_in")
    same = rent == entities and \
        {(s, r, o, d) for s, r, o, d, _ in redges} == \
        {(s, r, o, d) for s, r, o, d, _ in edges}
    print("== stage 2: resolution (Lesson 19) ==")
    print(f"surface {len(surface['entities'])} entities / "
          f"{len(surface['edges'])} edges -> resolved {len(rent)} "
          f"entities / {len(redges)} edges")
    print(f"named_in preserved: {named_res} of {named_surf}")
    print(f"matches Lesson 15 canonical graph: "
          f"{'YES' if same else 'NO'}")
    print()

    adj = entity_graph(graph)
    communities = detect_communities(adj)
    singletons = sum(1 for c in communities if len(c) == 1)
    claims_total = violations_total = 0
    for members in communities:
        _text, claims = summarise(members, graph, adj)
        violations = check_claims(claims, members, graph, adj)
        claims_total += len(claims)
        violations_total += len(violations)
    print("== stage 3: communities and summaries (Lesson 23) ==")
    print(f"communities: {len(communities)} "
          f"({singletons} singletons, reported not hidden)")
    print(f"summary gate: {claims_total} claims checked, "
          f"{violations_total} violations")
    print()

    question = localsearch.QUESTION["question"]
    seeds = find_seeds(question)
    seed_docs = [doc for doc, _t, _ov in seeds]
    layers = traverse(graph, seed_docs)
    visited = sum(len(layer) for layer in layers)
    hop1 = {doc: named_entities(graph, doc) for doc in seed_docs}
    common = sorted(set.intersection(*[set(v) for v in hop1.values()]))
    answer = next(n for n in common if rent[n] == "Supplier")
    partials = partial_answers(graph, adj, communities)
    themes, _silent = assemble_answer(rank_partials(partials))
    covered = set()
    for p in partials:
        covered |= p["docs"]
    heard = set()
    for p in themes:
        heard |= set(p["incident"])
    invisible = sorted({d[0] for d in DOCUMENTS} - covered)
    print("== stage 4: search, both directions (Lessons 27 + 31) ==")
    print(f"local: '{question}'")
    print("  seeds: " + ", ".join(
        f"{doc} (title overlap {ov})" for doc, _t, ov in seeds)
        + f"; hop 2 = {visited} nodes under budget 48")
    print(f"  answer: {answer} ({rent[answer]})")
    print(f"global: {len(partials)} partials, {len(themes)} themes")
    print(f"  incident coverage: {len(heard)} of "
          f"{len(globalmap.INCIDENT_DOCS)} reports; map hears "
          f"{len(covered)} of {len(DOCUMENTS)} documents")
    print(f"  invisible to the map: {', '.join(invisible)} "
          f"({len(invisible)})")
    print()

    build = build_ledger()
    upd = update_ledger(build)
    per_day = (build["total"] / REBUILD_CYCLE_DAYS
               + ARRIVALS_PER_DAY * upd["total"])
    incident_total = len(INCIDENT_DOCS)
    print("== stage 5: index economics (Lesson 39) ==")
    print(f"build: ${build['total']:.2f} for {len(DOCUMENTS)} documents "
          f"(${build['total'] / len(DOCUMENTS):.2f} per document), "
          f"${per_day:.2f} per day")
    print(f"one arrival (d25): ${upd['total']:.2f} incremental = "
          f"{upd['total'] / build['total']:.1%} of a rebuild; summaries "
          f"regenerated for communities "
          f"{' and '.join(str(i) for i in upd['affected'])} only")
    print(f"coverage: {incident_total} of {incident_total + 1} incident "
          f"reports until the update lands, {incident_total + 1} of "
          f"{incident_total + 1} after")
    print()

    questions = eval_set()
    vrows = score_vector(questions)
    grows = score_graph(questions)
    vshape = by_shape(vrows)
    gshape = by_shape(grows)
    vtotal = sum(ok for _q, ok, _w in vrows)
    gtotal = sum(ok for _q, ok, _w in grows)
    hybrid_totals = {"vector": 0, "graph": 0, "hybrid": 0}
    for q in QUESTIONS4:
        v_docs = vector_search(q["question"])
        v_ok, _vw = vector_verdict(q, v_docs)
        g_docs, _note = graph_search(graph, q)
        g_ok, _gw = graph_verdict(graph, q, g_docs)
        hybrid_totals["vector"] += v_ok
        hybrid_totals["graph"] += g_ok
        hybrid_totals["hybrid"] += (v_ok or g_ok)
    print("== stage 6: evaluation (Lessons 43 + 35) ==")
    print(f"20 questions: vector {vtotal} of 20 "
          f"(lookup {vshape['lookup'][0]}/8, "
          f"multi-hop {vshape['multi-hop'][0]}/7, "
          f"global {vshape['global'][0]}/5)")
    print(f"20 questions: graph {gtotal} of 20 "
          f"(lookup {gshape['lookup'][0]}/8, "
          f"multi-hop {gshape['multi-hop'][0]}/7, "
          f"global {gshape['global'][0]}/5)")
    print(f"hybrid set (Lesson 35): vector {hybrid_totals['vector']} "
          f"of 4, graph {hybrid_totals['graph']} of 4, "
          f"hybrid {hybrid_totals['hybrid']} of 4")
    print()

    print("stack receipt:")
    print(f"  corpus {len(DOCUMENTS)} documents / {len(chunks)} chunks; "
          f"graph {len(rent)} entities / {len(redges)} edges, "
          f"{attested} of {len(edges)} attested")
    print("  shipped routing: lookups -> baseline side, multi-hop and "
          "global -> graph side")
    print("graphstack demo complete")

    return {
        "documents": len(DOCUMENTS), "chunks": len(chunks),
        "entities": len(rent), "edges": len(redges),
        "attested": attested, "named_in": (named_res, named_surf),
        "canonical_match": same,
        "communities": len(communities), "singletons": singletons,
        "claims": claims_total, "violations": violations_total,
        "local_answer": answer, "visited": visited,
        "partials": len(partials), "themes": len(themes),
        "incident_heard": len(heard), "incident_total": incident_total,
        "map_docs": len(covered), "invisible": invisible,
        "build_total": build["total"], "per_day": per_day,
        "arrival_total": upd["total"],
        "arrival_pct": upd["total"] / build["total"] * 100,
        "affected": upd["affected"],
        "vshape": vshape, "gshape": gshape,
        "vtotal": vtotal, "gtotal": gtotal,
        "hybrid": hybrid_totals,
    }


def main() -> None:
    build_stack()


if __name__ == "__main__":
    main()
