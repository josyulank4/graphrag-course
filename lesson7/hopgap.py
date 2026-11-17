"""Lesson 7 - The Hop Gap, Measured (hopgap) - START STATE.

Prints the baseline's retrieval report per canonical question: what the
token-overlap baseline retrieves at the working depth k=3, with overlap
scores, against each question's evidence set. The scoring layer -
evidence coverage and single-chunk answerability - is built in the
lesson; score() below is the honest stub it replaces.
Run: python -m lesson7.hopgap
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS, keyword_search, tokenize

WORKING_K = 3
BY_ID = {doc_id: (title, text) for doc_id, title, text in DOCUMENTS}


def overlap(question: str, doc_id: str) -> int:
    title, text = BY_ID[doc_id]
    return len(tokenize(question) & tokenize(title + " " + text))


def score(question: dict, retrieved: list[str]) -> None:
    raise NotImplementedError("scoring is built in the lesson")


def main() -> None:
    print(f"documents: {len(DOCUMENTS)}")
    print(f"working depth: top-{WORKING_K}")
    for q in QUESTIONS:
        retrieved = keyword_search(q["question"], top_k=WORKING_K)
        scores = ", ".join(f"{d}={overlap(q['question'], d)}" for d in retrieved)
        print()
        print(f"{q['shape'].upper()}: {q['question']}")
        print(f"  retrieved: {', '.join(retrieved)}")
        print(f"  overlap scores: {scores}")
        print(f"  evidence: {', '.join(q['evidence_docs'])}")
        score(q, retrieved)
    print("hopgap demo complete")


if __name__ == "__main__":
    main()
