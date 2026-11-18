"""Lesson 31 - A Corpus-Wide Answer, Assembled (globalmap).

Global search over the Meridian corpus, end to end. The canonical
global question - what are the main themes across this quarter's
incident reports? - is about the whole corpus, so no traversal from
one seed can answer it (Lesson 29). The method is map-reduce over
Lesson 23's community summaries. Map: one partial answer per
community, built only from that community's claim-checked summary,
annotated with the incident reports the community actually touches.
Rank: partials ordered by incident coverage, then by size, so the
reduction reads the strongest evidence first. Reduce: the partials
that touch an incident report become the answer's themes; the ones
that do not are counted aloud, not silently dropped. Coverage is
stated in both directions - every incident report the answer claims,
and the documents no community can see because they name no resolved
entity. A global answer that hides its coverage is Lesson 32's
failure mode; this one prints it.
Run: python -m lesson31.globalmap
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS
from lesson19.resolvex import resolve_graph
from lesson23.communitylens import (check_claims, community_docs,
                                    detect_communities, entity_graph,
                                    summarise)

QUESTION = QUESTIONS[2]  # the canonical global question
INCIDENT_DOCS = set(QUESTION["evidence_docs"])


def partial_answers(graph: dict, adj: dict,
                      communities: list[list[str]]) -> list[dict]:
    """The map phase: one partial answer per community. A partial is
    the community's checked summary claims plus the incident reports
    its members are named in - nothing a claim did not survive."""
    partials = []
    for i, members in enumerate(communities, 1):
        text, claims = summarise(members, graph, adj)
        violations = check_claims(claims, members, graph, adj)
        docs = community_docs(members, graph)
        partials.append({
            "community": i,
            "members": members,
            "text": text,
            "claims": claims,
            "violations": violations,
            "docs": docs,
            "incident": sorted(docs & INCIDENT_DOCS),
        })
    return partials


def rank_partials(partials: list[dict]) -> list[dict]:
    """Rank by incident coverage, then community size, then first
    member name - deterministic, so the reduction is reproducible."""
    return sorted(partials,
                  key=lambda p: (-len(p["incident"]), -len(p["members"]),
                                 p["members"][0]))


def assemble_answer(ranked: list[dict]) -> tuple[list[dict], list[dict]]:
    """The reduce phase: partials touching an incident report become
    themes, in ranked order. Partials touching none contribute
    coverage, not themes, and are returned separately so the caller
    can count them aloud."""
    themes = [p for p in ranked if p["incident"]]
    silent = [p for p in ranked if not p["incident"]]
    return themes, silent


def main() -> None:
    graph = resolve_graph()
    entities, edges = graph["entities"], graph["edges"]
    question = QUESTION["question"]
    print(f"question: {question} (global)")
    print(f"resolved graph: {len(entities)} entities, {len(edges)} edges "
          f"(Lesson 19 output)")

    adj = entity_graph(graph)
    communities = detect_communities(adj)
    partials = partial_answers(graph, adj, communities)
    total_claims = sum(len(p["claims"]) for p in partials)
    total_violations = sum(len(p["violations"]) for p in partials)
    print(f"communities: {len(communities)} (Lesson 23 output); "
          f"summary claims checked: {total_claims}, "
          f"violations: {total_violations}")

    print(f"map: {len(partials)} partial answers, one per community")
    for p in partials:
        inc = ", ".join(p["incident"]) if p["incident"] else "none"
        print(f"  partial (community {p['community']}): {p['text']}; "
              f"incident reports: {inc}")

    ranked = rank_partials(partials)
    print("ranked: by incident coverage, then size - "
          + ", ".join(f"community {p['community']}" for p in ranked))

    themes, silent = assemble_answer(ranked)
    print(f"themes: {len(themes)} of {len(partials)} communities touch "
          f"an incident report; {len(silent)} contribute coverage, "
          f"not themes")
    print("answer (reduced from the partials, strongest first):")
    for p in themes:
        print(f"  theme (community {p['community']}): "
              f"{', '.join(p['members'])}; "
              f"incident reports: {', '.join(p['incident'])}")

    covered = set()
    for p in partials:
        covered |= p["docs"]
    heard = set()
    for p in themes:
        heard |= set(p["incident"])
    invisible = sorted({d[0] for d in DOCUMENTS} - covered)
    print(f"coverage: incident reports {len(heard)} of "
          f"{len(INCIDENT_DOCS)}; map documents {len(covered)} of "
          f"{len(DOCUMENTS)} "
          f"({len(invisible)} documents name no resolved entity and "
          f"are invisible to this map: {', '.join(invisible)})")
    print("globalmap demo complete")


if __name__ == "__main__":
    main()
