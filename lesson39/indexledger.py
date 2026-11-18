"""Lesson 39 - The Index Ledger: Cost per Document, Cost per Day
(indexledger) - START STATE.

Every other lesson in this section spends the index; this one reads
its bill. The ledger is kept from the pipeline's own outputs, not
from estimates about them: the chunk count is Lesson 15's, the
mention count is the extractor's, the resolution comparisons are
counted over Lesson 19's surface graph with its own token blocking,
and the summary lines are Lesson 23's fourteen communities with
their real claim lists. A stated rate card turns those counts into
money - the card is printed with the ledger, so any reader can
re-price it. The second half prices the alternative to a rebuild:
one new document arrives (d25, a scanner firmware incident naming
entities the graph already holds), and the ledger counts what an
incremental update actually touches - its chunks, its mentions,
the resolution comparisons its names provoke, and the community
summaries that must be regenerated - against the full build. The
cost of staleness is printed the way Lesson 32 taught: as a
coverage number, not a currency. The build ledger below is
complete - it recounts Lessons 15/19/23. The update ledger, the
pricing of one arrival against the rebuild, is built in the
lesson; update_ledger() is the honest stub it replaces.
Run: python -m lesson39.indexledger
"""
from __future__ import annotations

import re

from graphcommon import DOCUMENTS
from lesson15.extractpipe import INCIDENT_DOCS, chunk_corpus, find_mentions
from lesson19.resolvex import _tokens, resolve_graph, surface_graph
from lesson23.communitylens import (community_docs, detect_communities,
                                    entity_graph, summarise)

# The rate card (course rates, stated so the ledger can be re-priced):
MODEL_RATE = 0.60        # dollars per 1,000 tokens, model calls
EMBED_RATE = 0.02        # dollars per 1,000 tokens, embeddings
WORDS_TO_TOKENS = 1.3    # the token estimate used throughout
OUTPUT_PER_MENTION = 12  # output tokens per extracted mention record
PAIR_JUDGEMENT_TOKENS = 90   # tokens to judge one resolution pair
REBUILD_CYCLE_DAYS = 90      # a full rebuild is amortised over 90 days
ARRIVALS_PER_DAY = 1         # expected new documents per day

NEW_DOC = ("d25", "Incident report: scanner firmware fault",
           "Handheld scanners in the Pune warehouse dropped offline "
           "after a firmware update. Kestrel Components supplied the "
           "firmware and accepted the rollback.")
NEW_INCIDENT = "scanner firmware fault"


def tokens(text: str) -> int:
    """The ledger's token estimate: words x 1.3, rounded."""
    return int(round(len(text.split()) * WORDS_TO_TOKENS))


def model_cost(token_count: int) -> float:
    return token_count / 1000.0 * MODEL_RATE


def chunk_document(doc: tuple) -> list[tuple[str, int, str]]:
    """One document chunked exactly as Lesson 15 chunks the corpus."""
    doc_id, _title, text = doc
    return [(doc_id, i, sent.strip())
            for i, sent in enumerate(re.split(r"(?<=\.)\s+", text))]


def build_ledger() -> dict:
    """The full build, line by line, from the pipeline's own counts."""
    chunks = chunk_corpus()
    extraction_in = sum(tokens(text) for _d, _i, text in chunks)
    mentions = find_mentions(chunks)
    extraction_out = OUTPUT_PER_MENTION * len(mentions)

    surface = surface_graph(chunks)
    names = sorted(surface["entities"])
    comparisons = sum(
        1 for i, a in enumerate(names) for b in names[i + 1:]
        if _tokens(a) & _tokens(b))
    resolution_tokens = comparisons * PAIR_JUDGEMENT_TOKENS

    graph = resolve_graph()
    adj = entity_graph(graph)
    communities = detect_communities(adj)
    by_id = {d[0]: (d[1], d[2]) for d in DOCUMENTS}
    summary_in = summary_out = claims_total = 0
    for members in communities:
        text, claims = summarise(members, graph, adj)
        source = " ".join(f"{by_id[d][0]} {by_id[d][1]}"
                          for d in sorted(community_docs(members, graph)))
        summary_in += tokens(source)
        summary_out += tokens(text)
        claims_total += len(claims)

    lines = {
        "chunks": len(chunks),
        "extraction_tokens": extraction_in + extraction_out,
        "extraction_cost": model_cost(extraction_in + extraction_out),
        "mentions": len(mentions),
        "surface_entities": len(names),
        "comparisons": comparisons,
        "resolution_tokens": resolution_tokens,
        "resolution_cost": model_cost(resolution_tokens),
        "communities": len(communities),
        "claims": claims_total,
        "summary_tokens": summary_in + summary_out,
        "summary_cost": model_cost(summary_in + summary_out),
        "embedding_tokens": extraction_in,
        "embedding_cost": extraction_in / 1000.0 * EMBED_RATE,
    }
    lines["total"] = (lines["extraction_cost"] + lines["resolution_cost"]
                      + lines["summary_cost"] + lines["embedding_cost"])
    lines["graph"] = graph
    lines["communities_list"] = communities
    return lines


