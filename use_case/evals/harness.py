"""TC4 harness: the cases, four model-free scorers, the judge, and the generated failures.

The loop, the averages and saving a run come from the course's helpers/harness.py
(`run`, `save`, `load`, `compare`) and the judge from helpers/judge.py. This file
adds what is ours: which cases, what "correct" means for each of them, and the
scorers, each tied to one line of failures.md.

    cd 01_Product_Engineering/challenge
    uv run --no-sync python ../../use_case/evals/harness.py
        prints the echo / oracle / app table (Step 2). The app column replays the
        answers in use_case/data/traces_w4.jsonl, so it needs no model call.
    uv run --no-sync --env-file ../../.env python ../../use_case/evals/harness.py judge
        checks the judge (Step 3): separation, then agreement with my verdicts,
        about 60 Opus calls.
    uv run --no-sync --env-file ../../.env python ../../use_case/evals/harness.py synthetic [--judge]
        breaks my accepted answers into synthetic.jsonl and prints the detection
        table (Step 4); --judge runs the judge over them too, about 110 Opus calls.

Everything in use_case/data/ stays local, so a clean checkout cannot run this: the
cases come from use_case/data/synthetic_v2.jsonl and the traces from traces_w4.jsonl.
"""

import json
import os
import sys
from dataclasses import replace
from pathlib import Path

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parents[1]
sys.path.insert(0, str(EVALS))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "01_Product_Engineering" / "challenge"))  # llm.py, for the judge
from collect_traces import all_cases, read_jsonl  # the same fifty cases the traces came from
from helpers.harness import run
from helpers.judge import Judge

TRACES = EVALS.parent / "data" / "traces_w4.jsonl"

# Cases where the right answer is "no level": the client handed in nothing that is
# evidence for this control. From retrieval.jsonl (decline cases) and my verdicts.
SHOULD_DECLINE = {"retrieval-klijent-04", "retrieval-klijent-10", "golden-5",
                  "synthetic-r180", "synthetic-r181"}

UNRESOLVED_GOLDENS = {"golden-4", "golden-6"}

# Goldens whose level is unresolved: any level in the list is accepted.
LEVEL_RANGES = {
    ("golden-4", "implementation"): [2, 3],  # 58 % coverage, threshold for 3 not agreed
    ("golden-6", "implementation"): [3, 4],  # 3 as before, or 4 if the stand-in took over all duties (consultant, 1 Nov)
}


def parse(actual: str) -> dict:
    """The app's answer as a dict; anything that is not JSON counts as an empty answer."""
    try:
        reply = json.loads(actual)
    except (TypeError, ValueError):
        return {}
    return reply if isinstance(reply, dict) else {}


def documents_found(actual: str, case: dict) -> float:
    """failures.md #1: the search misses an important document of the case.

    Share of the case's documents that are in the answer's sources.
    """
    expected = case["expected_sources"]
    if not expected:
        return 1.0
    sources = parse(actual).get("sources") or []
    found = [doc for doc in expected if doc in sources]
    return len(found) / len(expected)


def level_matches(actual: str, case: dict) -> float:
    """failures.md #2: the level has no basis in the evidence.

    Share of the two dimensions whose level is one the golden accepts. Only goldens
    are scored: the synthetic levels are noisy and the retrieval cases have none.
    """
    expected = case["expected_levels"]
    if not expected:
        return 1.0
    reply = parse(actual)
    right = 0
    for dimension, allowed in expected.items():
        level = (reply.get(dimension) or {}).get("level")
        if level in allowed:
            right += 1
    return right / len(expected)


def declines_when_no_evidence(actual: str, case: dict) -> float:
    """failures.md #3: it builds the answer on documents that are not evidence.

    On a case with nothing to assess, the answer must give no level and no sources.
    """
    if not case["should_decline"]:
        return 1.0
    reply = parse(actual)
    levels = [(reply.get(dimension) or {}).get("level") for dimension in ("documentation", "implementation")]
    return float(levels == [None, None] and not reply.get("sources"))


