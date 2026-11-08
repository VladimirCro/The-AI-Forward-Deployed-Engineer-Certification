"""Does the skill find the same documents as the tool loop? The ten Week 3 cases, both ways.

    cd 01_Product_Engineering/challenge
    uv run --no-sync --env-file ../../.env python ../../05_Agent_Architecture/challenge/accuracy.py

The token savings in measure.py only count if the skill still finds the documents. For
each case: the share of the labelled documents in the answer's sources (documents_found
from Week 4), the extra sources, and for the two no-evidence cases whether it declined.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(APP))

import assess
import skill

CASES = APP.parents[1] / "use_case" / "evals" / "retrieval.jsonl"
WAYS = {"tool": assess.assess_control_for_client, "skill": skill.assess_control_with_skill}


def run(way: str, case: dict) -> dict:
    response = WAYS[way](case["client"], case["control_id"])
    sources = response.sources
    declined = not sources and response.documentation.level is None and response.implementation.level is None
    gold = case["gold"]
    return {
        "case": case["client"], "way": way, "kind": case["kind"],
        "found": len([s for s in sources if s in gold]) / len(gold) if gold else None,
        "extra": len([s for s in sources if s not in gold]),
        "declined": declined,
    }


def main() -> None:
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    jobs = [(way, case) for case in cases for way in WAYS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda job: run(*job), jobs))
    print("| Case | Kind | Tool: found | Tool: extra | Skill: found | Skill: extra |")
    print("| --- | --- | ---: | ---: | ---: | ---: |")
    for case in cases:
        tool, sk = (next(r for r in rows if r["case"] == case["client"] and r["way"] == w) for w in WAYS)
        cell = lambda r: ("declined" if r["declined"] else "not declined") if r["kind"] == "decline" else f"{r['found']:.2f}"
        print(f"| {case['client']} | {case['kind']} | {cell(tool)} | {tool['extra']} | {cell(sk)} | {sk['extra']} |")
    for way in WAYS:
        mine = [r for r in rows if r["way"] == way]
        found = [r["found"] for r in mine if r["found"] is not None]
        declines = [r["declined"] for r in mine if r["kind"] == "decline"]
        print(f"{way}: documents_found {sum(found) / len(found):.2f} on {len(found)} cases, "
              f"declined {sum(declines)} of {len(declines)}, extra sources {sum(r['extra'] for r in mine)}")


if __name__ == "__main__":
    main()
