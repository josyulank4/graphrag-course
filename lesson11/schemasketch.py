"""Lesson 11 - A Schema From Twenty Questions (schemasketch).

Takes twenty real questions over the Meridian corpus - the three canonical
questions of the course plus seventeen more drawn from the same documents -
and derives the graph schema from them, Lesson 10's method made executable:
every entity type and relationship type must name the questions that
justify it, and every question must be served by the schema it produced.
A type no question needs is not in the schema. A question the schema
cannot serve is a schema bug, printed as one.
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

# The derived schema. justified_by is the audit trail: the question ids
# whose evidence paths need this type. served_by maps each question to
# the types its answer path walks.
ENTITY_TYPES: dict[str, list[int]] = {
    "Supplier": [1, 2, 7, 11, 12, 18],
    "Insurer": [5, 18],
    "Licensor": [6, 18],
    "Location": [4, 8, 9, 17, 20],
    "Equipment": [7, 10, 12, 17],
    "Incident": [3, 8, 9, 10, 14, 20],
    "Contract": [1, 4, 5, 6, 7, 11, 15],
    "Document": list(range(1, 21)),
}

RELATIONSHIP_TYPES: dict[str, list[int]] = {
    "named_in": [2, 18],
    "supplied_by": [7, 12],
    "occurred_at": [8, 9, 20],
    "involved": [10, 17],
    "party_to": [1, 6, 11, 15],
    "held_by": [5],
}

SERVED_BY: dict[int, list[str]] = {
    1: ["Contract", "Supplier"],
    2: ["Supplier", "Document"],
    3: ["Incident", "Document"],
    4: ["Contract", "Location"],
    5: ["Insurer", "Contract"],
    6: ["Licensor", "Contract"],
    7: ["Supplier", "Equipment", "Contract"],
    8: ["Location", "Incident"],
    9: ["Location", "Incident"],
    10: ["Equipment", "Incident"],
    11: ["Contract", "Supplier"],
    12: ["Supplier", "Equipment"],
    13: ["Document"],
    14: ["Incident"],
    15: ["Contract"],
    16: ["Document"],
    17: ["Location", "Equipment"],
    18: ["Supplier", "Insurer", "Licensor"],
    19: ["Document"],
    20: ["Location", "Incident"],
}

PROPERTIES: list[tuple[str, str, list[int]]] = [
    ("Contract", "kind (supply / service / insurance / lease / licence)", [1, 4, 5, 6, 11]),
    ("Contract", "renewal_date", [1, 15]),
    ("Contract", "seats", [6]),
    ("every edge", "source_sentence (provenance)", list(range(1, 21))),
]


def census() -> dict[str, int]:
    out: dict[str, int] = {}
    for _qid, shape, _text in QUESTIONS20:
        out[shape] = out.get(shape, 0) + 1
    return out


def derive_schema() -> dict:
    """Assemble the schema and audit it against the questions.

    The audit is the lesson: a type with no justifying question is
    removed by the questions, not by taste; a question whose served
    types are missing or unjustified is a schema bug.
    """
    problems = []
    for name, justified in list(ENTITY_TYPES.items()) + list(RELATIONSHIP_TYPES.items()):
        if not justified:
            problems.append(f"type without a justifying question: {name}")
    served = 0
    for qid, _shape, _text in QUESTIONS20:
        types = SERVED_BY.get(qid, [])
        if not types:
            problems.append(f"question Q{qid} is served by no type")
            continue
        unjustified = [t for t in types
                       if qid not in ENTITY_TYPES.get(t, [])]
        if unjustified:
            problems.append(f"question Q{qid} served by unjustified types {unjustified}")
        else:
            served += 1
    return {"entity_types": ENTITY_TYPES,
            "relationship_types": RELATIONSHIP_TYPES,
            "properties": PROPERTIES,
            "served": served,
            "problems": problems}


def main() -> None:
    print(f"questions: {len(QUESTIONS20)}")
    for qid, shape, text in QUESTIONS20:
        print(f"  Q{qid:02d} [{shape}] {text}")
    c = census()
    print(f"shape census: lookup {c['lookup']}, multi-hop {c['multi-hop']}, "
          f"global {c['global']}")
    schema = derive_schema()
    print(f"entity types: {len(schema['entity_types'])}")
    for name, justified in schema["entity_types"].items():
        by = ", ".join(f"Q{q}" for q in justified[:4])
        if len(justified) > 4:
            by += f", +{len(justified) - 4} more"
        print(f"  {name} - justified by {by}")
    print(f"relationship types: {len(schema['relationship_types'])}")
    for name, justified in schema["relationship_types"].items():
        by = ", ".join(f"Q{q}" for q in justified)
        print(f"  {name} - justified by {by}")
    print("properties:")
    for owner, prop, _justified in schema["properties"]:
        print(f"  {owner}.{prop}")
    orphans = sum(1 for j in list(ENTITY_TYPES.values())
                  + list(RELATIONSHIP_TYPES.values()) if not j)
    print(f"questions served: {schema['served']} of {len(QUESTIONS20)}")
    print(f"types without a justifying question: {orphans}")
    if schema["problems"]:
        for p in schema["problems"]:
            print(f"  SCHEMA BUG: {p}")
    print("schemasketch demo complete")


if __name__ == "__main__":
    main()
