# Lab 2 — Build the Researcher–Summarizer–Critic crew (CrewAI)
#
# Instructor notes:
# - Run the normal path first, then BREAK_CONTEXT = True, and put both briefs
#   side by side on screen. The difference is the lesson.
# - If a student's crew produces a good brief even with the context removed,
#   their topic is one the model already knows well. Suggest a more obscure or
#   more recent topic.
# - Keep lab2_metrics.json — Lab 3 reads it to build the comparison.
# - Expected wall clock is 30–60 s. Anything over 3 minutes means an agent is
#   looping; check max_iter.

import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("Missing OPENAI_API_KEY — add it to .env and re-run.")

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

MODEL = "gpt-4o-mini"  # set explicitly on every agent — never rely on the default
TOPIC = "India's DPDP Act obligations for AI systems handling customer data"

BREAK_CONTEXT = False  # set True to remove the handoff from the write task
WEAK_CRITIC = False    # set True to degrade the critic's goal to a tone check


# --- R1: search tool with a graceful fallback --------------------------------
def build_search_tool():
    """Return (tool, backend_label). SerperDevTool when SERPER_API_KEY is set,
    otherwise a DuckDuckGo-backed tool so the lab still runs with no Serper key."""
    if os.getenv("SERPER_API_KEY"):
        from crewai_tools import SerperDevTool
        return SerperDevTool(), "SerperDevTool (SERPER_API_KEY found)"

    @tool("Web Search")
    def ddg_search(query: str) -> str:
        """Search the web for `query`. Returns the top results as text, each with
        a title, a short snippet and a URL. Use this to find source material."""
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddg:
            hits = list(ddg.text(query, max_results=5))
        if not hits:
            return "No results."
        return "\n".join(
            f"- {h.get('title', '')}: {h.get('body', '')[:200]} ({h.get('href', '')})"
            for h in hits
        )

    return ddg_search, "DuckDuckGo fallback (no SERPER_API_KEY)"


search_tool, BACKEND = build_search_tool()
print(f"[search backend] {BACKEND}")


# --- R2: three agents (max_iter=5 is the guardrail the module insists on) -----
critic_goal = ("Check the brief's tone is professional" if WEAK_CRITIC
               else "Flag any claim in the brief that is not supported by the findings")

researcher = Agent(
    role="Research Analyst", goal=f"Find and cite source material on {TOPIC}",
    backstory="You verify every claim against a source before you report it; "
              "you never present an unsourced statement as fact.",
    tools=[search_tool], llm=MODEL, max_iter=5, verbose=True,
)
summarizer = Agent(
    role="Briefing Writer", goal="Turn the researcher's findings into a 200-word brief",
    backstory="You compress findings into clear prose and never add a fact that "
              "is not in the findings you were handed.",
    tools=[], llm=MODEL, max_iter=5, verbose=True,
)
critic = Agent(
    role="Quality Critic", goal=critic_goal,
    backstory="You are hard to satisfy. You treat a claim as unsupported until "
              "you have seen it in the findings.",
    tools=[], llm=MODEL, max_iter=5, verbose=True,
)


# --- R3: three tasks with explicit context wiring -------------------------
find = Task(
    description="Research the topic: {topic}. Gather concrete findings and list "
                "a supporting source URL for each.",
    expected_output="A list of findings, each with its supporting source URL.",
    agent=researcher,
)

write = Task(
    description="Write a 200-word brief on {topic} using only the researcher's "
                "findings. Do not introduce facts that are not in the findings.",
    expected_output="A brief of about 200 words with no invented facts.",
    agent=summarizer,
    context=[] if BREAK_CONTEXT else [find],
)

# The check task sees BOTH `find` and `write`: comparing the draft against the
# findings is what lets the critic catch a claim the summarizer invented.
check = Task(
    description="Compare the brief against the findings. If every claim is "
                "supported, reply with exactly APPROVED. Otherwise reply with a "
                "numbered list of required revisions.",
    expected_output="Either 'APPROVED' or a numbered revision list.",
    agent=critic,
    context=[find, write],
)


# --- R7: metrics helpers -------------------------------------------------
def read_tokens(crew):
    um = getattr(crew, "usage_metrics", None)
    if um is None:
        return None, None, None
    get = um.get if isinstance(um, dict) else (lambda k: getattr(um, k, None))
    return get("prompt_tokens"), get("completion_tokens"), get("total_tokens")


def print_summary(m):
    tok = f"{m['total_tokens']:,}" if m["total_tokens"] is not None \
        else "read from verbose output above"
    bar = "=" * 66
    print(f"\n{bar}\n RUN SUMMARY — CrewAI\n{bar}")
    print(f" Topic              : {m['topic']}")
    print(f" Wall clock         : {m['wall_clock_seconds']} s")
    print(f" Agents / tasks     : {m['agents']} / {m['tasks']}")
    print(f" Tokens             : {tok}")
    print(f" Flags              : break_context={BREAK_CONTEXT}  "
          f"weak_critic={WEAK_CRITIC}")
    print(f" Metrics written to : lab2_metrics.json\n{bar}")


def print_break_hint():
    bar = "=" * 66
    print(f"\n{bar}\n WHAT TO COMPARE\n{bar}")
    print(" Run once with BREAK_CONTEXT = False, then once with True.")
    print(" With the handoff, the brief is built from the researcher's actual")
    print(" findings and their sources. Without it, the write task sees only the")
    print(" topic string. Read both briefs and record what changed.")
    if WEAK_CRITIC:
        print(" WEAK_CRITIC is on: the critic only checks tone now — note whether")
        print(" unsupported claims survive that a fact-checking critic would flag.")
    print(bar)


# --- R4 + R7: run the crew and emit metrics ------------------------------
def main():
    crew = Crew(
        agents=[researcher, summarizer, critic],
        tasks=[find, write, check],
        process=Process.sequential,
        verbose=True,
    )

    start = time.perf_counter()
    result = crew.kickoff(inputs={"topic": TOPIC})
    wall = time.perf_counter() - start

    prompt_tokens, completion_tokens, total_tokens = read_tokens(crew)
    if total_tokens is None:
        print("\n[tokens] This CrewAI version does not expose usage_metrics — "
              "read the token counts off the verbose output above.")

    metrics = {
        "framework": "crewai",
        "topic": TOPIC,
        "wall_clock_seconds": round(wall, 1),
        "model": MODEL,
        "agents": 3,
        "tasks": 3,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_inr": None,
        "flags": {"break_context": BREAK_CONTEXT, "weak_critic": WEAK_CRITIC},
        "final_output": str(result),
    }
    with open("lab2_metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print_summary(metrics)
    print_break_hint()


main()
