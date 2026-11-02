"""Build a client for each golden and each picked synthetic row, so all fifty traces go through the Week 3 endpoint.

Same rules as the TC3 clients: the functions come from build_clients.py, which is not changed.
Each client is the case's own documents plus noise from rows of the other two controls,
about 150 documents in all. Noise that mentions the topic of the case's control is left out,
and so are rows that share a decision number with the case.

The ten TC3 clients (klijent-01 to klijent-10) and their manifest.json are not touched.
The new clients go next to them; what each one holds is written to manifest_w4.json.

    cd 01_Product_Engineering/challenge
    uv run --no-sync python ../../use_case/evals/build_trace_clients.py
"""

import json
import random
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
APP = EVALS.parents[1] / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(EVALS))
sys.path.insert(0, str(APP))
from collect_traces import SYNTHETIC_COUNT, pick_synthetic, read_jsonl  # the same fifty cases

from build_clients import CLIENT_SIZE, CLIENTS, OUT, mentions_topic, numbers, page

DATA = EVALS.parent / "data"
SEED = 7


def trace_clients() -> dict[str, tuple[str, dict]]:
    """Client name -> (record id prefix, row with input documents) for the 6 goldens and the synthetic sample."""
    clients = {}
    for number, row in enumerate(read_jsonl(EVALS / "golden.jsonl"), start=1):
        # r9001 to r9006: the app only reads ids shaped r<number>-DOC-<number>, and synthetic rows stop at 547.
        clients[f"golden-{number}"] = (f"r{9000 + number}", row)
    for index, row in pick_synthetic(read_jsonl(DATA / "synthetic_v2.jsonl"), SYNTHETIC_COUNT):
        clients[f"synthetic-r{index}"] = (f"r{index}", row)
    return clients


def main() -> None:
    """Write each client's pages and index, stop if any noise document mentions the control."""
    noise_rows = read_jsonl(DATA / "synthetic_v1.jsonl")
    clients = trace_clients()
    # Rows that are a case somewhere (TC3 or here) are never used as noise.
    cases = set(CLIENTS.values()) | {int(prefix[1:]) for prefix, _ in clients.values() if prefix.startswith("r")}
    rng = random.Random(SEED)
    manifest = {}

    for client, (prefix, row) in clients.items():
        if client in CLIENTS:
            raise SystemExit(f"{client} would overwrite a TC3 client")
        control = row["input"]["control_id"]
        taken = numbers(row)
        pages = {f"{prefix}-{d['document_id']}": d for d in row["input"]["evidence_documents"]}
        case_documents = list(pages)
        skipped = {"other case": 0, "same decision number": 0, "mentions the control": 0}

        candidates = [i for i, r in enumerate(noise_rows) if r["input"]["control_id"] != control]
        rng.shuffle(candidates)
        for i in candidates:
            if len(pages) >= CLIENT_SIZE:
                break
            if i in cases:
                skipped["other case"] += 1
                continue
            if numbers(noise_rows[i]) & taken:
                skipped["same decision number"] += 1
                continue
            for d in noise_rows[i]["input"]["evidence_documents"]:
                if mentions_topic(d, control):
                    skipped["mentions the control"] += 1
                else:
                    pages[f"r{i}-{d['document_id']}"] = d

        noise = [d for record_id, d in pages.items() if record_id not in case_documents]
        leaked = sum(mentions_topic(d, control) for d in noise)
        if leaked:
            raise SystemExit(f"{client}: {leaked} noise documents mention {control}")

        folder = OUT / client
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.md"):
            old.unlink()
        for record_id, d in pages.items():
            (folder / f"{record_id}.md").write_text(page(d), encoding="utf-8")
        index = "\n".join(f"- [{d['name']}]({record_id}.md)" for record_id, d in sorted(pages.items()))
        (folder / "index.md").write_text(f"# {client}: dokumenti\n\n{index}\n", encoding="utf-8")

        manifest[client] = {"control_id": control, "case_documents": case_documents,
                            "documents": len(pages), "skipped": skipped}
        print(f"{client} {control}: {len(pages)} documents, case documents {len(case_documents)}, skipped {skipped}")

    (OUT / "manifest_w4.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
