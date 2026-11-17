"""Shared foundation for the GraphRAG in Production companion demos.

One deterministic corpus: 24 short documents from a fictional company,
Meridian Logistics, carrying one planted evidence thread (the supplier
Kestrel Components) and three canonical questions - one per question shape
the course teaches: lookup, multi-hop, global. Every DEMO package in this
repo builds on this corpus so the numbers stay comparable across lessons.

Stdlib only. No randomness anywhere: the corpus is data, not generation.
"""
from __future__ import annotations

# (doc_id, title, text) - the planted thread: Kestrel Components is named in
# BOTH the March outage review (d02) and the contract renewal memo (d03);
# the renewal date lives in d03 alone; incident reports d01/d04-d11 carry
# the themes the global question asks about.
DOCUMENTS: list[tuple[str, str, str]] = [
    ("d01", "Incident report: warehouse scanner outage",
     "Handheld scanners in the Pune warehouse failed during the night shift. "
     "The scanners were supplied by Kestrel Components. Picking paused for two hours."),
    ("d02", "Outage review, March",
     "Outage review, March: the conveyor controller fault was traced to a power "
     "module. The module vendor, Kestrel Components, attended the review and "
     "accepted the action items."),
    ("d03", "Contract renewal memo: Kestrel Components",
     "Contract renewal memo: the supply contract with Kestrel Components comes "
     "up for renewal on 1 March 2027. Commercial terms are unchanged."),
    ("d04", "Incident report: cold-chain temperature excursion",
     "A refrigerated trailer rose above its temperature band for forty minutes "
     "after a door seal failed. The affected shipment was quarantined and inspected."),
    ("d05", "Incident report: forklift battery smoke",
     "A forklift battery smoked during charging in the Hyderabad depot. The "
     "charging bay was evacuated and the battery isolated. No injuries were reported."),
    ("d06", "Incident report: customs hold at the border",
     "A cross-border shipment was held at customs for nine hours over a missing "
     "certificate. The delay cascaded into two missed delivery windows."),
    ("d07", "Incident report: label printer faults",
     "Label printers in two depots produced unreadable barcodes for a full shift. "
     "The fault was traced to a worn print-head batch. Sorting fell back to manual labels."),
    ("d08", "Incident report: routing software crash",
     "The route planning service crashed during the morning peak and drivers "
     "reverted to printed route sheets. Thirty-one routes were replanned by hand."),
    ("d09", "Incident report: loading dock door jam",
     "A loading dock door jammed half-open during a storm, soaking six pallets. "
     "The door motor was replaced the same evening."),
    ("d10", "Incident report: festival week staffing shortage",
     "Depot staffing fell thirty percent during the festival week and the "
     "backlog took four days to clear. Overtime was approved for two weekends."),
    ("d11", "Incident report: fuel surcharge dispute",
     "A carrier disputed the fuel surcharge on forty invoices. Finance held "
     "payment pending a rate review. Deliveries were not affected."),
    ("d12", "Office lease note",
     "The Pune office lease runs to December 2028. The landlord confirmed the "
     "rent review clause applies from January 2027."),
    ("d13", "Cafeteria menu change",
     "The cafeteria adds a millet counter from next month. The subsidy rate is unchanged."),
    ("d14", "New hire onboarding",
     "Six warehouse associates joined this week. Their safety induction is "
     "scheduled across two mornings."),
    ("d15", "Insurance renewal note",
     "The fleet insurance policy with Alder Insurance renews in June. The broker "
     "requested updated vehicle lists."),
    ("d16", "Analytics licence note",
     "The Northbeam Analytics licence covers forty seats. Usage last quarter "
     "averaged twenty-six seats."),
    ("d17", "Holiday schedule",
     "The Diwali holiday schedule is published. Depots run skeleton crews on "
     "the two main festival days."),
    ("d18", "Parking policy update",
     "Visitor parking moves to the east lot from Monday. Staff permits are unchanged."),
    ("d19", "Laptop refresh plan",
     "The laptop refresh replaces machines older than five years. The first "
     "batch arrives in February."),
    ("d20", "Audit visit notice",
     "The annual safety audit visits the Hyderabad depot next month. Document "
     "bundles are due the week before."),
    ("d21", "Training calendar",
     "Forklift refresher training runs monthly. Scanner handling training is "
     "added from next quarter."),
    ("d22", "Customer tour note",
     "A retail customer tours the Pune warehouse next week. The tour route "
     "avoids the charging bay."),
    ("d23", "Water cooler contract",
     "The water cooler contract with PureFlow was renewed for one year at the "
     "same rate."),
    ("d24", "Depot cleaning rota",
     "The deep-clean rota moves to Sunday nights. The charging bay is cleaned "
     "first each week."),
]

# The three canonical questions: one per shape. evidence_docs is the set of
# documents a truthful answer must draw on - one document for a lookup, two
# joined documents for the multi-hop, the whole incident set for the global.
QUESTIONS: list[dict] = [
    {"shape": "lookup",
     "question": "When does the Kestrel Components supply contract come up for renewal?",
     "evidence_docs": ["d03"]},
    {"shape": "multi-hop",
     "question": "Which supplier is named in both the March outage review and the contract renewal memo?",
     "evidence_docs": ["d02", "d03"]},
    {"shape": "global",
     "question": "What are the main themes across this quarter's incident reports?",
     "evidence_docs": ["d01", "d04", "d05", "d06", "d07", "d08", "d09", "d10", "d11"]},
]

STOPWORDS = frozenset(
    "a an the is are was were in on of for to and or this that it its during "
    "across both named when does do did what which who".split())


def tokenize(text: str) -> set[str]:
    """Lowercase word tokens with stopwords removed (the toy baseline's lens)."""
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()
    return {t for t in raw if t not in STOPWORDS}


def keyword_search(question: str, top_k: int = 3) -> list[str]:
    """The honest toy baseline: rank documents by question-token overlap.

    Deterministic: ties break by document order. This is the retriever the
    course measures in Lesson 7 (hopgap) - strong on lookups, blind to
    joins and to whole-corpus questions.
    """
    q = tokenize(question)
    scored = []
    for idx, (doc_id, title, text) in enumerate(DOCUMENTS):
        score = len(q & tokenize(title + " " + text))
        scored.append((-score, idx, doc_id))
    scored.sort()
    return [doc_id for _, _, doc_id in scored[:top_k]]
