"""End-to-end validation for the Course 11 code repository.
Runs every lesson demo as a subprocess (exactly how a student runs them)
and checks expected output markers. Run from the repo root: python validate.py
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent
FAILURES = []
COUNT = [0]
def check(name, condition, detail=""):
    COUNT[0] += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" — {detail}" if detail and not condition else ""))
    if not condition: FAILURES.append(name)
def expect(module, markers):
    proc = subprocess.run([sys.executable, "-m", module], cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
    check(f"{module}: runs end-to-end (exit 0)", proc.returncode == 0, proc.stderr.strip()[-300:])
    for m in markers: check(f"{module}: output contains {m!r}", m in proc.stdout)
def main():
    print("== module demos (subprocess) ==")
    expect("lesson1.questions", ["documents: 24", "question shapes: lookup, multi-hop, global",
                                 "MULTI-HOP: Which supplier is named in both the March outage review",
                                 "lesson1 demo complete"])
    expect("lesson7.hopgap", ["evidence coverage: 100%",
                              "single-chunk answerable: YES",
                              "shapes answered from their own evidence: 1 of 3",
                              "hopgap demo complete"])
    expect("lesson11.schemasketch", ["questions: 20",
                              "shape census: lookup 8, multi-hop 7, global 5",
                              "entity types: 8",
                              "relationship types: 6",
                              "questions served: 20 of 20",
                              "types without a justifying question: 0",
                              "schemasketch demo complete"])
    expect("lesson15.extractpipe", ["documents: 24",
                              "chunks: 51",
                              "equipment mentions found: 0 of 8",
                              "entities: 29",
                              "edges: 47",
                              "edges with evidence: 47 of 47 (100%)",
                              "extractpipe demo complete"])
    expect("lesson19.resolvex", ["documents: 24",
                              "surface entities: 30",
                              "edges keyed by surface: 48",
                              "MERGE Handheld scanners + scanners -> handheld scanners",
                              "resolved entities: 29",
                              "resolved edges: 47",
                              "evidence preserved: named_in 34 of 34",
                              "resolved graph matches Lesson 15 canonical graph: YES",
                              "resolvex demo complete"])
    expect("lesson23.communitylens", ["resolved graph: 29 entities, 47 edges",
                              "entity graph: 29 nodes, 22 links",
                              "communities detected: 14",
                              "singleton communities: 4",
                              "draft summary of community 1: 8 claims, 3 violations",
                              "summaries written: 14",
                              "summary claims checked: 71, violations: 0",
                              "communitylens demo complete"])
    expect("lesson27.localsearch", ["seed documents: d02 (title overlap 3), d03 (title overlap 3)",
                              "hop 1: d02 names 3 entities; d03 names 2 entities",
                              "hop 2: neighbourhood grows to 8 nodes",
                              "named in both seed documents: Kestrel Components",
                              "answer: Kestrel Components (Supplier)",
                              "localsearch demo complete"])
    expect("lesson31.globalmap", ["communities: 14 (Lesson 23 output); summary claims checked: 71, violations: 0",
                              "map: 14 partial answers, one per community",
                              "themes: 10 of 14 communities touch an incident report; 4 contribute coverage, not themes",
                              "coverage: incident reports 9 of 9; map documents 17 of 24",
                              "globalmap demo complete"])
    expect("lesson39.indexledger", ["build total: $1.91",
                              "cost per document: $0.08 (24 documents)",
                              "incremental total: $0.50 - 26.0% of the full build",
                              "after the update: coverage 10 of 10 incident reports",
                              "indexledger demo complete"])
    expect("lesson35.hybridfuse", ["no seed: the question names no resolved entity, so the graph abstains",
                              "the themes cover the incident set 9 of 9",
                              "scoreboard: vector 2 of 4, graph 3 of 4, hybrid 4 of 4",
                              "hybridfuse demo complete"])
    print()
    print("== direct assertions ==")
    from graphcommon import DOCUMENTS, QUESTIONS, keyword_search, tokenize
    check("corpus holds exactly 24 documents", len(DOCUMENTS) == 24)
    check("document ids are unique", len({d[0] for d in DOCUMENTS}) == 24)
    check("three canonical questions, one per shape",
          [q["shape"] for q in QUESTIONS] == ["lookup", "multi-hop", "global"])
    check("multi-hop evidence joins exactly d02 and d03",
          QUESTIONS[1]["evidence_docs"] == ["d02", "d03"])
    check("keyword baseline ranks the renewal memo first for the lookup question",
          keyword_search(QUESTIONS[0]["question"], top_k=1) == ["d03"])
    check("tokenize drops stopwords and case",
          tokenize("The Kestrel Contract") == {"kestrel", "contract"})
    from lesson11.schemasketch import QUESTIONS20
    check("twenty questions in the schema sketch", len(QUESTIONS20) == 20)
    check("question census is 8 lookup / 7 multi-hop / 5 global",
          [sum(1 for q in QUESTIONS20 if q[1] == s)
           for s in ("lookup", "multi-hop", "global")] == [8, 7, 5])
    from lesson15.extractpipe import chunk_corpus
    check("corpus chunks into 51 sentence windows with provenance",
          len(chunk_corpus()) == 51
          and all(c[0].startswith("d") and c[2] for c in chunk_corpus()))
    from lesson19.resolvex import surface_graph
    _sg = surface_graph(chunk_corpus())
    check("surface graph fragments the corpus into 30 surface entities",
          len(_sg["entities"]) == 30)
    check("handheld scanners arrives under two surface forms",
          _sg["entities"].get("Handheld scanners") == "Equipment"
          and _sg["entities"].get("scanners") == "Equipment")
    from lesson19.resolvex import resolve_graph
    from lesson23.communitylens import entity_graph
    check("entity graph spans all 29 resolved entities",
          len(entity_graph(resolve_graph())) == 29)
    from lesson27.localsearch import find_seeds, named_entities
    _g = resolve_graph()
    check("local search seeds are the two documents the question names",
          [d for d, _t, _o in find_seeds(QUESTIONS[1]["question"])]
          == ["d02", "d03"])
    check("exactly one entity is named in both seed documents",
          sorted(set(named_entities(_g, "d02"))
                 & set(named_entities(_g, "d03")))
          == ["Kestrel Components"])
    from lesson31.globalmap import partial_answers
    from lesson23.communitylens import entity_graph as _eg, \
        detect_communities as _dc
    _adj = _eg(_g)
    _partials = partial_answers(_g, _adj, _dc(_adj))
    check("global map phase yields one partial per community",
          len(_partials) == 14)
    check("ten partials touch an incident report, four touch none",
          sum(1 for p in _partials if p["incident"]) == 10
          and sum(1 for p in _partials if not p["incident"]) == 4)
    from lesson35.hybridfuse import QUESTIONS4, fuse, graph_search
    check("the graph abstains on the cafeteria question",
          graph_search(resolve_graph(), QUESTIONS4[3])[0] == [])
    check("hybrid fusion ranks the corroborated document first",
          fuse(["d03", "d01", "d02"], ["d03", "d01", "d02"])[0] == "d03")
    from lesson39.indexledger import build_ledger
    _ledger = build_ledger()
    check("the build ledger counts Lesson 15's 51 chunks",
          _ledger["chunks"] == 51)
    check("resolution blocking finds 14 candidate pairs",
          _ledger["comparisons"] == 14)
    print()
    print(f"CHECKS: {COUNT[0]}  FAILURES: {len(FAILURES)}")
    if FAILURES:
        print("OVERALL: FAIL")
        for f in FAILURES: print("  FAILED:", f)
        return 1
    print("OVERALL: PASS")
    return 0
if __name__ == "__main__":
    sys.exit(main())
