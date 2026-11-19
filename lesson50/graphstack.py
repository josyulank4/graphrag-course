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

START STATE: the contract prints; build_stack() is a stub that raises
NotImplementedError by design - the composition lands with the finish.
"""


def build_stack() -> dict:
    """Compose the five stages in dependency order, print every stage's
    receipt, and return the measured values for the Lesson 51 review."""
    print("graphstack: the full GraphRAG stack, composed (Lesson 50)")
    print("contract: one corpus, both retrievers, every claim from a run")
    raise NotImplementedError(
        "the stack stages land with the Lesson 50 finish")


def main() -> None:
    build_stack()


if __name__ == "__main__":
    main()
