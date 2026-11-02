"""Collect fifty traces from the running app for the Step 1 trace pass.

The app must be running (the tc3-app container on port 7860). Every case goes
through the Week 3 endpoint, /assess_control_for_client, the way a user or the
frontend would call it, so every trace is the whole flow: search, classify, assess,
check the quotes.

- the 10 cases in retrieval.jsonl  -> their TC3 clients (klijent-01 to klijent-10)
- the 6 goldens                    -> clients golden-1 to golden-6
- 34 rows of synthetic_v2.jsonl    -> clients synthetic-r<row>

The golden and synthetic clients are built first by build_trace_clients.py.

Writes use_case/data/traces_w4.jsonl and traces_w4.md to read (both gitignored).

    cd 01_Product_Engineering/challenge
    uv run --no-sync python ../../use_case/evals/collect_traces.py
"""

import json
import random
import time
from pathlib import Path

APP_URL = "http://localhost:7860"
EVALS = Path(__file__).resolve().parent
DATA = EVALS.parent / "data"
SYNTHETIC_COUNT = 34


def read_jsonl(path: Path) -> list[dict]:
    """All rows of a jsonl file."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def pick_synthetic(rows: list[dict], count: int) -> list[tuple[int, dict]]:
    """Rows taken in turn from each (control, implementation level) group, so rare levels are not drowned by level 3."""
    groups = {}
    for index, row in enumerate(rows):
        key = (row["input"]["control_id"], str(row["output"]["implementation"]["level"]))
        groups.setdefault(key, []).append((index, row))
    rng = random.Random(7)
    for members in groups.values():
        rng.shuffle(members)
    picked = []
    while len(picked) < count:
        for key in sorted(groups):
            if groups[key] and len(picked) < count:
                picked.append(groups[key].pop())
    return picked


def all_cases() -> list[dict]:
    """The fifty cases, each with what goes to the endpoint and what we expect back."""
    cases = []
    for case in read_jsonl(EVALS / "retrieval.jsonl"):
        cases.append({"trace_id": f"retrieval-{case['client']}", "source": "retrieval.jsonl",
                      "endpoint": "/assess_control_for_client",
                      "input": {"client_id": case["client"], "control_id": case["control_id"]},
                      "reference": {"gold": case["gold"], "kind": case["kind"], "why": case["why"]}})
    # Goldens and synthetic rows: their documents now sit in their own client, so the
    # search has to find them; case_documents keeps the ones it should have found.
    for number, row in enumerate(read_jsonl(EVALS / "golden.jsonl"), start=1):
        cases.append({"trace_id": f"golden-{number}", "source": "golden.jsonl",
                      "endpoint": "/assess_control_for_client",
                      "input": {"client_id": f"golden-{number}", "control_id": row["input"]["control_id"]},
                      "case_documents": row["input"]["evidence_documents"], "record_prefix": f"r{9000 + number}",
                      "reference": row["output"]})
    for index, row in pick_synthetic(read_jsonl(DATA / "synthetic_v2.jsonl"), SYNTHETIC_COUNT):
        cases.append({"trace_id": f"synthetic-r{index}", "source": "synthetic_v2.jsonl", "axes": row["axes"],
                      "endpoint": "/assess_control_for_client",
                      "input": {"client_id": f"synthetic-r{index}", "control_id": row["input"]["control_id"]},
                      "case_documents": row["input"]["evidence_documents"], "record_prefix": f"r{index}",
                      "reference": row["output"]})
    return cases


def call_endpoint(client, case: dict) -> dict:
    """One call to the app; keeps the answer, or the error if the call failed, and how long it took."""
    started = time.time()
    try:
        reply = client.predict(case["input"]["client_id"], case["input"]["control_id"], api_name=case["endpoint"])
        case["actual"] = json.loads(reply)
        case["error"] = None
    except Exception as exc:  # a failed call is a trace too
        case["actual"] = None
        case["error"] = f"{type(exc).__name__}: {exc}"
    case["seconds"] = round(time.time() - started, 1)
    return case


def to_markdown(trace: dict) -> str:
    """One trace as a block to read: what went in, what we expected, what came back."""
    lines = [f"## {trace['trace_id']}  ({trace['endpoint']}, {trace['seconds']} s)", ""]
    if "axes" in trace:
        lines.append(f"Recipe: {json.dumps(trace['axes'], ensure_ascii=False)}")
    lines.append(f"Control: {trace['input']['control_id']}  Client: {trace['input']['client_id']}")
    if "case_documents" in trace:
        lines += ["", "**Documents the search should find**"]
        for doc in trace["case_documents"]:
            lines += ["", f"**{trace['record_prefix']}-{doc['document_id']}: {doc['name']}**", doc["content"]]
    lines += ["", "**Expected**", "```json", json.dumps(trace["reference"], ensure_ascii=False, indent=1), "```", ""]
    if trace["error"]:
        lines.append(f"**Actual: ERROR** {trace['error']}")
    else:
        lines += ["**Actual**", "```json", json.dumps(trace["actual"], ensure_ascii=False, indent=1), "```"]
    lines += ["", "---", ""]
    return "\n".join(lines)


def main() -> None:
    """Send every case to the app one after another, then write both files."""
    from gradio_client import Client  # only needed to call the app, so harness.py can import the cases without it

    client = Client(APP_URL, verbose=False)
    traces = []
    for number, case in enumerate(all_cases(), start=1):
        trace = call_endpoint(client, case)
        traces.append(trace)
        print(f"{number:2}/50 {trace['trace_id']}: {trace['seconds']} s{'  ERROR' if trace['error'] else ''}", flush=True)
    with open(DATA / "traces_w4.jsonl", "w", encoding="utf-8") as out:
        for trace in traces:
            out.write(json.dumps(trace, ensure_ascii=False) + "\n")
    (DATA / "traces_w4.md").write_text("\n".join(to_markdown(t) for t in traces), encoding="utf-8")
    errors = sum(1 for t in traces if t["error"])
    print(f"{len(traces)} traces, {errors} errors -> use_case/data/traces_w4.jsonl and traces_w4.md")


if __name__ == "__main__":
    main()