def update_ledger(build: dict) -> dict:
    """The incremental update for one arriving document - built in
    Lesson 39. The start state keeps the build ledger only; what an
    arrival costs, and what staleness costs until it lands, is the
    lesson's build."""
    raise NotImplementedError("the update ledger is built in Lesson 39")


def main() -> None:
    print("rate card: model calls $0.60 per 1,000 tokens; embeddings "
          "$0.02 per 1,000 tokens; tokens estimated at words x 1.3")
    build = build_ledger()
    print(f"build ledger - the full index, {len(DOCUMENTS)} documents:")
    print(f"  chunking: {build['chunks']} sentence chunks "
          f"(deterministic code, no model tokens) - $0.00")
    print(f"  extraction: {build['chunks']} calls, "
          f"{build['extraction_tokens']} tokens "
          f"({build['mentions']} mention records out) - "
          f"${build['extraction_cost']:.2f}")
    print(f"  resolution: {build['comparisons']} candidate pairs from "
          f"{build['surface_entities']} surface entities "
          f"(token blocking), {build['resolution_tokens']} tokens - "
          f"${build['resolution_cost']:.2f}")
    print(f"  summaries: {build['communities']} communities, "
          f"{build['claims']} claims, {build['summary_tokens']} tokens - "
          f"${build['summary_cost']:.2f}")
    print(f"  embeddings (the vector index, Lesson 35's other half): "
          f"{build['embedding_tokens']} tokens - "
          f"${build['embedding_cost']:.2f}")
    print(f"  build total: ${build['total']:.2f}")
    print(f"  cost per document: ${build['total'] / len(DOCUMENTS):.2f} "
          f"({len(DOCUMENTS)} documents)")

    upd = update_ledger(build)
    incident_total = len(INCIDENT_DOCS) + 1
    print()
    print(f"one arrival: {NEW_DOC[0]} '{NEW_DOC[1]}' - a new incident "
          f"report naming {', '.join(upd['new_names'])}")
    print(f"  staleness, priced as coverage: the standing map hears "
          f"{len(INCIDENT_DOCS)} of {incident_total} incident reports "
          f"until the update lands")
    print(f"  incremental update: {upd['chunks']} chunks, "
          f"{upd['mentions']} mentions, {upd['comparisons']} resolution "
          f"comparisons, summaries regenerated for communities "
          f"{' and '.join(str(i) for i in upd['affected'])} "
          f"({len(upd['affected'])} of {build['communities']})")
    print(f"  incremental total: ${upd['total']:.2f} - "
          f"{upd['total'] / build['total']:.1%} of the full build")
    print(f"  after the update: coverage {incident_total} of "
          f"{incident_total} incident reports")
    per_day = (build["total"] / REBUILD_CYCLE_DAYS
               + ARRIVALS_PER_DAY * upd["total"])
    print()
    print(f"cost per day: build amortised over {REBUILD_CYCLE_DAYS} "
          f"days (${build['total'] / REBUILD_CYCLE_DAYS:.2f}) + "
          f"{ARRIVALS_PER_DAY} arrival/day at the incremental rate "
          f"(${upd['total']:.2f}) = ${per_day:.2f}")
    print("the ledger's lesson: on a corpus this small the per-pair "
          "resolution judgements are the largest line; extraction is "
          "the line that grows with the corpus - and staleness is "
          "priced in coverage, not currency")
    print("indexledger demo complete")


if __name__ == "__main__":
    main()
