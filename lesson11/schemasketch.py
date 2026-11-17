"""Lesson 11 - A Schema From Twenty Questions (schemasketch) - START STATE.

Takes twenty real questions over the Meridian corpus - the three canonical
questions of the course plus seventeen more drawn from the same documents -
and derives the graph schema from them, Lesson 10's method made executable.
The twenty questions and their shape census are here; the derivation -
entity types, relationship types, properties, and the audit that every
type is justified and every question served - is built in the lesson;
derive_schema() below is the honest stub it replaces.
Run: python -m lesson11.schemasketch
"""
from __future__ import annotations

# (id, shape, question) - shapes assigned by Lesson 5's diagnostic: where
# does the evidence live? One place (lookup), joined places (multi-hop),
# or the set itself (global).
QUESTIONS20: list[tuple[int, str, str]] = [
    (1, "lookup", "When does the Kestrel Components supply contract come up for renewal?"),
    (2, "multi-hop", "Which supplier is named in both the March outage review and the contract renewal memo?"),
    (3, "global", "What are the main themes across this quarter's incident reports?"),
    (4, "lookup", "When does the Pune office lease run to?"),
    (5, "lookup", "Which insurer holds the fleet insurance policy?"),
    (6, "lookup", "How many seats does the Northbeam Analytics licence cover?"),
    (7, "multi-hop", "Which supplier's scanners failed in the Pune warehouse, and when does that supplier's contract come up for renewal?"),
    (8, "multi-hop", "Which depot hosts the annual safety audit, and what happened in that depot's charging bay?"),
    (9, "global", "Which locations appear most often across the incident reports?"),
    (10, "global", "What kinds of equipment failure recur across this quarter's incident reports?"),
    (11, "lookup", "For how long was the water cooler contract with PureFlow renewed?"),
    (12, "multi-hop", "The vendor who attended the March outage review supplied which equipment that failed in the Pune warehouse?"),
    (13, "lookup", "How long was the cross-border shipment held at customs?"),
    (14, "global", "How do this quarter's incidents divide between equipment failures and outside causes?"),
    (15, "multi-hop", "Which renews first, the Kestrel supply contract or the office lease's rent review?"),
    (16, "lookup", "How many warehouse associates joined this week?"),
    (17, "multi-hop", "A customer tours which warehouse next week, and what equipment failed in that warehouse?"),
    (18, "global", "Which organisations are named anywhere in the corpus, and in what roles?"),
    (19, "lookup", "What did the cafeteria add to its menu from next month?"),
    (20, "multi-hop", "The depot where the battery smoked is in which city, and which audit visits that depot next month?"),
]



def census() -> dict[str, int]:
    out: dict[str, int] = {}
    for _qid, shape, _text in QUESTIONS20:
        out[shape] = out.get(shape, 0) + 1
    return out


def derive_schema() -> dict:
    raise NotImplementedError("schema derivation is built in the lesson")


def main() -> None:
    print(f"questions: {len(QUESTIONS20)}")
    for qid, shape, text in QUESTIONS20:
        print(f"  Q{qid:02d} [{shape}] {text}")
    c = census()
    print(f"shape census: lookup {c['lookup']}, multi-hop {c['multi-hop']}, "
          f"global {c['global']}")
    derive_schema()
    print("schemasketch demo complete")


if __name__ == "__main__":
    main()
