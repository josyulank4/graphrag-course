"""Lesson 1 - The three question shapes over one small corpus.

Prints the running corpus and the three canonical questions, one per shape
(lookup, multi-hop, global), with the evidence each truthful answer needs.
This is the map Lesson 7 (hopgap) later scores the baseline against.
Run: python -m lesson1.questions
"""
from __future__ import annotations

from graphcommon import DOCUMENTS, QUESTIONS


def main() -> None:
    print(f"documents: {len(DOCUMENTS)}")
    shapes = [q["shape"] for q in QUESTIONS]
    print("question shapes: " + ", ".join(shapes))
    for q in QUESTIONS:
        print(f"{q['shape'].upper()}: {q['question']}")
        print(f"  evidence needed: {', '.join(q['evidence_docs'])}")
    print("lesson1 demo complete")


if __name__ == "__main__":
    main()
