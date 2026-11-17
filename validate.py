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
