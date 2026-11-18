"""Lesson 23 - Detect Communities, Write the Summaries (communitylens).

Community detection and summarisation over the resolved Meridian
graph (Lesson 19's output). The entity graph links entities two ways:
relationship edges from the corpus (supplied_by, involved, ...) and
shared-document links (two entities named in the same document).
Communities are found by deterministic label propagation - sorted
order, heaviest neighbour label wins, ties break to the smallest
label - so the partition is reproducible exactly. Each community is
then summarised by template from its own members, and every claim in
every summary is checked back against the graph before it may stand:
a claim is a member name, a member count, or a document count, and
the checker re-derives each one. A greedy draft summary that
overclaims is run through the same checker first, and its violations
are printed, not hidden - Lesson 24 audits why maps mislead; this
lesson builds the check that catches it.
Run: python -m lesson23.communitylens
"""
from __future__ import annotations

from lesson19.resolvex import resolve_graph


def entity_graph(graph: dict) -> dict:
    """Undirected weighted adjacency over canonical entities.

    Relationship edges weigh 3; sharing a document weighs 1 per shared
    document. named_in edges are the evidence trail, not links: they
    are read here to derive the shared-document links, then set aside.
    """
    adj: dict[str, dict[str, int]] = {e: {} for e in graph["entities"]}

    def link(a: str, b: str, w: int) -> None:
        if a == b:
            return
        adj[a][b] = adj[a].get(b, 0) + w
        adj[b][a] = adj[b].get(a, 0) + w

    docs_of: dict[str, set] = {}
    for s, rel, o, _d, _sent in graph["edges"]:
        if rel == "named_in":
            docs_of.setdefault(s, set()).add(o)
        else:
            link(s, o, 3)
    names = sorted(docs_of)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = docs_of[a] & docs_of[b]
            if shared:
                link(a, b, len(shared))
    return adj


def detect_communities(adj: dict) -> list[list[str]]:
    """Label propagation, deterministic: nodes in sorted order adopt
    the heaviest neighbour label (ties: smallest label); iterate to a
    fixpoint. Singletons are reported, never hidden or merged away."""
    labels = {n: n for n in adj}
    for _round in range(50):
        changed = False
        for node in sorted(adj):
            if not adj[node]:
                continue
            weight: dict[str, int] = {}
            for nbr, w in adj[node].items():
                weight[labels[nbr]] = weight.get(labels[nbr], 0) + w
            best = min(weight, key=lambda lab: (-weight[lab], lab))
            if best != labels[node]:
                labels[node] = best
                changed = True
        if not changed:
            break
    groups: dict[str, list[str]] = {}
    for node, lab in labels.items():
        groups.setdefault(lab, []).append(node)
    communities = [sorted(members) for members in groups.values()]
    communities.sort(key=lambda ms: (-len(ms), ms[0]))
    return communities


def community_docs(members: list[str], graph: dict) -> set:
    docs = set()
    for s, rel, o, _d, _sent in graph["edges"]:
        if rel == "named_in" and s in members:
            docs.add(o)
    return docs


def hub_of(members: list[str], adj: dict) -> str:
    return min(members, key=lambda m: (-sum(adj[m].values()), m))


def summarise(members: list[str], graph: dict, adj: dict) -> tuple:
    """A summary as a list of claims, each checkable against the graph.

    Claim forms: ("member", name), ("count", n), ("docs", n),
    ("hub", name). The rendered sentence is assembled from the claims
    and nothing else, so checking the claims checks the summary.
    """
    docs = community_docs(members, graph)
    hub = hub_of(members, adj)
    types = sorted({graph["entities"][m] for m in members})
    claims = [("count", len(members)), ("docs", len(docs)),
              ("hub", hub)] + [("member", m) for m in members]
    text = (f"{len(members)} entities across {len(docs)} documents; "
            f"hub: {hub}; types: {', '.join(types)}; "
            f"members: {', '.join(members)}")
    return text, claims


def check_claims(claims: list, members: list[str], graph: dict,
                 adj: dict) -> list[str]:
    """Re-derive every claim from the graph; return the violations."""
    violations = []
    member_set = set(members)
    for kind, value in claims:
        if kind == "member" and value not in member_set:
            violations.append(f"names non-member {value!r}")
        elif kind == "count" and value != len(members):
            violations.append(f"claims {value} members, community "
                              f"has {len(members)}")
        elif kind == "docs" and value != len(community_docs(members,
                                                            graph)):
            violations.append(f"claims {value} documents, members "
                              f"are named in "
                              f"{len(community_docs(members, graph))}")
        elif kind == "hub" and value != hub_of(members, adj):
            violations.append(f"claims hub {value!r}, heaviest member "
                              f"is {hub_of(members, adj)!r}")
    return violations


def draft_summary(members: list[str], graph: dict, adj: dict) -> tuple:
    """The greedy draft: right shape, two overclaims - it borrows the
    corpus's most famous neighbour from another community and rounds
    its document coverage up to the whole incident set. The checker
    below is what stands between this draft and a global answer."""
    outsider = "Kestrel Components" if "Kestrel Components" not in members \
        else "Hyderabad depot"
    claims = [("count", len(members) + 1), ("docs", 9),
              ("hub", hub_of(members, adj)),
              ("member", outsider)] + [("member", m) for m in members]
    text = (f"{len(members) + 1} entities across 9 documents; "
            f"including {outsider}")
    return text, claims


def main() -> None:
    graph = resolve_graph()
    entities, edges = graph["entities"], graph["edges"]
    print(f"resolved graph: {len(entities)} entities, {len(edges)} edges "
          f"(Lesson 19 output)")
    adj = entity_graph(graph)
    links = sum(len(v) for v in adj.values()) // 2
    print(f"entity graph: {len(adj)} nodes, {links} links "
          f"(relationships + shared documents)")
    communities = detect_communities(adj)
    print(f"communities detected: {len(communities)}")
    for i, members in enumerate(communities, 1):
        unit = "member" if len(members) == 1 else "members"
        print(f"  community {i}: {len(members)} {unit} - "
              f"{', '.join(members)}")
    singletons = [m for m in communities if len(m) == 1]
    print(f"singleton communities: {len(singletons)} "
          f"(reported, not hidden)")

    largest = communities[0]
    _draft_text, draft_claims = draft_summary(largest, graph, adj)
    draft_violations = check_claims(draft_claims, largest, graph, adj)
    print(f"draft summary of community 1: {len(draft_claims)} claims, "
          f"{len(draft_violations)} violations")
    for v in draft_violations:
        print(f"  violation: {v}")

    total_claims, total_violations = 0, 0
    for members in communities:
        _text, claims = summarise(members, graph, adj)
        violations = check_claims(claims, members, graph, adj)
        total_claims += len(claims)
        total_violations += len(violations)
    print(f"summaries written: {len(communities)}")
    print(f"summary claims checked: {total_claims}, "
          f"violations: {total_violations}")
    print("communitylens demo complete")


if __name__ == "__main__":
    main()
