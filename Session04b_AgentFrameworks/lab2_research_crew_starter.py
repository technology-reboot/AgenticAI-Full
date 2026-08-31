# Lab 2 — Build the Researcher–Summarizer–Critic crew (CrewAI)  (STARTER)
#
# Fill in the three TODO blocks: the agents, the tasks, and the metrics block.
# The search tool, the crew wiring and the break-hint output are done for you.
#
# Instructor notes:
# - Run the normal path first, then BREAK_CONTEXT = True, and put both briefs
#   side by side on screen. The difference is the lesson.
# - Keep lab2_metrics.json — Lab 3 reads it to build the comparison.
# - Expected wall clock is 30–60 s. Over 3 minutes means an agent is looping.

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


# --- R1: search tool with a graceful fallback (done for you) -----------------
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


# --- R2: three agents -------------------------------------------------------
critic_goal = (
    "Check the brief's tone is professional"
    if WEAK_CRITIC
    else "Flag any claim in the brief that is not supported by the findings"
)

# TODO (1/3): build three Agent objects — researcher, summarizer, critic.
#   researcher : role="Research Analyst",  goal about finding+citing sources on
#                TOPIC,  tools=[search_tool]
#   summarizer : role="Briefing Writer",   goal "Turn the researcher's findings
#                into a 200-word brief",   tools=[]
#   critic     : role="Quality Critic",    goal=critic_goal,   tools=[]
#   On every agent: a short backstory that shapes behaviour (researcher verifies
#   before reporting, summarizer never adds facts, critic is hard to satisfy),
#   llm=MODEL, max_iter=5, verbose=True.
researcher = None
summarizer = None
critic = None


# --- R3: three tasks with explicit context wiring -------------------------
# TODO (2/3): build three Task objects — find, write, check.
#   find  : agent=researcher,  no context,  expected_output = findings + sources
#   write : agent=summarizer,  context = [] if BREAK_CONTEXT else [find]
#           expected_output = "a 200-word brief with no invented facts"
#   check : agent=critic,      context = [find, write]   <-- seeing BOTH is what
#           lets the critic catch an unsupported claim; keep this comment
#           expected_output = "Either 'APPROVED' or a numbered revision list"
#   Use the {topic} placeholder in the find/write descriptions; it is filled by
#   crew.kickoff(inputs={"topic": TOPIC}).
find = None
write = None
check = None


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
    print(" findings. Without it, the write task sees only the topic string.")
    print(" Read both briefs and record what changed.")
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

    # TODO (3/3): metrics emission.
    #   - pull prompt/completion/total tokens from crew.usage_metrics if this
    #     crewai version exposes it; otherwise set all three to None and print a
    #     line telling the student to read tokens off the verbose output.
    #     DO NOT invent token numbers.
    #   - build the metrics dict with EXACTLY these keys: framework, topic,
    #     wall_clock_seconds (round 1dp), model, agents, tasks, prompt_tokens,
    #     completion_tokens, total_tokens, estimated_cost_inr (None),
    #     flags={"break_context":BREAK_CONTEXT,"weak_critic":WEAK_CRITIC},
    #     final_output=str(result)
    #   - json.dump it to lab2_metrics.json with indent=2
    #   - call print_summary(metrics) and print_break_hint()
    raise NotImplementedError


main()
