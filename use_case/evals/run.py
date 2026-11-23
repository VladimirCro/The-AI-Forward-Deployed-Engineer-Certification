"""Point the harness at the Week 3 endpoint and print the report. TC4 Step 6.

    cd 01_Product_Engineering/challenge
    uv run --no-sync --env-file ../../.env python ../../use_case/evals/run.py
        runs the cases live and compares the run with baseline.json (PASS or not).
    ... python ../../use_case/evals/run.py --save
        the same, and saves the run as the new baseline. Only when re-baselining on purpose.
    ... python ../../use_case/evals/run.py memory
        only the Week 7 memory tests, in this process, on an empty memory file: one real
        assessment for the cost test, no container needed.

Needs the app running (tc3-app container on port 7860) with the fictional clients
mounted, and .env with LLM_THINKING=between_tools. Everything in use_case/data/ stays
local, so a clean checkout cannot run this: the cases come from
use_case/data/synthetic_v2.jsonl, and the clients are built by build_clients.py
(Week 3) and build_trace_clients.py (noise from synthetic_v1.jsonl). Runs from the
app's environment, which has gradio_client.

One run: 52 app calls and 62 judge calls (12 to calibrate, 50 to score; crashed cases are not scored), 52 minutes on 2 Nov,
plus the memory tests: one assessment and one explanation in this process.

Since Week 7 the app keeps its answers in memory (MEMORY_FILE, /tmp/memory.sqlite in the container).
Start a new container before each run, or the cases are answered from memory and the run scores
the stored answers, not the tool.
"""

import json
import os
import statistics
import sys
import tempfile
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
from harness import (APPLIES, JUDGE_MODEL, LEVEL_BASIS_RUBRIC, SCORERS, UNRESOLVED_GOLDENS,
                     GatewayJudge, blocks_injection, bootstrap_ci, golden_cases, harness_cases, injection_cases,
                     memory_cases, memory_holds, memory_test, subset_means, through_rails)
from helpers import harness as course

APP_URL = "http://localhost:7860"
BASELINE = EVALS / "baseline.json"
# Three runs of the same app on 13 Nov moved the judge by 0.07 and only_case_documents by 0.04,
# so the course default of 0.02 called noise a regression (decisions.md, Week 6).
TOLERANCE = 0.08
HEADLINE = "documents_found"  # failures.md #1, the top line: the search misses an important document


def endpoint():
    """The system under test: one call to the Week 3 endpoint, as the frontend makes it."""
    from gradio_client import Client

    client = Client(APP_URL, verbose=False)

    def system(question: str) -> str:
        request = json.loads(question)
        return client.predict(request["client_id"], request["control_id"], api_name="/assess_control_for_client")

    return system


def scorers_with_judge(cases: list[dict]) -> dict:
    """The four model-free scorers plus the judge, calibrated first as the course requires."""
    judge = GatewayJudge(None, rubric=LEVEL_BASIS_RUBRIC, model=JUDGE_MODEL)
    calibration = judge.calibrate([case for case in golden_cases(cases) if case["trace_id"] not in UNRESOLVED_GOLDENS])
    print(f"Judge separation: accepted {calibration.accepted:.2f}, wrong {calibration.wrong:.2f}, passed {calibration.passed}")
    # Stop rather than drop the column: a run without the judge would not compare with the baseline.
    if not calibration.passed:
        sys.exit("The judge failed separation; fix it before running, or the run will not compare.")
    return {**SCORERS, "judge_level_basis": judge.score}


def summary(report, cases: list[dict]) -> str:
    """Each scorer averaged over the cases it is about, and the headline with its interval."""
    lines = ["| Scorer | Cases | Mean |", "| --- | ---: | ---: |"]
    for label in report.means:
        applies = APPLIES.get(label, lambda case: True)
        scores = [result.scores[label] for result, case in zip(report.results, cases) if applies(case)]
        lines.append(f"| {label} | {len(scores)} | {sum(scores) / len(scores):.2f} |")
    headline = [result.scores[HEADLINE] for result, case in zip(report.results, cases) if APPLIES[HEADLINE](case)]
    mean, lo, hi = bootstrap_ci(headline)
    lines.append("")
    lines.append(f"Headline {HEADLINE}: {mean:.2f}, 95% CI [{lo:.2f}, {hi:.2f}] on {len(headline)} cases")
    if report.errors:
        lines.append(f"{report.errors} cases errored and scored 0")
    # The endpoint's time per case, so a guardrail put in front of it shows up as latency, not only as scores.
    seconds = sorted(result.seconds for result in report.results)
    p95 = seconds[round(0.95 * (len(seconds) - 1))]
    lines.append(f"Seconds per case: median {statistics.median(seconds):.1f}, p95 {p95:.1f}, max {seconds[-1]:.1f}")
    return "\n".join(lines)