def only_case_documents(actual: str, case: dict) -> float:
    """failures.md #3: it builds the answer on documents that are not evidence.

    Share of the answer's sources that are documents of the case. Added after the
    Step 4 detection table showed that no scorer caught an unrelated source.
    """
    sources = parse(actual).get("sources") or []
    if not sources:
        return 1.0
    expected = case["expected_sources"]
    return len([doc for doc in sources if doc in expected]) / len(sources)


SCORERS = {
    "documents_found": documents_found,
    "level_matches": level_matches,
    "declines_when_no_evidence": declines_when_no_evidence,
    "only_case_documents": only_case_documents,
}

# Which cases each scorer is about. A scorer returns 1.0 on the others, so averaging it
# over all fifty would hand every system free points: echo would score 0.9 on levels.
APPLIES = {
    "documents_found": lambda case: bool(case["expected_sources"]),
    "level_matches": lambda case: bool(case["expected_levels"]),
    "declines_when_no_evidence": lambda case: case["should_decline"],
    "only_case_documents": lambda case: True,
}


def harness_cases() -> list[dict]:
    """The fifty cases in the shape helpers.harness.run expects: input as text, plus what is right."""
    cases = []
    for case in all_cases():
        trace_id = case["trace_id"]
        decline = trace_id in SHOULD_DECLINE
        if "gold" in case["reference"]:
            expected_sources = case["reference"]["gold"]
        elif decline:
            expected_sources = []
        else:
            expected_sources = [f"{case['record_prefix']}-{doc['document_id']}" for doc in case["case_documents"]]
        expected_levels = {}
        if case["source"] == "golden.jsonl":
            for dimension in ("documentation", "implementation"):
                level = case["reference"][dimension]["level"]
                expected_levels[dimension] = LEVEL_RANGES.get((trace_id, dimension), [level])
        cases.append({"trace_id": trace_id, "input": json.dumps(case["input"], ensure_ascii=False),
                      "expected_sources": expected_sources, "expected_levels": expected_levels,
                      "should_decline": decline})
    return cases


def echo(question: str) -> str:
    """The worst system: hands the request back. Every real system must beat it."""
    return question


def make_oracle(cases: list[dict]):
    """The best system: answers each case with exactly what is right. Every scorer must give it 1.0."""
    answers = {}
    for case in cases:
        levels = {dimension: {"level": allowed[0]} for dimension, allowed in case["expected_levels"].items()}
        if case["should_decline"]:
            levels = {"documentation": {"level": None}, "implementation": {"level": None}}
        answers[case["input"]] = json.dumps({**levels, "sources": case["expected_sources"]}, ensure_ascii=False)
    return lambda question: answers[question]


def make_replay():
    """The app as it answered on 1 Nov 2026, read back from the traces: no model call."""
    answers = {}
    for line in TRACES.read_text(encoding="utf-8").splitlines():
        trace = json.loads(line)
        answers[json.dumps(trace["input"], ensure_ascii=False)] = json.dumps(trace["actual"], ensure_ascii=False)
    return lambda question: answers[question]


def traced_cases() -> list[dict]:
    """The cases that have a 1 Nov trace: the fifty read in Step 1. Goldens added later have none."""
    traced = {json.dumps(json.loads(line)["input"], ensure_ascii=False)
              for line in TRACES.read_text(encoding="utf-8").splitlines()}
    return [case for case in harness_cases() if case["input"] in traced]


