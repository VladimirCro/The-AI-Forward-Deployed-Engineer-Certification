"""Implementation two of assess_control_for_client: the search as a skill. TC5 Step 3.

The model reads the control's SKILL.md (what the control asks for, without the level
scale), plans the searches in one call, and skills/run.py runs each search as a
subprocess. Classification, solve() and the quote check are the same as in
implementation one; only the way the model reaches the search changes.
"""

import json
import subprocess
import sys
from pathlib import Path

import assess
import retrieval
from llm import chat_with_tools
from schema import Response

SKILLS = Path(__file__).parent / "skills"

TOOLS = [retrieval.tool_schema(
    "search_documents", "Search this client's documents. Give one query for each thing the control asks for.",
    {"queries": {"type": "array", "items": {"type": "string"}}}, ("queries",))]


def dispatch(call) -> tuple[list[str], str]:
    """The model's request as a list of queries, or a message saying what is wrong. Never raises."""
    if call.function.name != "search_documents":
        return [], f"Unknown tool: {call.function.name}. Available tools: search_documents"
    try:
        queries = json.loads(call.function.arguments or "{}")["queries"]
    except (ValueError, KeyError, TypeError) as error:
        return [], f"Arguments were not a JSON object with queries: {error}"
    if not isinstance(queries, list) or not queries or not all(isinstance(q, str) and q.strip() for q in queries):
        return [], "queries must be a list of non-empty strings"
    return queries, ""


def plan_queries(skill: str, client_id: str) -> list[str]:
    """One model call that plans every search; a second try if the request was wrong."""
    messages = [{"role": "system", "content": skill},
                {"role": "user", "content": f"Plan the searches for {client_id}: call search_documents once with all your queries."}]
    for _ in range(2):
        msg = chat_with_tools(messages, TOOLS)
        calls = msg.tool_calls or []
        if not calls:
            messages += [{"role": "assistant", "content": msg.content or ""},
                         {"role": "user", "content": "Call search_documents with your queries."}]
            continue
        queries, problem = dispatch(calls[0])
        if queries:
            return queries
        shaped = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls]
        messages += [{"role": "assistant", "content": msg.content or "", "tool_calls": shaped}]
        messages += [{"role": "tool", "tool_call_id": c.id, "content": problem} for c in calls]
    # No plan is a failure, not an empty search: it must not turn into "no evidence found".
    raise RuntimeError("The model did not plan any searches.")


def run_skill(client_id: str, query: str, k: int = retrieval.TOP_K) -> str:
    """Run the skill's script the way an agent would: as a subprocess."""
    finished = subprocess.run([sys.executable, str(SKILLS / "run.py"), client_id, query, str(k)],
                              capture_output=True, text=True, timeout=300)
    if finished.returncode != 0:
        # A failed search must not look like a search that found nothing.
        raise RuntimeError(f"run.py failed: {finished.stderr[-300:]}")
    return finished.stdout


def find_candidates_with_skill(client_id: str, control_id: str) -> dict[str, str]:
    """The documents the skill's searches name for this control, by record id."""
    pages, _ = retrieval.load_client(client_id)
    skill = (SKILLS / control_id.lower() / "SKILL.md").read_text(encoding="utf-8")
    results = [run_skill(client_id, query) for query in plan_queries(skill, client_id)]
    return {record_id: pages[record_id] for record_id in retrieval.found_documents("\n".join(results), pages)}


def find_candidates_with_skill_loop(client_id: str, control_id: str) -> dict[str, str]:
    """The same skill used in a loop: read SKILL.md, run one search, look at the result, search again.

    find_candidates_with_skill plans every search before it sees a result, as Session 10's
    call_with_skill does. This one keeps the Week 3 loop, so the two differ only in that.
    """
    pages, _ = retrieval.load_client(client_id)
    skill = (SKILLS / control_id.lower() / "SKILL.md").read_text(encoding="utf-8")
    tools = [retrieval.tool_schema(
        "search_documents", "Search this client's documents for one query. Search again with a new query when evidence is incomplete.",
        {"query": {"type": "string"}, "k": {"type": "integer"}}, ("query",))]
    # The same k as the Week 3 search tool, so the loop and the tool see as many documents per search.
    funcs = {"search_documents": lambda query, k=retrieval.TOP_K: run_skill(client_id, query, k)}
    task = f"{skill}\n\nClient: {client_id}. Find every document among this client's documents that is evidence for this control."
    result = retrieval.run_agent(task, tools, funcs)
    return {record_id: pages[record_id] for record_id in retrieval.found_documents(result["answer"], pages)}


def assess_control_with_skill(client_id: str, control_id: str) -> Response:
    """The Week 3 flow with the skill's search in front."""
    return assess.assess_control_for_client(client_id, control_id, find=find_candidates_with_skill)


def assess_control_with_skill_loop(client_id: str, control_id: str) -> Response:
    """The Week 3 flow with the skill used in a search loop."""
    return assess.assess_control_for_client(client_id, control_id, find=find_candidates_with_skill_loop)
