# Lab 3 — The same task in AutoGen, then compare
#
# PROJECT STATUS: AutoGen entered maintenance mode in October 2025 (bug and
# security fixes only, community-managed). Its successors are Microsoft Agent
# Framework 1.0 (GA April 2026, merging AutoGen with Semantic Kernel) and the
# community fork AG2. This lab teaches the conversational pattern, which
# transfers to both — it is not a live recommendation of autogen-agentchat.
#
# Instructor notes: run the default path first, THEN the unbounded run (it is
# billed — stop it after ~30 s). AutoGen using more tokens than CrewAI here is
# the structural point (every agent sees the full history each turn), not a bug.

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

# Same model as Lab 2 — the comparison is only meaningful with the model held constant.
MODEL = "gpt-4o-mini"
DEFAULT_TOPIC = "India's DPDP Act obligations for AI systems handling customer data"

UNBOUNDED = False  # set True to remove MaxMessageTermination — Ctrl-C to stop


# R1 — search tool. AutoGen wraps this plain async function automatically.
async def search_web(query: str) -> str:
    """Search the web for `query`; return the top 3-5 results as text, each with
    a title, snippet and URL. Call this before making any factual claim."""
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
    return "\n".join(f"- {h.get('title','')}: {h.get('body','')[:200]} "
                     f"({h.get('href','')})" for h in hits)

# R4 — reuse Lab 2's topic so the comparison is like-for-like.
def load_topic():
    try:
        with open("lab2_metrics.json", encoding="utf-8") as fh:
            topic = json.load(fh).get("topic")
        if topic:
            return topic
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    print("[warn] lab2_metrics.json not found — using default topic; "
          "the comparison will be approximate.")
    return DEFAULT_TOPIC

# R2 — three agents; each system_message carries the same intent as its Lab 2 agent.
def build_agents(model_client):
    researcher = AssistantAgent(  # mirrors Lab 2 "Research Analyst"
        "researcher", model_client=model_client, tools=[search_web],
        system_message="You are a research analyst. Find and cite source "
        "material on the topic. Never state a fact without a source URL; verify "
        "before you report. Then hand the findings to the summarizer.")
    summarizer = AssistantAgent(  # mirrors Lab 2 "Briefing Writer"
        "summarizer", model_client=model_client,
        system_message="You are a briefing writer. Turn the researcher's "
        "findings into a 200-word brief. Add nothing that is not in the findings.")
    critic_msg = ("You are a quality critic. Flag any claim in the brief not "
                  "present in the researcher's findings. When every claim is "
                  "supported, reply with exactly APPROVED.")
    if UNBOUNDED:  # weaken it so it will not say the magic word
        critic_msg = ("You are a relentless quality critic. Always demand at "
                      "least one further improvement. Never reply APPROVED.")
    critic = AssistantAgent("critic", model_client=model_client,
                            system_message=critic_msg)  # mirrors Lab 2 "Quality Critic"
    return [researcher, summarizer, critic]

# R3 — team + termination. TextMention is the INTENT; MaxMessage is the SAFETY
# NET. Shipping only the first is how you get an unbounded run (FM-3, no termination).
def build_team(agents):
    stop = TextMentionTermination("APPROVED")
    if not UNBOUNDED:
        stop = stop | MaxMessageTermination(12)
    return RoundRobinGroupChat(agents, termination_condition=stop)

# R6 — token usage from per-message models_usage; skip messages that carry none.
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
    return (prompt, completion, prompt + completion) if seen else (None, None, None)


def final_text(messages):
    for m in reversed(messages):
        c = getattr(m, "content", None)
        if isinstance(c, str) and c.strip():
            return c
    return ""

def fmt_tokens(v):
    return f"{v:,}" if isinstance(v, int) else "null"

# R7 — the comparison table is the actual deliverable of this lab.
def print_comparison(ag):
    try:
        with open("lab2_metrics.json", encoding="utf-8") as fh:
            cw = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        cw = None

    bar = "=" * 66
    ag_wall, ag_msgs, ag_tok = (f"{ag['wall_clock_seconds']} s",
                                f"{ag['messages']} messages",
                                fmt_tokens(ag["total_tokens"]))

    def row(label, c, a):
        print(f" {label:<23}{c:<18}{a}")

    print(f"\n{bar}\n COMPARISON — same task, two frameworks\n{bar}")
    row("", "CrewAI", "AutoGen")
    if cw is None:
        print(" Run Lab 2 first for the CrewAI column.")
        row("Wall clock", "—", ag_wall)
        row("Messages", "—", ag_msgs)
        row("Total tokens", "—", ag_tok)
        merged = {"crewai": None, "autogen": ag}
    else:
        row("Wall clock", f"{cw['wall_clock_seconds']} s", ag_wall)
        row("Calls / messages", f"{cw['tasks']} tasks", ag_msgs)
        row("Total tokens", fmt_tokens(cw["total_tokens"]), ag_tok)
        row("Handoff", "explicit context", "shared history")
        row("Termination", "task list ends", "explicit condition")
        merged = {"crewai": cw, "autogen": ag}
    print(bar)
    print("\n Now answer, in your own words: (1) which output was better, and on"
          "\n what evidence?  (2) which was cheaper?  (3) which would you rather"
          "\n maintain in twelve months?")
    with open("framework_comparison.json", "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2)
    print("\n Merged figures written to framework_comparison.json")

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
        task = (f"Produce an APPROVED 200-word brief on: {topic}\n"
                "researcher: gather findings with sources. summarizer: write the "
                "brief from those findings only. critic: check every claim "
                "against the findings and reply APPROVED when the brief is clean.")
        if UNBOUNDED:
            b = "!" * 66
            print(f"\n{b}\n UNBOUNDED RUN — the critic will not say APPROVED and "
                  f"there is no message\n ceiling. Press Ctrl-C after ~30 seconds. "
                  f"THIS RUN IS BILLED.\n{b}\n")

        counter, start = _Counter(), time.perf_counter()
        try:
            result = await Console(_counted(team.run_stream(task=task), counter))
        except KeyboardInterrupt:
            print(f"\n[stopped] Ctrl-C after {time.perf_counter()-start:.1f} s "
                  f"and ~{counter.n} messages. No reachable termination "
                  "condition — FM-3 (no termination).")
            return
        wall = time.perf_counter() - start
        messages = result.messages
        p_tok, c_tok, t_tok = sum_tokens(messages)
        if t_tok is None:
            print("[tokens] models_usage not present — token fields written null.")

        metrics = {
            "framework": "autogen", "topic": topic,
            "wall_clock_seconds": round(wall, 1), "model": MODEL, "agents": 3,
            "messages": len(messages), "prompt_tokens": p_tok,
            "completion_tokens": c_tok, "total_tokens": t_tok,
            "estimated_cost_inr": None, "flags": {"unbounded": UNBOUNDED},
            "final_output": final_text(messages),
        }
        with open("lab3_metrics.json", "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)
        print_comparison(metrics)
    finally:
        await model_client.close()  # always close the client, even on error


# Async entry point — the first async code in the programme.
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n[stopped] Interrupted.")