def bootstrap_ci(scores, n_resamples: int = 5000, level: float = 0.95, seed: int = 0):
    """Confidence interval for a mean, by resampling (Session 7, Task 5).

    Resample the scores with replacement thousands of times; the spread of those
    means is how much the number would move on a different set of the same size.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    arr = np.asarray(scores, dtype=float)
    means = arr[rng.integers(0, len(arr), size=(n_resamples, len(arr)))].mean(axis=1)
    lo, hi = np.percentile(means, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(arr.mean()), float(lo), float(hi)


def subset_means(report, cases: list[dict]):
    """The same run with each scorer averaged over the cases it is about, so compare() sees real drops."""
    means = {}
    for label in report.means:
        applies = APPLIES.get(label, lambda case: True)
        scores = [result.scores[label] for result, case in zip(report.results, cases) if applies(case)]
        means[label] = sum(scores) / len(scores)
    return replace(report, means=means)


# ----------------------------------------------------------------- Step 3: the judge

# A different, stronger model than the app's Sonnet 5.5; set in .env like the app's model.
JUDGE_MODEL = os.getenv("LLM_JUDGE_MODEL", "openai/claude-opus-5-5")

# One checkable property, for failures.md #2: the level has no basis in the evidence.
# Second wording (2 Nov): the first one failed agreement (0.50 vs floor 0.50) because it
# punished every honest caveat; this one asks only about the key condition of the level.
# {expected} is not used: the answer carries its own level, the catalog statement for
# that level and its rationale, which is all this question needs.
LEVEL_BASIS_RUBRIC = """You check one answer from a tool that proposes a maturity level for a security control from a client's documents. A GRC consultant reviews every answer afterwards and checks details herself.

Answer (JSON):
{actual}

Question: is each level backed by the key condition that separates it from the level below?

Look at documentation and implementation separately. Each has "level", "level_statement" (what the level requires) and "rationale".
- Score 0 if a dimension has a level while its own rationale says the key condition of that level, the one that separates it from the level below, is not proven. Example of a 0: implementation level 3 for a policy, where level 3 requires formal adoption by the board, and the rationale says "formal adoption by the board has not been proven".
- Notes about details the consultant can check later (the full text of a document, the content of an annex, whether every element is covered) do not make it 0, as long as the key condition is shown.
- Score 0 if the answer is not a JSON assessment at all.
- Otherwise score 1. Example of a 1: implementation level 2 for a policy that is a draft whose adoption was postponed, with the note "check that the draft covers all basic elements".

