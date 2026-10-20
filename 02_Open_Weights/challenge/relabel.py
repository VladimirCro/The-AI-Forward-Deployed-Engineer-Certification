"""Relabel the synthetic rows with a stronger model: same documents, new levels.

    uv run python 02_Open_Weights/challenge/relabel.py
    uv run python 02_Open_Weights/challenge/relabel.py --input <file> --rows 3,17 --out <file>
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "01_Product_Engineering" / "challenge")]

from helpers import nb
from helpers.llm import complete
from schema import Response

MODEL = "openai/claude-opus-5-5"
WORKERS = 6
DATA = ROOT / "use_case" / "data"

PROMPT = """You are a GRC consultant. Assess one control from the client's documents only.

Control {control_id}: {name}

Documentation levels:
{documentation}

Implementation levels:
{implementation}

Documents:
{documents}

Rules:
- Use only what the documents say. Count people, dates and numbers from the documents themselves.
- Missing evidence is not proof that something is not done. If there is no relevant evidence, the level is null.
- A contradiction is two documents that cannot both be true. A postponement or a backup role is not one.
- Pick the highest level whose description is fully met.

The documents were written to match this description: {recipe}
Say whether they really do.

Answer with one JSON object and nothing else:
{{"documentation_level": 1-5 or null, "implementation_level": 1-5 or null,
 "documentation_reason": "...", "implementation_reason": "...",
 "matches_description": true or false, "mismatch": "..." or null}}"""


def ask(cfg, row: dict, catalog: dict) -> dict:
    """One call: the stronger model's levels for one row."""
    control = catalog[row["input"]["control_id"]]
    prompt = PROMPT.format(
        control_id=row["input"]["control_id"],
        name=control["name"],
        documentation="\n".join(f"{k}: {v}" for k, v in control["documentation"].items()),
        implementation="\n".join(f"{k}: {v}" for k, v in control["implementation"].items()),
        documents="\n\n".join(f"{d['document_id']} {d['name']}\n{d['content']}" for d in row["input"]["evidence_documents"]),
        recipe="; ".join(f"{k}: {v}" for k, v in row["axes"].items()),
    )
    # the gateway turns thinking off by default, and this model refuses that
    reply = complete(cfg, [{"role": "user", "content": prompt}], model=MODEL, timeout=300,
                     extra_body={"thinking": {"type": "adaptive"}}).choices[0].message.content or ""
    return json.loads(reply[reply.index("{"): reply.rindex("}") + 1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA / "synthetic_v1.jsonl"))
    parser.add_argument("--rows", default=None, help="only these row numbers (0-based), comma separated")
    parser.add_argument("--out", default=str(DATA / "synthetic_v2.jsonl"))
    args = parser.parse_args()

    # 1. Load the config, the catalog and the rows.
    cfg = nb.bootstrap(start=ROOT)
    catalog = json.loads((ROOT / "01_Product_Engineering" / "challenge" / "catalog.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.rows:
        rows = [rows[int(i)] for i in args.rows.split(",")]

    # 2. Ask the stronger model about every row, six at a time.
    def run(row):
        try:
            return ask(cfg, row, catalog)
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"[:200]}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        answers = list(pool.map(run, rows))

    # 3. Keep the documents, replace the levels, and mark rows whose documents do not match their recipe.
    kept, changed, mismatched, failed = [], 0, 0, 0
    for row, answer in zip(rows, answers):
        if "error" in answer:
            failed += 1
            continue
        if not answer["matches_description"]:
            mismatched += 1
        new = json.loads(json.dumps(row))
        for dim in ("documentation", "implementation"):
            level = answer[f"{dim}_level"]
            if level != row["output"][dim]["level"]:
                changed += 1
            new["output"][dim]["level"] = level
            new["output"][dim]["rationale"] = answer[f"{dim}_reason"]
        Response(**new["output"])
        new["relabel"] = {
            "model": MODEL,
            "old": [row["output"]["documentation"]["level"], row["output"]["implementation"]["level"]],
            "matches_recipe": answer["matches_description"],
            "mismatch": answer["mismatch"],
        }
        kept.append(new)

    # 4. Write the relabelled rows and the numbers.
    with open(args.out, "w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"rows {len(rows)}, kept {len(kept)}, levels changed {changed}, documents do not match the recipe {mismatched}, failed {failed}")
    for row, answer in zip(rows, answers):
        if args.rows:
            print(json.dumps({"control": row["input"]["control_id"], "old": [row["output"]["documentation"]["level"], row["output"]["implementation"]["level"]], "new": answer}, ensure_ascii=False))


if __name__ == "__main__":
    main()
