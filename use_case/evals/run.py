"""Point the harness at the Week 3 endpoint and print the report. TC4 Step 6.

    cd 01_Product_Engineering/challenge
    uv run --no-sync --env-file ../../.env python ../../use_case/evals/run.py
        runs the cases live and compares the run with baseline.json (PASS or not).
    ... python ../../use_case/evals/run.py --save
        the same, and saves the run as the new baseline. Only when re-baselining on purpose.

Needs the app running (tc3-app container on port 7860) with the fictional clients
mounted, and .env with LLM_THINKING=between_tools. Everything in use_case/data/ stays
local, so a clean checkout cannot run this: the cases come from
use_case/data/synthetic_v2.jsonl, and the clients are built by build_clients.py
(Week 3) and build_trace_clients.py (noise from synthetic_v1.jsonl). Runs from the
app's environment, which has gradio_client.

One run: 52 app calls and 60 judge calls (8 to calibrate, 52 to score), 52 minutes on 2 Nov.
"""

import json
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
from harness import (APPLIES, JUDGE_MODEL, LEVEL_BASIS_RUBRIC, SCORERS, UNRESOLVED_GOLDENS,
                     GatewayJudge, bootstrap_ci, golden_cases, harness_cases, subset_means)
from helpers import harness as course

APP_URL = "http://localhost:7860"
BASELINE = EVALS / "baseline.json"
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
    return "\n".join(lines)


def main() -> None:
    """Run live, print the summary, compare with the baseline; save it only with --save."""
    cases = harness_cases()
    scorers = scorers_with_judge(cases)
    name = "week4-baseline" if "--save" in sys.argv else "week4-candidate"
    report = course.run(cases, endpoint(), scorers, name=name,
                         progress=lambda done, total: print(f"{done}/{total}", flush=True))
    print(report)
    print(summary(report, cases))
    if "--save" in sys.argv:
        course.save(report, BASELINE)
    # Compare per-scorer means over the cases each scorer is about, on both sides.
    print(course.compare(subset_means(course.load(BASELINE), cases), subset_means(report, cases)))


if __name__ == "__main__":
    main()
