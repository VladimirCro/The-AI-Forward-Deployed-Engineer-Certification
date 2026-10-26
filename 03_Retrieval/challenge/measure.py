"""Measure the retrieval techniques against the ten labelled cases.

    uv run --env-file ../../.env python ../../03_Retrieval/challenge/measure.py      (from the app folder)

Every case runs through every technique with the same model, the same task and the
same pages. The table goes to 03_Retrieval/challenge/results.md; the answers and
traces, which quote the documents, go to use_case/data/retrieval_runs.json (gitignored).
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(APP))

import retrieval as R

CASES = ROOT / "use_case" / "evals" / "retrieval.jsonl"
TABLE = Path(__file__).resolve().parent / "results.md"
RUNS = ROOT / "use_case" / "data" / "retrieval_runs.json"
WORKERS = 4
DECLINE_MARKER = "no evidence found"


def techniques(pages: dict, index: str) -> dict:
    """Each technique as its tools, built over the same pages."""
    return {
        "Agentic RAG (BM25)": R.rag_tools(pages),
        "DCI (wiki)": R.dci_tools(pages, index),
    }


def score(case: dict, result: dict, sources: list[str]) -> dict:
    """Session 5's measure, on our labels: the answer, the gold documents, and the trace."""
    answer = result["answer"].lower()
    if case["kind"] == "decline":
        # A decline passes when the agent answers, says so, and names no document.
        # Running out of turns is not a decline: the agent never said anything.
        passed = result["stopped"] == "answer" and DECLINE_MARKER in answer and not sources
        complete = passed
    else:
        passed = all(term.lower() in answer for term in case["expected_terms"])
        complete = all(record_id in sources for record_id in case["gold"])
    return {
        "pass": passed,
        "complete": complete,
        "extra": len([record_id for record_id in sources if record_id not in case["gold"]]),
        "calls": len(result["trace"]),
        "evidence_chars": result["evidence_chars"],
        "latency_s": round(result["latency_s"], 1),
        "stopped": result["stopped"],
    }


def run_case(case: dict, catalog: dict) -> list[dict]:
    """One case through every technique."""
    pages, index = R.load_client(case["client"])
    question = R.task(case["control_id"], catalog)
    rows = []
    for name, (tools, funcs) in techniques(pages, index).items():
        result = R.run_agent(question, tools, funcs)
        sources = R.found_documents(result["answer"], pages)
        rows.append({"client": case["client"], "control_id": case["control_id"], "kind": case["kind"],
                     "technique": name, "sources": sources, "answer": result["answer"], "trace": result["trace"],
                     **score(case, result, sources)})
    return rows


def table(rows: list[dict]) -> str:
    """The results table: one line per technique, then one line per case and technique."""
    lines = [
        f"# TC3 retrieval results ({date.today().isoformat()})",
        "",
        f"Model `{os.getenv('LLM_MODEL')}` at the provider's default temperature (the model rejects one), "
        f"at most {R.MAX_TURNS} tool turns, BM25 top {R.TOP_K} per search (the model may ask for more), "
        "one page per document (no chunking inside documents), word split `\\w+` so Croatian letters count. "
        "Ten fictional clients of about 150 documents each, built by `build_clients.py`; labels in `use_case/evals/retrieval.jsonl`.",
        "",
        "| Technique | Pass | Complete (all gold cited) | Extra documents cited | Calls (mean) | Evidence read, chars (mean) | Latency, s (mean) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name in dict.fromkeys(row["technique"] for row in rows):
        mine = [row for row in rows if row["technique"] == name]
        n = len(mine)
        lines.append(
            f"| {name} | {sum(r['pass'] for r in mine)}/{n} | {sum(r['complete'] for r in mine)}/{n} "
            f"| {sum(r['extra'] for r in mine)} | {sum(r['calls'] for r in mine) / n:.1f} "
            f"| {sum(r['evidence_chars'] for r in mine) / n:,.0f} | {sum(r['latency_s'] for r in mine) / n:.1f} |"
        )
    lines += ["", "| Client | Control | Kind | Technique | Pass | Complete | Extra | Calls | Chars | Latency, s | Stopped |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['client']} | {r['control_id']} | {r['kind']} | {r['technique']} | {'✅' if r['pass'] else '❌'} "
                     f"| {'✅' if r['complete'] else '❌'} | {r['extra']} | {r['calls']} | {r['evidence_chars']:,} "
                     f"| {r['latency_s']} | {r['stopped']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    catalog = json.loads((APP / "catalog.json").read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(lambda case: run_case(case, catalog), cases))
    rows = [row for case_rows in results for row in case_rows]
    TABLE.write_text(table(rows), encoding="utf-8")
    RUNS.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(table(rows))


if __name__ == "__main__":
    main()