Reply with JSON only: {{"score": 0 or 1, "why": "<one sentence>"}}"""


class GatewayJudge(Judge):
    """The course's Judge, asking through our llm.py so the gateway's thinking setting is sent.

    helpers/llm.py does not know that Opus 5.5 behind our gateway needs
    thinking=between_tools, and helpers/ is not ours to change; calibrate(),
    score() and the 0.0-on-unparseable rule all stay the course's.
    """

    def _ask(self, prompt: str) -> str:
        from litellm import completion

        from llm import API_BASE, EXTRA_HEADERS, THINKING

        # Same settings as the app's calls in llm.py, plus retries: a gateway error once
        # (2 Nov) must not turn into a 0 from the judge.
        kwargs = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                  "timeout": self.timeout, "num_retries": self.max_retries}
        if API_BASE:
            kwargs["api_base"] = API_BASE
        if EXTRA_HEADERS:
            kwargs["extra_headers"] = EXTRA_HEADERS
        if THINKING:
            kwargs["extra_body"] = {"thinking": {"type": THINKING}}
        return completion(**kwargs).choices[0].message.content or ""


def golden_cases(cases: list[dict]) -> list[dict]:
    """The six goldens with their accepted answer as `output`, the shape Judge.calibrate expects."""
    outputs = {f"golden-{n}": row["output"] for n, row in enumerate(read_jsonl(EVALS / "golden.jsonl"), start=1)}
    return [{**case, "output": json.dumps(outputs[case["trace_id"]], ensure_ascii=False)}
            for case in cases if case["trace_id"] in outputs]


def check_judge() -> None:
    """Separation on the goldens (accepted vs wrong vs echo), then agreement with my fifty verdicts."""
    cases = traced_cases()
    judge = GatewayJudge(None, rubric=LEVEL_BASIS_RUBRIC, model=JUDGE_MODEL)

    # Goldens 4 and 6 have unresolved levels, so their answers are not known-good and
    # cannot be used to check separation.
    goldens = [case for case in golden_cases(cases) if case["trace_id"] not in UNRESOLVED_GOLDENS]
    calibration = judge.calibrate(goldens)
    echo_mean = sum(judge._raw_score(echo(case["input"]), case) for case in goldens) / len(goldens)
    print(f"Separation on {len(goldens)} goldens: accepted (oracle) {calibration.accepted:.2f}, "
          f"echo {echo_mean:.2f}, wrong answer {calibration.wrong:.2f}, passed: {calibration.passed}")
    if not calibration.passed:
        print("The judge failed separation, so it is not used.")
        return

    replay = make_replay()
    verdicts = {}
    for line in (EVALS / "human_scores.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        verdicts[row["trace_id"]] = row["pass"]
    rows = []
    for case in cases:
        judged = judge.score(replay(case["input"]), case) >= 0.5
        rows.append({"trace_id": case["trace_id"], "human": verdicts[case["trace_id"]], "judge": judged})
        print(f"{case['trace_id']}: human {verdicts[case['trace_id']]}, judge {judged}", flush=True)
    (EVALS.parent / "data" / "judge_agreement.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")

    agree = sum(row["human"] == row["judge"] for row in rows) / len(rows)
    human_pass = sum(row["human"] for row in rows) / len(rows)
    judge_pass = sum(row["judge"] for row in rows) / len(rows)
    # Chance floor: how often two raters with these pass rates would agree by luck.
    floor = human_pass * judge_pass + (1 - human_pass) * (1 - judge_pass)
    print(f"Agreement with my {len(rows)} verdicts: {agree:.2f} (chance floor {floor:.2f})")


# ----------------------------------------------------------------- Step 4: generated failures

CATALOG = json.loads((ROOT / "01_Product_Engineering" / "challenge" / "catalog.json").read_text(encoding="utf-8"))
CLIENTS = EVALS.parent / "data" / "clients"
SYNTHETIC = EVALS / "synthetic.jsonl"

# Each corruption breaks an answer I accepted in one known way, tied to a line of failures.md.
CORRUPTIONS = {
    "drop_source": "#1 the search misses an important document",
    "level_up": "#2 the level has no basis in the evidence",
    "unrelated_source": "#3 it builds the answer on documents that are not evidence",
    "skip_decline": "#3 it does not decline when there is no evidence",
    "false_decline": "declines where an answer was required",
}


# The judge reads levels and rationales, not the list of sources, so it runs only on these.
JUDGE_READS = {"level_up", "false_decline", "skip_decline"}


def noise_documents(case: dict) -> list[str]:
    """Documents in the client's folder that are not evidence for this case, in a fixed order."""
    client = json.loads(case["input"])["client_id"]
    return sorted(p.stem for p in (CLIENTS / client).glob("r*-DOC-*.md") if p.stem not in case["expected_sources"])


def set_level(answer: dict, dimension: str, level, control_id: str) -> None:
    """Change one level and its catalog statement, leaving the rationale as it was."""
    answer[dimension]["level"] = level
    answer[dimension]["level_statement"] = CATALOG[control_id][dimension][str(level)] if level else None


def corrupt(answer: dict, case: dict, kind: str, hard: bool) -> dict | None:
    """Break an accepted answer in one known way; None if that way does not apply to this case."""
    broken = json.loads(json.dumps(answer))
    control_id = answer["control_id"]
    sources = broken.get("sources") or []
    if kind == "drop_source":
        present = [doc for doc in case["expected_sources"] if doc in sources]
        if not present:
            return None
        dropped = present[-1:] if hard and len(present) > 1 else present
        broken["sources"] = [doc for doc in sources if doc not in dropped]
    elif kind == "level_up":
        level = broken["implementation"]["level"]
        if level is None or level == 5:
            return None
        set_level(broken, "implementation", level + 1 if hard else 5, control_id)
    elif kind == "unrelated_source":
        if case["should_decline"]:
            return None
        broken["sources"] = sources + noise_documents(case)[: 1 if hard else 3]
    elif kind == "skip_decline":
        if not case["should_decline"]:
            return None
        for dimension in ("documentation", "implementation"):
            set_level(broken, dimension, 2, control_id)
        broken["sources"] = noise_documents(case)[:1]
    elif kind == "false_decline":
        if case["should_decline"] or broken["implementation"]["level"] is None:
            return None
        for dimension in ("documentation", "implementation"):
            set_level(broken, dimension, None, control_id)
        broken["sources"] = []
    return broken


