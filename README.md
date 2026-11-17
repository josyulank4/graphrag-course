# GraphRAG in Production — Companion Code (Udemy Course 11)

Working, stdlib-only Python demos for every hands-on lesson of the course.
No paid services, no third-party packages: every mechanic runs offline so
students see what the production tools actually compute. One shared module,
`graphcommon.py`, carries the deterministic corpus for a fictional company,
Meridian Logistics — 24 short documents with one planted evidence thread
(the supplier Kestrel Components, named in two documents) and three
canonical questions, one per question shape: lookup, multi-hop, global.

## Run the full validation
```
python validate.py
```
Expected final line: `OVERALL: PASS`.

## Packages (one per DEMO lesson — added as each lesson is produced)
| Package | Lesson | What it shows |
|---|---|---|
| lesson1 | 1 | The three question shapes over the corpus, with the evidence each answer needs (foundation stub) |
| hopgap | 7 | The vector baseline scored per question shape — the hop gap, measured |
| schemasketch | 11 | Twenty questions turned into a graph schema, every type justified |
| extractpipe | 15 | Entity and relationship extraction from raw text, failures before fixes |
| resolvex | 19 | Entity resolution with the receipts: every merge printed with its evidence |
| communitylens | 23 | Community detection and hierarchical summaries, claims checked |
| localsearch | 27 | A multi-hop question answered by traversal, the path as citation |
| globalmap | 31 | A corpus-wide answer assembled by map-reduce over community summaries |
| hybridfuse | 35 | Graph and vector evidence fused, routed by question shape |
| indexledger | 39 | The indexing ledger: build cost, update cost, cost of staleness |
| grapheval | 43 | Both retrievers scored per question shape; failures attributed to their layer |
| graphstack | 50/51 | The capstone stack: build end to end, then the production readiness review |

## Lesson tags
Each DEMO lesson is tagged in this repo: `lXX-start` (code before the lesson's
build) and `lXX-finish` (the exact code the lesson ships). Tags are added as
each DEMO lesson is produced. The foundation carries the Lesson 1 stub tags
`l01-start` (scaffold) and `l01-finish` (corpus + question-shapes demo).
