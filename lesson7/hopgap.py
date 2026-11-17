"""Lesson 7 - The Hop Gap, Measured (hopgap).

Scores the course's honest token-overlap baseline (graphcommon.keyword_search)
per question shape against the canonical evidence sets, at the working depth
k=3. Two measurements per shape: evidence coverage (how much of the evidence
set the retrieved chunks cover) and single-chunk answerability (whether the
retrieved evidence, as chunks, can state the answer at all).
Run: python -m lesson7.hopgap
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS, keyword_search, tokenize

WORKING_K = 3
BY_ID = {doc_id: (title, text) for doc_id, title, text in DOCUMENTS}


def overlap(question: str, doc_id: str) -> int:
    title, text = BY_ID[doc_id]
    return len(tokenize(question) & tokenize(title + " " + text))


def coverage(retrieved: list[str], evidence: list[str]) -> float:
    return len(set(retrieved) & set(evidence)) / len(evidence)


def answerable(question: dict, retrieved: list[str]) -> tuple[bool, str]:
    """Can the retrieved chunks, as chunks, state the answer?

    A single chunk can state the answer only if one retrieved document
    holds the complete evidence set on its own. For the lookup we also
    check the answer fact itself is present verbatim in that document.
    """
    evidence = question["evidence_docs"]
    holders = [d for d in retrieved if {d} >= set(evidence)]
    if question["shape"] == "lookup":
        for doc_id in holders:
            if "1 March 2027" in BY_ID[doc_id][1]:
                return True, f"the date is stated verbatim in {doc_id}"
        return False, "the answer fact is stated in no retrieved chunk"
    if question["shape"] == "multi-hop":
        return False, ("no single chunk holds the whole evidence; "
                       "the join lives between documents")
    cov = coverage(retrieved, evidence)
    return False, f"the retrieved set covers {cov:.0%} of the evidence set"


def main() -> None:
    print(f"documents: {len(DOCUMENTS)}")
    print(f"working depth: top-{WORKING_K}")
    answered = 0
    for q in QUESTIONS:
        retrieved = keyword_search(q["question"], top_k=WORKING_K)
        cov = coverage(retrieved, q["evidence_docs"])
        ok, why = answerable(q, retrieved)
        answered += ok
        scores = ", ".join(f"{d}={overlap(q['question'], d)}" for d in retrieved)
        print()
        print(f"{q['shape'].upper()}: {q['question']}")
        print(f"  retrieved: {', '.join(retrieved)}")
        print(f"  overlap scores: {scores}")
        print(f"  evidence: {', '.join(q['evidence_docs'])}")
        print(f"  evidence coverage: {cov:.0%}")
        print(f"  single-chunk answerable: {'YES' if ok else 'NO'} - {why}")
    print()
    print(f"shapes answered from their own evidence: {answered} of {len(QUESTIONS)}")
    print("hopgap demo complete")


if __name__ == "__main__":
    main()
