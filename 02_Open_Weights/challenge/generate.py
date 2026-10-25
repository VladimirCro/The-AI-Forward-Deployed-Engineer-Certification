"""Generate synthetic requests from the axes, then dedupe and validate.

    uv run python 02_Open_Weights/challenge/generate.py
    uv run python 02_Open_Weights/challenge/generate.py --limit 3
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "01_Product_Engineering" / "challenge")]

from axes import AXES
from helpers import nb
from helpers.llm import complete
from helpers.sdg import GENERATION_PROMPT, SDGReport, combinations, dedupe, leak_check
from schema import Request, Response

TEMPERATURE = 0.7
DECLINE_TEMPERATURE = 0.3  # a decline should come out the same every time
TOP_P = 0.9
PER_COMBO = 2
DEDUPE_THRESHOLD = 0.7
WORKERS = 4
SEED_LINES = (3, 5, 6)  # 3 contradiction, 5 decline, 6 vacancy; golden 4 left out, its level is disputed

NOT_APPLICABLE = "not applicable"
DECLINE = "irrelevant documents only (decline: no level, ask for evidence)"
EVIDENCE_ONLY = "evidence only, no paper"

OUT_DIR = ROOT / "use_case" / "data"


def possible_combos() -> list[dict]:
    """All axis combinations, without the ones that cannot exist (450 -> 288).

    If an axis does not apply, its value becomes "not applicable" and the duplicates are dropped.
    """
    seen, combos = set(), []
    for combo in combinations(AXES):
        if combo["implementation_evidence"] == DECLINE:
            # irrelevant documents: state and relation do not apply (90 -> 3)
            combo |= {"document_state": NOT_APPLICABLE, "document_relation": NOT_APPLICABLE}
        elif combo["implementation_evidence"] == EVIDENCE_ONLY:
            # no document: its state does not apply (90 -> 15)
            combo |= {"document_state": NOT_APPLICABLE}
        key = tuple(combo.values())
        if key not in seen:
            seen.add(key)
            combos.append(combo)
    return combos


def profile(combo: dict, catalog: dict) -> str:
    """What one combination should look like, with the control's levels."""
    control = catalog[combo["control"]]
    lines = [f"- {axis}: {value}" for axis, value in combo.items()]
    lines.append(f"- control name: {control['name']}")
    for dimension in ("documentation", "implementation"):
        lines.append(f"- {dimension} levels for this control (label against these):")
        lines += [f"    {level}: {text}" for level, text in control[dimension].items()]
    return "\n".join(lines)


def parse(reply: str) -> tuple[list[dict], int, int]:
    """Read JSON lines from a reply. Returns (rows, repaired, unparseable)."""
    rows, repaired, unparseable = [], 0, 0
    for line in reply.splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            rows.append(json.loads(line))
            continue
        except json.JSONDecodeError:
            pass
        try:
            obj, end = json.JSONDecoder().raw_decode(line)
        except json.JSONDecodeError:
            unparseable += 1
            continue
        # the model sometimes adds one closing brace too many
        if line[end:].strip("} \t"):
            unparseable += 1
        else:
            rows.append(obj)
            repaired += 1
    return rows, repaired, unparseable


def is_valid(row: dict) -> str | None:
    """Check a row against the Week 1 schema. Returns the error, or None."""
    try:
        Request(**row["input"])
        Response(**row["output"])
    except Exception as exc:
        return f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="only the first N combinations")
    args = parser.parse_args()

    # 1. Load the config, the catalog and the golden examples.
    cfg = nb.bootstrap(start=ROOT)
    catalog = json.loads((ROOT / "01_Product_Engineering" / "challenge" / "catalog.json").read_text(encoding="utf-8"))
    golden = [json.loads(line) for line in (ROOT / "use_case" / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    examples = "\n".join(json.dumps(golden[n - 1], ensure_ascii=False) for n in SEED_LINES)

    # 2. Build the combinations; --limit keeps only the first N.
    combos = possible_combos()
    if args.limit:
        combos = combos[: args.limit]

    def run(combo: dict) -> dict:
        temperature = DECLINE_TEMPERATURE if combo["implementation_evidence"] == DECLINE else TEMPERATURE
        prompt = GENERATION_PROMPT.format(examples=examples, n=PER_COMBO, profile=profile(combo, catalog))
        try:
            response = complete(cfg, [{"role": "user", "content": prompt}], timeout=300, temperature=temperature, top_p=TOP_P)
        except Exception:
            return {"combo": combo, "reply": None}
        return {"combo": combo, "reply": response.choices[0].message.content or ""}

    # 3. One model call per combination, four at a time.
    report = SDGReport()
    raw, repaired = [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run, combo) for combo in combos]
        for done, future in enumerate(as_completed(futures), 1):
            result = future.result()
            rows, fixed, bad = parse(result["reply"] or "")
            if not rows:
                report.failed_combos += 1  # the call failed or nothing in the reply could be read
            raw += [{**row, "axes": result["combo"]} for row in rows]
            repaired += fixed
            report.unparseable += bad
            if done % 10 == 0 or done == len(combos):
                print(f"{done}/{len(combos)} combinations, {len(raw)} rows so far", flush=True)

    # 4. Dedupe, then check every row against the schema.
    report.generated = len(raw)
    kept, dropped = dedupe(raw, threshold=DEDUPE_THRESHOLD)
    report.after_dedupe = len(kept)
    errors = [is_valid(row) for row in kept]
    valid = [row for row, error in zip(kept, errors) if error is None]
    report.valid = len(valid)
    report.leaks = leak_check(golden, valid)
    first_error = next((error for error in errors if error), None)
    if first_error:
        print("first schema error:", first_error)

    # 5. Write the dataset, what dedupe dropped, and the run report.
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "synthetic_v1.jsonl", "w", encoding="utf-8") as f:
        for row in valid:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(OUT_DIR / "dedupe_dropped.jsonl", "w", encoding="utf-8") as f:
        for row, twin in dropped:
            f.write(json.dumps({"dropped": row, "kept_twin": twin}, ensure_ascii=False) + "\n")

    summary = {
        "date": date.today().isoformat(),
        "model": cfg.llm_model,
        "temperature": TEMPERATURE,
        "decline_temperature": DECLINE_TEMPERATURE,
        "top_p": TOP_P,
        "per_combo": PER_COMBO,
        "dedupe_threshold": DEDUPE_THRESHOLD,
        "combinations": len(combos),
        "generated": report.generated,
        "repaired_lines": repaired,
        "unparseable_lines": report.unparseable,
        "after_dedupe": report.after_dedupe,
        "schema_valid": report.valid,
        "dead_combinations": report.failed_combos,
        "possible_leaks": report.leaks,
    }
    (OUT_DIR / "run_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    print("repaired lines:", repaired)


if __name__ == "__main__":
    main()
