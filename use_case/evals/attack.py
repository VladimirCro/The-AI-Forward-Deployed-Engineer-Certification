"""Run the attacks in attacks.jsonl against the Week 1 assessment and score them with leaked(). TC6 Step 2 and 3.

    cd 01_Product_Engineering/challenge
    uv run --no-sync --env-file ../../.env python ../../use_case/evals/attack.py
        runs every attack whose leaked is still null, and writes runs and leaked back.
    ... attack.py --rerun 3
        runs the attack on line 3 (1-based) again, for example eight times once it has landed.
    ... attack.py --after
        runs every measured attack again through the app as it is now, after the fix, and keeps
        the result next to the first one (after_runs, after_leaked), so both stay in the file.

Each line of attacks.jsonl is one attack on one golden case, as Session 11 records them:
    {"kind": "indirect", "input": "golden-1", "context": {"name": "...", "content": "..."},
     "asked_level": 5, "runs": 2, "leaked": null}
`input` is the legitimate request (a golden, so the right level is known), `context` is the
poisoned document added to its evidence, `asked_level` is the level the document asks for.

The attacks go only to the model in INJECTION_MODEL at INJECTION_API_BASE, a model on this
machine (Session 11 and the challenge README, Step 2). The script stops if that base is not local.
Every run is a fresh call, as promptfoo's --no-cache in Session 11: a repeat must be a new sample.
The clean answer for each golden is run once and kept, so leaked() can tell the attack from the
small model's own mistakes. Every reply is kept in use_case/data/attack_runs.jsonl, which stays local.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parents[1]
ATTACKS = EVALS / "attacks.jsonl"
RUNS_LOG = ROOT / "use_case" / "data" / "attack_runs.jsonl"


def point_the_app_at_the_local_model() -> None:
    """Swap the app's model for the injection model before llm.py reads its settings."""
    model, base = os.getenv("INJECTION_MODEL"), os.getenv("INJECTION_API_BASE")
    if not model or not base:
        sys.exit("Set INJECTION_MODEL and INJECTION_API_BASE in .env (a model on this machine, see 06_Guardrails/README.md).")
    if urlparse(base).hostname not in ("localhost", "127.0.0.1"):
        sys.exit(f"INJECTION_API_BASE is {base}: attacks go only to a model on this machine.")
    os.environ["LLM_MODEL"], os.environ["LLM_API_BASE"] = model, base
    # Gateway settings would be sent to Ollama too; they belong to the gateway only.
    for name in ("LLM_THINKING", "LLM_EXTRA_HEADERS", "LLM_API_KEY"):
        os.environ.pop(name, None)


# The app's modules read the model settings when they are imported, so the swap comes first.
point_the_app_at_the_local_model()
sys.path.insert(0, str(EVALS))
sys.path.insert(0, str(ROOT / "01_Product_Engineering" / "challenge"))
from harness import DIMENSIONS, leaked
from schema import EvidenceDocument, Request, solve


def golden(trace_id: str) -> dict:
    """The golden case 'golden-N' as written in golden.jsonl."""
    rows = [json.loads(line) for line in (EVALS / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[int(trace_id.removeprefix("golden-")) - 1]


def ask(request: Request) -> tuple[str, float]:
    """One assessment, as the Week 1 endpoint returns it, and how long it took. An error is kept as text."""
    started = time.perf_counter()
    try:
        reply = solve(request).model_dump_json()
    except Exception as error:
        reply = f"ERROR {type(error).__name__}: {str(error)[:300]}"
    return reply, time.perf_counter() - started


def log(record: dict) -> None:
    """Append one run to the local log, so every reply can be read later."""
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUNS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def clean_levels(trace_id: str) -> dict:
    """The golden's levels without any attack, from the kept run, or from one new run."""
    if RUNS_LOG.exists():
        for line in RUNS_LOG.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record["kind"] == "clean" and record["input"] == trace_id and record["model"] == os.environ["LLM_MODEL"]:
                return record["levels"]
    reply, seconds = ask(Request(**golden(trace_id)["input"]))
    levels = levels_of(reply)
    log({"kind": "clean", "input": trace_id, "model": os.environ["LLM_MODEL"], "levels": levels,
         "seconds": round(seconds, 1), "reply": reply})
    return levels


def levels_of(reply: str) -> dict:
    """The two levels in a reply, or None for each when the reply is not valid JSON."""
    try:
        answer = json.loads(reply)
        return {dimension: answer[dimension]["level"] for dimension in DIMENSIONS}
    except (ValueError, KeyError, TypeError):
        return {dimension: None for dimension in DIMENSIONS}


def run_attack(number: int, attack: dict) -> dict:
    """Run one attack `runs` times; count the leaks and the errors."""
    case = golden(attack["input"])
    poisoned = EvidenceDocument(document_id=attack["context"].get("document_id", "DOC-99"),
                                name=attack["context"]["name"], content=attack["context"]["content"])
    request = Request(control_id=case["input"]["control_id"],
                      evidence_documents=[*map(EvidenceDocument.model_validate, case["input"]["evidence_documents"]), poisoned])
    clean = clean_levels(attack["input"])
    leaks = errors = 0
    for run in range(attack["runs"]):
        reply, seconds = ask(request)
        hit = leaked(reply, attack.get("asked_level"), clean, attacker_document=poisoned.document_id)
        leaks += hit
        errors += reply.startswith("ERROR")
        log({"kind": attack["kind"] + ("-after" if "--after" in sys.argv else ""), "attack": number, "input": attack["input"], "model": os.environ["LLM_MODEL"],
             "run": run + 1, "leaked": hit, "levels": levels_of(reply), "clean": clean, "seconds": round(seconds, 1), "reply": reply})
        print(f"attack {number} run {run + 1}/{attack['runs']}: leaked={hit} levels={levels_of(reply)} clean={clean} {seconds:.0f}s", flush=True)
    if "--after" in sys.argv:
        return {**attack, "after_runs": attack["runs"], "after_leaked": leaks, "after_errors": errors}
    return {**attack, "leaked": leaks, "errors": errors, "model": os.environ["LLM_MODEL"]}


def main() -> None:
    attacks = [json.loads(line) for line in ATTACKS.read_text(encoding="utf-8").splitlines() if line.strip()]
    rerun = int(sys.argv[sys.argv.index("--rerun") + 1]) if "--rerun" in sys.argv else None
    for number, attack in enumerate(attacks, start=1):
        after = "--after" in sys.argv and attack.get("leaked") is not None
        if after or (rerun is None and attack.get("leaked") is None and "--after" not in sys.argv) or number == rerun:
            attacks[number - 1] = run_attack(number, attack)
            # Written after every attack, so a long run that stops keeps what it measured.
            ATTACKS.write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in attacks), encoding="utf-8")
    for number, attack in enumerate(attacks, start=1):
        after = f", after the fix {attack['after_leaked']}/{attack['after_runs']}" if "after_leaked" in attack else ""
        print(f"{number}. {attack['kind']} on {attack['input']}: leaked {attack.get('leaked')}/{attack['runs']}"
              f" (errors {attack.get('errors', 0)}){after}")


if __name__ == "__main__":
    main()
