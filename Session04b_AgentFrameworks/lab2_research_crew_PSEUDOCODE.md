# Lab 2 — Researcher → Summarizer → Critic Crew (CrewAI)

**Framework:** CrewAI (`Agent`, `Task`, `Crew`, `Process`)
**You will write:** the whole script, from these instructions only.

## Learning objective

Wire three specialized agents into a sequential pipeline where later agents
receive earlier agents' output as explicit **context**, then measure what
breaks when that handoff is removed.

## Setup (given, not an exercise)

- `.env` with `OPENAI_API_KEY` (required); `SERPER_API_KEY` optional.
- `MODEL = "gpt-4o-mini"` — set explicitly on every agent, never rely on a
  framework default.
- `TOPIC = "India's DPDP Act obligations for AI systems handling customer data"`
- Two flags you'll use later: `BREAK_CONTEXT = False`, `WEAK_CRITIC = False`.

## Part A — Search tool with graceful fallback (given, read to understand the pattern)

You're given this behavior so you can *consume* the tool object — you don't
need to write it, but understand what it returns:

```
FUNCTION build_search_tool() -> (tool, backend_label):
    IF SERPER_API_KEY is set:
        RETURN SerperDevTool(), "SerperDevTool (SERPER_API_KEY found)"

    DEFINE a tool "Web Search" wrapping a function ddg_search(query):
        # docstring: search the web for `query`, return top results as text
        # each with title, short snippet (<=200 chars), and URL — used to
        # find source material
        results = DuckDuckGo text search for query, max 5 results
        IF no results: RETURN "No results."
        RETURN each result formatted as "- {title}: {snippet} ({url})", one per line

    RETURN ddg_search, "DuckDuckGo fallback (no SERPER_API_KEY)"
```

Call it once at module load: `search_tool, BACKEND = build_search_tool()` and
print which backend got picked — useful for debugging in class.

## Part B — Three agents (this is your exercise)

Build three `Agent` objects. On **every** agent set: `llm=MODEL`,
`max_iter=5` (guardrail — a runaway agent should not loop forever), and
`verbose=True`.

```
researcher = Agent(
    role  = "Research Analyst",
    goal  = "Find and cite source material on {TOPIC}",
    backstory = <write 1-2 sentences establishing: verifies every claim
                 against a source before reporting it; never presents an
                 unsourced statement as fact>,
    tools = [search_tool],
)

summarizer = Agent(
    role  = "Briefing Writer",
    goal  = "Turn the researcher's findings into a 200-word brief",
    backstory = <compresses findings into clear prose; never adds a fact
                 that isn't in the findings it was handed>,
    tools = [],
)

critic_goal = "Check the brief's tone is professional" IF WEAK_CRITIC
              ELSE "Flag any claim in the brief that is not supported by the findings"

critic = Agent(
    role  = "Quality Critic",
    goal  = critic_goal,
    backstory = <hard to satisfy; treats a claim as unsupported until it has
                 seen it in the findings>,
    tools = [],
)
```

Think about *why* the backstory text matters here as much as the goal: in
CrewAI both feed the agent's effective system prompt.

## Part C — Three tasks with explicit context wiring (this is your exercise)

```
find = Task(
    description     = "Research the topic: {topic}. Gather concrete findings
                        and list a supporting source URL for each.",
    expected_output = "A list of findings, each with its supporting source URL.",
    agent           = researcher,
    # no context — this is the first task
)

write = Task(
    description     = "Write a 200-word brief on {topic} using only the
                        researcher's findings. Do not introduce facts that
                        are not in the findings.",
    expected_output = "A brief of about 200 words with no invented facts.",
    agent           = summarizer,
    context         = [] IF BREAK_CONTEXT ELSE [find],
)

check = Task(
    description     = "Compare the brief against the findings. If every
                        claim is supported, reply with exactly APPROVED.
                        Otherwise reply with a numbered list of required
                        revisions.",
    expected_output = "Either 'APPROVED' or a numbered revision list.",
    agent           = critic,
    context         = [find, write],   # <- seeing BOTH is what lets the
                                        #    critic catch an invented claim
)
```

The `{topic}` placeholder in `find`/`write` descriptions gets filled at run
time via `crew.kickoff(inputs={"topic": TOPIC})` — don't hardcode `TOPIC`
into the description strings.

## Part D — Run the crew and emit metrics (this is your exercise)

```
FUNCTION main():
    crew = Crew(agents=[researcher, summarizer, critic],
                tasks=[find, write, check],
                process=Process.sequential,
                verbose=True)

    start = now()
    result = crew.kickoff(inputs={"topic": TOPIC})
    wall_clock_seconds = round(now() - start, 1)

    # Token usage: NOT every CrewAI version exposes this. Try to read
    # prompt_tokens / completion_tokens / total_tokens from crew.usage_metrics
    # (it may be a dict or an object — handle both). If it isn't available,
    # set all three to None and print a line telling the user to read token
    # counts off the verbose console output instead. Do NOT invent numbers.
    prompt_tokens, completion_tokens, total_tokens = read_tokens(crew)

    metrics = {
        "framework": "crewai",
        "topic": TOPIC,
        "wall_clock_seconds": wall_clock_seconds,
        "model": MODEL,
        "agents": 3,
        "tasks": 3,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_inr": None,
        "flags": {"break_context": BREAK_CONTEXT, "weak_critic": WEAK_CRITIC},
        "final_output": string(result),
    }
    WRITE metrics as JSON (indent=2) to "lab2_metrics.json"

    print_summary(metrics)   # given helper — prints a formatted run report
    print_break_hint()       # given helper — prints what to compare
```

**Important:** keep the exact key names above — `lab3` reads this file to
build a framework comparison, and a renamed key silently breaks that lab.

## Experiment — run it twice

1. Run once with `BREAK_CONTEXT = False`, `WEAK_CRITIC = False`. Read the
   brief.
2. Set `BREAK_CONTEXT = True`, run again. The `write` task now sees only the
   topic string, not the researcher's findings. Put both briefs side by side
   — record what changed.
3. Optionally set `WEAK_CRITIC = True` as well and note whether unsupported
   claims now survive that a fact-checking critic would have caught.

## Acceptance checklist

- [ ] Missing `OPENAI_API_KEY` fails immediately with a clear message.
- [ ] `[search backend]` line prints at startup showing which tool got picked.
- [ ] `lab2_metrics.json` is written after every run with the exact keys listed above.
- [ ] The `check` task's context includes **both** `find` and `write`, not just one.
- [ ] You've run the BREAK_CONTEXT experiment and can describe, in your own words, what changed in the brief.
- [ ] Total wall clock is roughly 30–60s; if it's over 3 minutes, an agent is looping — check `max_iter` is actually set to 5 on all three agents.
