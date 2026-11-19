"""Lesson 43 - Score Both Systems, Read the Gap (grapheval) -
START STATE.

The evaluation the last two lessons contracted for. One question set -
Lesson 11's twenty questions, the set the schema was sketched from -
each question carrying the evidence documents a truthful answer must
draw on, fixed here BEFORE any scoring runs. Both systems are scored
under the contract Lesson 7 set and Lesson 35 reused: a system answers
a question only if its own evidence, as delivered, can state the
answer. The vector baseline below is complete - it is Lesson 7's
honest keyword top-3, unchanged, and its scoreboard is the number the
graph must beat per shape or stand unjustified. The graph scoring and
the gap table are built in the lesson; score_graph() is the honest
stub they replace.
Run: python -m lesson43.grapheval
"""
from __future__ import annotations

from graphcommon import DOCUMENTS
from lesson11.schemasketch import QUESTIONS20
from lesson19.resolvex import resolve_graph
from lesson35.hybridfuse import graph_search, vector_search, vector_verdict

INCIDENTS = ["d01", "d04", "d05", "d06", "d07", "d08",
             "d09", "d10", "d11"]

# The evidence map: the documents a truthful answer to each question
# must draw on. Fixed before scoring; neither system is consulted.
EVIDENCE: dict[int, list[str]] = {
    1: ["d03"], 2: ["d02", "d03"], 3: INCIDENTS, 4: ["d12"],
    5: ["d15"], 6: ["d16"], 7: ["d01", "d03"], 8: ["d05", "d20"],
    9: INCIDENTS, 10: ["d01", "d05", "d07", "d09"], 11: ["d23"],
    12: ["d01", "d02"], 13: ["d06"], 14: INCIDENTS,
    15: ["d03", "d12"], 16: ["d14"], 17: ["d01", "d22"],
    18: ["d01", "d02", "d03", "d15", "d16", "d23"], 19: ["d13"],
    20: ["d05", "d20"],
}

# The answer fact for each lookup, stated verbatim in its evidence
# document - Lesson 7's answerability check, applied per question.
FACTS: dict[int, str] = {
    1: "1 March 2027", 4: "December 2028", 5: "Alder Insurance",
    6: "forty seats", 11: "one year", 13: "nine hours",
    16: "Six warehouse associates", 19: "millet counter",
}

SHAPES = ("lookup", "multi-hop", "global")


def eval_set() -> list[dict]:
    """The twenty questions as scoring dicts: shape, text, evidence,
    and (for lookups) the fact a stated answer must contain."""
    out = []
    for qid, shape, text in QUESTIONS20:
        q = {"qid": qid, "shape": shape, "question": text,
             "evidence_docs": list(EVIDENCE[qid])}
        if qid in FACTS:
            q["fact"] = FACTS[qid]
        out.append(q)
    return out


def score_vector(questions: list[dict]) -> list[tuple[dict, bool, str]]:
    """The baseline, scored exactly as Lesson 7 scored it."""
    rows = []
    for q in questions:
        retrieved = vector_search(q["question"])
        ok, why = vector_verdict(q, retrieved)
        rows.append((q, ok, why))
    return rows


def score_graph(questions: list[dict]) -> list[tuple[dict, bool, str]]:
    """The graph side, scored under the same contract - built in
    Lesson 43. Baselines first: until this exists, the graph's
    claims are unscored, and unscored claims are marketing."""
    raise NotImplementedError(
        "the graph side is scored in Lesson 43 - baselines first")


def by_shape(rows: list[tuple[dict, bool, str]]) -> dict[str, tuple[int, int]]:
    out = {}
    for shape in SHAPES:
        mine = [ok for q, ok, _w in rows if q["shape"] == shape]
        out[shape] = (sum(mine), len(mine))
    return out


def print_rows(rows: list[tuple[dict, bool, str]]) -> None:
    for q, ok, why in rows:
        print(f"Q{q['qid']:02d} [{q['shape']}] "
              f"{'YES' if ok else 'NO'} - {why}")


def main() -> None:
    questions = eval_set()
    census = {s: sum(1 for q in questions if q["shape"] == s)
              for s in SHAPES}
    print(f"documents: {len(DOCUMENTS)}")
    print(f"question set: {len(questions)} questions "
          f"(lookup {census['lookup']}, multi-hop {census['multi-hop']}, "
          f"global {census['global']})")
    print("evidence fixed before scoring: every question carries the "
          "documents a truthful answer must draw on")
    print("scoring contract: a system answers only if its own evidence, "
          "as delivered, can state the answer")
    print()
    print("== vector baseline: keyword top-3 (Lesson 7, unchanged) ==")
    vrows = score_vector(questions)
    print_rows(vrows)
    vshape = by_shape(vrows)
    vtotal = sum(ok for _q, ok, _w in vrows)
    print(f"vector by shape: lookup {vshape['lookup'][0]} of 8, "
          f"multi-hop {vshape['multi-hop'][0]} of 7, "
          f"global {vshape['global'][0]} of 5")
    print(f"vector scoreboard: {vtotal} of 20")
    print()
    print("== graph system: shape-dispatched search (Lesson 35, unchanged) ==")
    grows = score_graph(questions)
    print_rows(grows)


if __name__ == "__main__":
    main()