def build_synthetic() -> list[dict]:
    """Break every answer I accepted, one hard and one easy version where both exist; write synthetic.jsonl."""
    cases = {case["trace_id"]: case for case in harness_cases()}
    replay = make_replay()
    verdicts = [json.loads(line) for line in (EVALS / "human_scores.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = []
    for verdict in verdicts:
        if verdict["pass"] is not True:
            continue
        case = cases[verdict["trace_id"]]
        original = json.loads(replay(case["input"]))
        for kind in CORRUPTIONS:
            versions = [True] if kind in ("skip_decline", "false_decline") else [False, True]
            for hard in versions:
                broken = corrupt(original, case, kind, hard)
                if broken is None or broken == original:
                    continue
                difficulty = "hard" if hard and kind not in ("skip_decline", "false_decline") else "easy"
                rows.append({"trace_id": case["trace_id"], "input": case["input"],
                             "actual": json.dumps(broken, ensure_ascii=False),
                             "original": json.dumps(original, ensure_ascii=False),
                             "failure": kind, "failure_line": CORRUPTIONS[kind], "difficulty": difficulty})
    SYNTHETIC.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return rows


def detection_table(with_judge: bool) -> str:
    """Per failure mode and difficulty, the share of broken answers each scorer scores below the original."""
    cases = {case["trace_id"]: case for case in harness_cases()}
    rows = build_synthetic()
    scorers = dict(SCORERS)
    if with_judge:
        judge = GatewayJudge(None, rubric=LEVEL_BASIS_RUBRIC, model=JUDGE_MODEL)
        judge.calibrate([case for case in golden_cases(list(cases.values())) if case["trace_id"] not in UNRESOLVED_GOLDENS])
        scorers["judge_level_basis"] = judge.score
    caught = {}
    original_scores = {}
    for row in rows:
        case = cases[row["trace_id"]]
        for label, scorer in scorers.items():
            if label == "judge_level_basis" and row["failure"] not in JUDGE_READS:
                continue
            key = (row["trace_id"], label)
            if key not in original_scores:
                original_scores[key] = scorer(row["original"], case)
            hit = scorer(row["actual"], case) < original_scores[key]
            caught.setdefault((row["failure"], row["difficulty"]), {}).setdefault(label, []).append(hit)
        print(f"{row['trace_id']} {row['failure']} {row['difficulty']}", flush=True)
    labels = list(scorers)
    lines = ["| Failure mode | Difficulty | Generated | " + " | ".join(labels) + " |",
             "| --- | --- | ---: |" + " ---: |" * len(labels)]
    for (failure, difficulty), hits in caught.items():
        count = len(hits["documents_found"])
        cells = [f"{sum(hits[label]) / count:.2f}" if label in hits else "not run" for label in labels]
        lines.append(f"| {failure} | {difficulty} | {count} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def scorer_table(cases: list[dict], systems: dict) -> str:
    """One row per scorer, one column per system; each scorer averaged over the cases it is about."""
    lines = ["| Scorer | Cases | " + " | ".join(systems) + " |", "| --- | ---: |" + " ---: |" * len(systems)]
    for label, scorer in SCORERS.items():
        subset = [case for case in cases if APPLIES[label](case)]
        means = [run(subset, system, {label: scorer}, name=name).means[label] for name, system in systems.items()]
        lines.append(f"| {label} | {len(subset)} | " + " | ".join(f"{mean:.2f}" for mean in means) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    if sys.argv[1:] == ["judge"]:
        check_judge()
        sys.exit()
    if sys.argv[1:2] == ["synthetic"]:
        table = detection_table(with_judge="--judge" in sys.argv)
        print(table)
        (EVALS.parent / "data" / "detection_table.md").write_text(table + "\n", encoding="utf-8")
        sys.exit()
    cases = traced_cases()
    print(scorer_table(cases, {"echo": echo, "oracle": make_oracle(cases), "app (1 Nov)": make_replay()}))
