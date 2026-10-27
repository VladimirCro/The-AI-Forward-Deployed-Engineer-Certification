"""Run the ten labelled cases through the endpoint's logic and write what it answered.

    uv run --env-file ../../.env python answer_cases.py      (from the app folder)

The table goes to 03_Retrieval/challenge/endpoint_results.md: the proposed levels,
the sources, how many gold documents are among them, and whether a decline case
was declined. The full Responses, which quote the documents, go to
use_case/data/endpoint_runs.json (gitignored).
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import assess

APP = Path(__file__).resolve().parent
ROOT = APP.parents[1]
CASES = ROOT / "use_case" / "evals" / "retrieval.jsonl"
TABLE = ROOT / "03_Retrieval" / "challenge" / "endpoint_results.md"
RUNS = ROOT / "use_case" / "data" / "endpoint_runs.json"
WORKERS = 4


def run_case(case: dict) -> dict:
    """One case through assess_control_for_client, with what the labels say about it."""
    started = time.perf_counter()
    response = assess.assess_control_for_client(case["client"], case["control_id"])
    declined = not response.sources and response.documentation.level is None and response.implementation.level is None
    found = [record_id for record_id in case["gold"] if record_id in response.sources]
    if case["kind"] == "decline":
        correct = declined
    else:
        correct = len(found) == len(case["gold"])
    return {"case": case, "response": response.model_dump(), "declined": declined, "found": found,
            "correct": correct, "latency_s": round(time.perf_counter() - started, 1)}


def table(rows: list[dict]) -> str:
    """One line per case: levels, sources, gold found, and whether the endpoint got it right."""
    correct = sum(row["correct"] for row in rows)
    lines = [
        f"# TC3 endpoint on the ten cases ({date.today().isoformat()})",
        "",
        "`assess_control_for_client`: hybrid retrieval, one call that labels each document supports, contradicts "
        "or neutral, `solve()` on the supporting and contradicting ones, every quote checked against its document. "
        "Correct means: a decline case returns no level and no sources; any other case has every gold document in `sources`.",
        "",
        f"Correct: {correct}/{len(rows)}.",
        "",
        "| Client | Control | Kind | Documentation | Implementation | Sources | Gold in sources | Correct | Latency, s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        case, response = row["case"], row["response"]
        sources = ", ".join(response["sources"]) or "none"
        gold = f"{len(row['found'])}/{len(case['gold'])}" if case["gold"] else "n/a"
        lines.append(f"| {case['client']} | {case['control_id']} | {case['kind']} | {response['documentation']['level'] or '-'} "
                     f"| {response['implementation']['level'] or '-'} | {sources} | {gold} | {'✅' if row['correct'] else '❌'} "
                     f"| {row['latency_s']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        rows = list(pool.map(run_case, cases))
    TABLE.write_text(table(rows), encoding="utf-8")
    RUNS.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(table(rows))


if __name__ == "__main__":
    main()
