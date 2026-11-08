"""The Session 10 counter, pointed at the Week 3 endpoint. TC5 Steps 4 and 5.

    cd 01_Product_Engineering/challenge
    uv run --no-sync --env-file ../../.env python ../../05_Agent_Architecture/challenge/measure.py klijent-01 POL-001

For one request it reports the four columns Step 4 asks for: model calls, capability
calls (runs of the search, counted in run.py for the skill), seconds and tokens, plus the bytes each search call
returned and the size of the final answer, for Step 5. Needs the clients built by
build_clients.py and .env with LLM_THINKING=between_tools.
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(APP))

import litellm
import assess
import retrieval
import skill


class Meter:
    """Counts model round trips and the tokens they cost (Session 10's Meter).

    Our code streams the assessment, and a streamed reply carries no usage. LiteLLM's
    success callback gets the finished response with its usage, so the meter listens
    there instead of being handed each response. Chunk callbacks arrive without usage
    and are not counted.
    """

    def __init__(self):
        self.calls = 0
        self.tokens = 0
        self.embedding_tokens = 0
        self.lock = threading.Lock()

    def __call__(self, kwargs, response, start_time, end_time):
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        with self.lock:
            # Embedding calls report usage too; they are not model round trips, so they get their own total.
            if isinstance(response, litellm.EmbeddingResponse):
                self.embedding_tokens += usage.total_tokens or 0
                return
            self.calls += 1
            self.tokens += usage.total_tokens or 0


class SearchCounter:
    """Counts the runs of the search tool and the bytes each one returned.

    The deep dive's counting wrapper: the endpoint builds its search tool inside
    find_candidates, so the counter wraps retrieval.search_tool for the time of one
    request rather than taking the function as an argument.
    """

    def __init__(self):
        self.calls = 0
        self.bytes = []

    def wrap(self, search_tool):
        def counted_search_tool(pages, rank):
            tools, funcs = search_tool(pages, rank)
            search_chunks = funcs["search_chunks"]

            def counted(query: str, k: int = retrieval.TOP_K) -> str:
                result = search_chunks(query, k)
                self.calls += 1
                self.bytes.append(len(result.encode("utf-8")))
                return result

            return tools, {**funcs, "search_chunks": counted}

        return counted_search_tool


class FirstTurn:
    """How many tool calls the model asked for in its first turn: four searches in one turn
    are one round trip, not four (Step 4)."""

    def __init__(self):
        self.tool_calls = None

    def wrap(self, chat_with_tools):
        def counted(messages, tools):
            msg = chat_with_tools(messages, tools)
            if self.tool_calls is None:
                self.tool_calls = len(msg.tool_calls or [])
            return msg

        return counted


def endpoint_today(client_id: str, control_id: str) -> str:
    """Implementation one: the Week 3 endpoint as it is."""
    return assess.assess_control_for_client(client_id, control_id).model_dump_json()


def endpoint_with_skill(client_id: str, control_id: str) -> str:
    """Implementation two: the search as a skill (skill.py)."""
    return skill.assess_control_with_skill(client_id, control_id).model_dump_json()


def measure(way, client_id: str, control_id: str) -> dict:
    """Run one way on one request and count what it did."""
    meter, counter, first = Meter(), SearchCounter(), FirstTurn()
    original, original_chat, original_skill_chat = retrieval.search_tool, retrieval.chat_with_tools, skill.chat_with_tools
    retrieval.search_tool = counter.wrap(original)
    retrieval.chat_with_tools = first.wrap(original_chat)
    skill.chat_with_tools = first.wrap(original_skill_chat)
    litellm.success_callback = [meter]
    # The skill searches in a subprocess, where neither counter can see; run.py writes one line per search here.
    log = Path(tempfile.mkstemp(suffix=".jsonl")[1])
    os.environ["SKILL_CALL_LOG"] = str(log)
    started = time.perf_counter()
    try:
        answer = way(client_id, control_id)
    finally:
        seconds = time.perf_counter() - started
        retrieval.search_tool, retrieval.chat_with_tools, skill.chat_with_tools = original, original_chat, original_skill_chat
    # LiteLLM runs success callbacks on a thread after the call returns; give the last one time to land.
    time.sleep(3)
    litellm.success_callback = []
    far_side = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    log.unlink()
    counter.calls += len(far_side)
    counter.bytes += [entry["bytes"] for entry in far_side]
    return {
        "model calls": meter.calls,
        "capability calls": counter.calls,
        "seconds": round(seconds, 1),
        "tokens": meter.tokens,
        "embedding tokens": meter.embedding_tokens,
        "tool calls in the first turn": first.tool_calls,
        "bytes per search call": round(sum(counter.bytes) / len(counter.bytes)) if counter.bytes else 0,
        "answer bytes": len(answer.encode("utf-8")),
    }


if __name__ == "__main__":
    client_id, control_id = sys.argv[1], sys.argv[2]
    for name, way in (("endpoint today", endpoint_today), ("with the skill", endpoint_with_skill)):
        print(f"{client_id} {control_id}, {name}:", measure(way, client_id, control_id))
