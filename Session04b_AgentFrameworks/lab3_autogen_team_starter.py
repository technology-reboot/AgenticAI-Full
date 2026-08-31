# Lab 3 — The same task in AutoGen, then compare  (STARTER)
#
# Fill in the three TODO blocks: the agents, the termination condition, and the
# comparison block. The search tool, topic loading and metrics emission are done.
#
# PROJECT STATUS: AutoGen entered maintenance mode in October 2025 (bug and
# security fixes only, community-managed). Its successors are Microsoft Agent
# Framework 1.0 (GA April 2026, merging AutoGen with Semantic Kernel) and the
# community fork AG2. This lab teaches the conversational pattern, which
# transfers to both.
#
# Instructor notes:
# - Run the default path first, THEN the unbounded run.
# - Warn the room the unbounded run costs money; stop it after ~30 seconds.
# - Expect AutoGen to use more tokens than CrewAI — every agent sees the full
#   shared history each turn. That is the structural difference, not a defect.

import asyncio
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("Missing OPENAI_API_KEY — add it to .env and re-run.")

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Same model as Lab 2 — the comparison is only meaningful with the model held
# constant.
MODEL = "gpt-4o-mini"
DEFAULT_TOPIC = "India's DPDP Act obligations for AI systems handling customer data"

UNBOUNDED = False  # set True to remove MaxMessageTermination — Ctrl-C to stop


# --- R1: search tool (done for you) --------------------------------------
async def search_web(query: str) -> str:
    """Search the web for `query` and return the top 3-5 results as text, each
    with a title, a short snippet and a URL. Call this to find source material
    before making any factual claim."""
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    def _run():
        with DDGS() as ddg:
            return list(ddg.text(query, max_results=5))

    hits = await asyncio.to_thread(_run)
    if not hits:
        return "No results."
    return "\n".join(
        f"- {h.get('title', '')}: {h.get('body', '')[:200]} ({h.get('href', '')})"
        for h in hits
    )


def load_topic():
    try:
        with open("lab2_metrics.json", encoding="utf-8") as fh:
            topic = json.load(fh).get("topic")
        if topic:
            return topic
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    print("[warn] lab2_metrics.json not found — using the default topic; the "
          "comparison will be approximate.")
    return DEFAULT_TOPIC


# --- R2: three agents ---------------------------------------------------
def build_agents(model_client):
    # TODO (1/3): create three AssistantAgent instances, each carrying the SAME
    # intent as its Lab 2 CrewAI counterpart (add a comment naming the mirror):
    #   researcher  -> Lab 2 "Research Analyst"; tools=[search_web];
    #                  "find and cite sources, never a fact without a URL"
    #   summarizer  -> Lab 2 "Briefing Writer"; tools=[];
    #                  "200-word brief from the findings, add nothing"
    #   critic      -> Lab 2 "Quality Critic"; tools=[];
    #                  "flag any claim not in the findings; reply APPROVED when clean"
    #   If UNBOUNDED: weaken the critic's system_message so it will not say
    #   APPROVED (tell it to always demand one more improvement).
    # Return them as a list [researcher, summarizer, critic].
    raise NotImplementedError


# --- R3: team and termination -----------------------------------------
def build_team(agents):
    # TODO (2/3): build the termination condition and the team.
    #   default : stop = TextMentionTermination("APPROVED") | MaxMessageTermination(12)
    #   UNBOUNDED: stop = TextMentionTermination("APPROVED")   (no safety net)
    #   The text condition is the INTENT; MaxMessageTermination is the SAFETY NET.
    #   Shipping only the first is how you get an unbounded run (FM-3).
    #   return RoundRobinGroupChat(agents, termination_condition=stop)
    raise NotImplementedError


def sum_tokens(messages):
    prompt = completion = 0
    seen = False
    for m in messages:
        usage = getattr(m, "models_usage", None)
        if not usage:
            continue
        seen = True
        prompt += getattr(usage, "prompt_tokens", 0) or 0
        completion += getattr(usage, "completion_tokens", 0) or 0
    if not seen:
        return None, None, None
    return prompt, completion, prompt + completion


def final_text(messages):
    for m in reversed(messages):
        content = getattr(m, "content", None)
        if isinstance(content, str) and content.strip():
            return content
    return ""


def fmt_tokens(v):
    return f"{v:,}" if isinstance(v, int) else "null"


# --- R7: the comparison table ----------------------------------------
def print_comparison(autogen_m):
    # TODO (3/3): load lab2_metrics.json (catch FileNotFoundError / JSONDecodeError).
    #   - print a side-by-side table: Wall clock, Calls/messages, Total tokens,
    #     Handoff (explicit context vs shared history), Termination.
    #   - if lab2_metrics.json is missing, print the AutoGen column only with "—"
    #     in the CrewAI column and a note to run Lab 2 first.
    #   - print the three reflection questions from the spec.
    #   - write the merged dict {"crewai": <lab2 or None>, "autogen": autogen_m}
    #     to framework_comparison.json with indent=2.
    raise NotImplementedError


def warn_unbounded():
    bar = "!" * 66
    print(f"\n{bar}")
    print(" UNBOUNDED RUN — the critic will not say APPROVED and there is no")
    print(" message ceiling. Press Ctrl-C after about 30 seconds.")
    print(" THIS RUN IS BILLED: every turn is a real model call.")
    print(f"{bar}\n")


class _Counter:
    n = 0


async def _counted(stream, counter):
    async for event in stream:
        counter.n += 1
        yield event


async def main():
    topic = load_topic()
    model_client = OpenAIChatCompletionClient(model=MODEL)
    try:
        team = build_team(build_agents(model_client))
        task = (
            f"Produce an APPROVED 200-word brief on: {topic}\n"
            "researcher: gather findings with sources. summarizer: write the "
            "brief from those findings only. critic: check every claim against "
            "the findings and reply APPROVED when the brief is clean."
        )

        if UNBOUNDED:
            warn_unbounded()

        counter = _Counter()
        start = time.perf_counter()
        try:
            result = await Console(_counted(team.run_stream(task=task), counter))
        except KeyboardInterrupt:
            elapsed = time.perf_counter() - start
            print(f"\n[stopped] Ctrl-C after {elapsed:.1f} s and ~{counter.n} "
                  "messages. No reachable termination condition — FM-3.")
            return
        wall = time.perf_counter() - start

        messages = result.messages
        p_tok, c_tok, t_tok = sum_tokens(messages)
        if t_tok is None:
            print("[tokens] models_usage not present — token fields written null.")

        metrics = {
            "framework": "autogen",
            "topic": topic,
            "wall_clock_seconds": round(wall, 1),
            "model": MODEL,
            "agents": 3,
            "messages": len(messages),
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": t_tok,
            "estimated_cost_inr": None,
            "flags": {"unbounded": UNBOUNDED},
            "final_output": final_text(messages),
        }
        with open("lab3_metrics.json", "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)

        print_comparison(metrics)
    finally:
        await model_client.close()  # always close the client, even on error


# Async entry point — the first async code in the programme.
asyncio.run(main())
