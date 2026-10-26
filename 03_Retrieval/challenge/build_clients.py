"""Build the fictional clients the retrieval is measured on.

    uv run python 03_Retrieval/challenge/build_clients.py

Each client is one target row from synthetic_v1.jsonl (its documents are the gold
answer, or nothing for a decline) plus noise: documents from rows of the other two controls, until the client
has about 150 documents. One document is one page, named by its record id.
"""

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "use_case" / "data"
OUT = DATA / "clients"

# Client -> target row in synthetic_v1.jsonl (0-based), as labelled in use_case/evals/retrieval.jsonl.
CLIENTS = {
    "klijent-01": 12, "klijent-02": 24, "klijent-03": 34, "klijent-04": 9,
    "klijent-05": 174, "klijent-06": 189, "klijent-07": 300,
    "klijent-08": 350, "klijent-09": 378, "klijent-10": 355,
}
CLIENT_SIZE = 150
SEED = 7

# Noise that mentions the topic of the target control is left out: it could be a second right
# answer that is not in the gold list.
TOPIC = {
    "POL-001": r"politi|strateg",  # "politi" also catches "politici", where the k turns into c
    "ORG-001": r"\bulog|odgovornost|matric|radnih mjesta|nositelj|zaduž|imenov|odgovorn|ovlašten",
    "EDU-001": r"eduk|obuk|obuč|osposob|radionic|tečaj|izobraz|webinar|upozna|pohađ|razumijev|svjesn|svijest|osvješ|onboarding|čitanj|pročita|poznat|potvrd\w* o (čitanju|primitku)",
}
DECISION_NUMBER = re.compile(r"\b\d{1,4}/20\d\d\b")


def mentions_topic(doc: dict, control: str) -> bool:
    """Does the document mention the topic of the control, in its name or content? Such noise is left out."""
    return re.search(TOPIC[control], (doc["name"] + " " + doc["content"]).lower()) is not None


def numbers(row: dict) -> set[str]:
    """Decision numbers (like 47/2024) in all documents of a row, so noise cannot share one with the target."""
    return {n for d in row["input"]["evidence_documents"] for n in DECISION_NUMBER.findall(d["name"] + " " + d["content"])}


def page(doc: dict) -> str:
    """One document as a Markdown page: the name as the heading, then the content."""
    return f"# {doc['name']}\n\n{doc['content'].strip()}\n"


def main() -> None:
    """Build every client in CLIENTS: target documents plus noise, written as pages, an index and the manifest."""
    rows = [json.loads(line) for line in (DATA / "synthetic_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    targets = set(CLIENTS.values())
    rng = random.Random(SEED)
    manifest = {}

    for client, target in CLIENTS.items():
        control = rows[target]["input"]["control_id"]
        taken = numbers(rows[target])
        pages = {f"r{target}-{d['document_id']}": d for d in rows[target]["input"]["evidence_documents"]}
        target_documents = list(pages)
        skipped = {"other target": 0, "same decision number": 0, "mentions the control": 0}

        candidates = [i for i, r in enumerate(rows) if r["input"]["control_id"] != control]
        rng.shuffle(candidates)
        for i in candidates:
            if len(pages) >= CLIENT_SIZE:
                break
            if i in targets:
                skipped["other target"] += 1
                continue
            if numbers(rows[i]) & taken:
                skipped["same decision number"] += 1
                continue
            for d in rows[i]["input"]["evidence_documents"]:
                if mentions_topic(d, control):
                    skipped["mentions the control"] += 1
                else:
                    pages[f"r{i}-{d['document_id']}"] = d

        noise = [d for rid, d in pages.items() if rid not in target_documents]
        leaked = sum(mentions_topic(d, control) for d in noise)
        if leaked:
            raise SystemExit(f"{client}: {leaked} noise documents mention {control}")

        folder = OUT / client
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.md"):
            old.unlink()
        for record_id, d in pages.items():
            (folder / f"{record_id}.md").write_text(page(d), encoding="utf-8")
        index = "\n".join(f"- [{d['name']}]({rid}.md)" for rid, d in sorted(pages.items()))
        (folder / "index.md").write_text(f"# {client}: dokumenti\n\n{index}\n", encoding="utf-8")

        manifest[client] = {"control_id": control, "target_row": target, "target_documents": target_documents,
                            "documents": len(pages), "skipped": skipped}
        print(f"{client} {control} r{target}: {len(pages)} documents, target documents {len(target_documents)}, skipped {skipped}")

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