# Attack 2 is a plain lie with no instruction in it; the rules cannot catch it (decisions.md, Week 6).
# The other five that landed must stay stopped.
MIN_CAUGHT = 5


def guardrail_report() -> str:
    """Week 6: the attacks that landed and the real documents, in one pass through the same rails.

    Stops the run when the rail lets an attack through that it used to stop, or refuses a real
    document, so a broken rail cannot hide behind a PASS on the other scorers.
    """
    cases = injection_cases()
    report = course.run(cases, through_rails, {"blocks_injection": blocks_injection}, name="week6-rails")
    by_kind = {}
    for result, case in zip(report.results, cases):
        by_kind.setdefault(case["kind"], []).append(result.scores["blocks_injection"])
    caught = sum(by_kind.get("attack", []))
    refused_golden = len(by_kind.get("golden", [])) - sum(by_kind.get("golden", []))
    refused_client = len(by_kind.get("client", [])) - sum(by_kind.get("client", []))
    ms = 1000 * sum(result.seconds for result in report.results) / len(report.results)
    line = (f"blocks_injection: caught {caught:.0f} of {len(by_kind.get('attack', []))} attacks that landed · "
            f"refused {refused_golden:.0f} of {len(by_kind.get('golden', []))} golden documents and "
            f"{refused_client:.0f} of {len(by_kind.get('client', []))} synthetic client documents · {ms:.0f} ms per call")
    if caught < MIN_CAUGHT or refused_golden or refused_client:
        sys.exit(line + "\nThe rail no longer does what it did on 17 Nov.")
    return line


def memory_report() -> str:
    """Week 7: the four memory tests on an empty memory file of their own.

    Stops the run when one fails, so a PASS on the other scorers does not cover a broken memory.
    """
    before = os.environ.get("MEMORY_FILE")
    with tempfile.TemporaryDirectory() as folder:
        os.environ["MEMORY_FILE"] = str(Path(folder) / "memory.sqlite")
        try:
            cases = memory_cases()
            report = course.run(cases, memory_test, {"memory_holds": memory_holds}, name="week7-memory")
        finally:
            if before is None:
                os.environ.pop("MEMORY_FILE")
            else:
                os.environ["MEMORY_FILE"] = before
    lines = [f"{case['trace_id']}: {result.actual or result.error.strip().splitlines()[-1]}"
             for case, result in zip(cases, report.results)]
    if report.means["memory_holds"] < 1:
        sys.exit("\n".join(lines) + "\nThe memory no longer does what it did on 23 Nov.")
    return "\n".join(lines)


def main() -> None:
    """Run live, print the summary, compare with the baseline; save it only with --save."""
    if sys.argv[1:] == ["memory"]:
        print(memory_report())
        return
    cases = harness_cases()
    scorers = scorers_with_judge(cases)
    name = "week4-baseline" if "--save" in sys.argv else "week4-candidate"
    report = course.run(cases, endpoint(), scorers, name=name,
                         progress=lambda done, total: print(f"{done}/{total}", flush=True))
    print(report)
    print(summary(report, cases))
    print(guardrail_report())
    print(memory_report())
    if "--save" in sys.argv:
        # A run where the app was down scores 0 everywhere, and compare() against it would pass anything.
        if report.errors > len(cases) // 10:
            sys.exit(f"{report.errors} of {len(cases)} cases errored; not saving this run as the baseline.")
        course.save(report, BASELINE)
    # Compare per-scorer means over the cases each scorer is about, on both sides.
    print(course.compare(subset_means(course.load(BASELINE), cases), subset_means(report, cases), tolerance=TOLERANCE))


if __name__ == "__main__":
    main()
