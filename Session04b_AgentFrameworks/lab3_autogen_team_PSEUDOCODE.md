# Lab 3 — The Same Task in AutoGen, Then Compare

**Framework:** AutoGen (`autogen-agentchat`, `RoundRobinGroupChat`)
**Prerequisite:** run Lab 2 first — this lab reads `lab2_metrics.json` to
build the comparison. If you skip it, this lab still runs, just with an
approximate topic and no CrewAI column.
**You will write:** the whole script, from these instructions only.

## Project status (context, not an exercise)

AutoGen entered maintenance mode in October 2025 (bug/security fixes only,
community-managed). Its successors are Microsoft Agent Framework 1.0 (GA
April 2026, merging AutoGen with Semantic Kernel) and the community fork
AG2. This lab teaches the *conversational* multi-agent pattern, which
transfers to both — treat it as a pattern lesson, not a live product
recommendation.

## Learning objective

Build the *same* Researcher → Summarizer → Critic task as Lab 2, but as a
free-running conversation instead of a fixed task pipeline, then compare
cost/behavior between the two architectures.

## Setup (given, not an exercise)

- `.env` with `OPENAI_API_KEY`.
- `MODEL = "gpt-4o-mini"` — same model as Lab 2; the comparison is only
  meaningful with the model held constant.
- `DEFAULT_TOPIC` — same string as Lab 2's `TOPIC`, used only as a fallback.
- `UNBOUNDED = False` — a flag you'll flip later to remove the safety net.

## Part A — Load the topic from Lab 2 (this is your exercise)

```
FUNCTION load_topic() -> string:
    TRY:
        OPEN "lab2_metrics.json", read JSON, get "topic" field
        IF topic is present: RETURN it
    CATCH file-not-found OR invalid-json:
        pass
    PRINT a warning that lab2_metrics.json was not found, using the default
          topic, and the comparison will be approximate
    RETURN DEFAULT_TOPIC
```

## Part B — Search tool (given, read to understand — it's the async twin of Lab 2's tool)

```
ASYNC FUNCTION search_web(query) -> string:
    # docstring: search the web for `query`, return top 3-5 results as text,
    # each with title, snippet, URL. Call this before making any factual claim.
    run the DuckDuckGo search in a background thread (it's a blocking call)
    IF no results: RETURN "No results."
    RETURN each result formatted as "- {title}: {snippet} ({url})", one per line
```

AutoGen wraps a plain async function as a tool automatically — you don't
need a decorator here the way CrewAI needed `@tool`.

## Part C — Three agents (this is your exercise)

Build three `AssistantAgent` instances. Each `system_message` should carry
the **same intent** as its Lab 2 CrewAI counterpart — add a one-line comment
next to each naming which Lab 2 agent it mirrors, so the parallel is obvious
when you diff the two labs later.

```
researcher = AssistantAgent("researcher", model_client=model_client,
    tools=[search_web],
    system_message = <mirrors Lab 2 "Research Analyst": find and cite source
                       material on the topic; never state a fact without a
                       source URL; verify before reporting; then hand
                       findings to the summarizer>)

summarizer = AssistantAgent("summarizer", model_client=model_client,
    system_message = <mirrors Lab 2 "Briefing Writer": turn the researcher's
                       findings into a 200-word brief; add nothing that is
                       not in the findings>)

critic_message = <mirrors Lab 2 "Quality Critic": flag any claim in the
                   brief not present in the researcher's findings; when
                   every claim is supported, reply with exactly APPROVED>

IF UNBOUNDED:
    # weaken it on purpose so it will never say the magic word — this is
    # what you'll use to demonstrate an unbounded run in Part F
    critic_message = <a relentless critic that always demands one more
                       improvement and never replies APPROVED>

critic = AssistantAgent("critic", model_client=model_client,
                         system_message=critic_message)

RETURN [researcher, summarizer, critic]
```

## Part D — Team and termination (this is your exercise)

```
FUNCTION build_team(agents) -> team:
    stop = TextMentionTermination("APPROVED")
    IF NOT UNBOUNDED:
        stop = stop OR MaxMessageTermination(12)
    RETURN RoundRobinGroupChat(agents, termination_condition=stop)
```

Understand the design intent here: `TextMentionTermination("APPROVED")` is
the **intent** (stop when the critic is satisfied); `MaxMessageTermination`
is the **safety net** (stop regardless, after 12 messages). Shipping only
the first is exactly how you get a run with no reachable termination
condition — which is what `UNBOUNDED = True` deliberately simulates.

## Part E — Metrics and comparison (this is your exercise)

Token accounting differs from Lab 2: AutoGen exposes usage per-message, not
per-crew.

```
FUNCTION sum_tokens(messages) -> (prompt, completion, total) or (None, None, None):
    prompt = completion = 0
    seen_any = False
    FOR EACH message IN messages:
        usage = message.models_usage  # may be absent
        IF usage is missing: CONTINUE
        seen_any = True
        prompt     += usage.prompt_tokens (or 0 if missing)
        completion += usage.completion_tokens (or 0 if missing)
    IF NOT seen_any: RETURN (None, None, None)
    RETURN (prompt, completion, prompt + completion)

FUNCTION final_text(messages) -> string:
    scan messages in REVERSE order
    RETURN the content of the first one whose content is a non-empty string
    (fallback: empty string if none found)
```

Then `print_comparison(autogen_metrics)`:

```
FUNCTION print_comparison(ag):
    TRY: load lab2_metrics.json into cw
    CATCH file-not-found OR invalid-json: cw = None

    PRINT a side-by-side table with columns "CrewAI" and "AutoGen":
        Wall clock
        Calls/messages          (CrewAI: task count · AutoGen: message count)
        Total tokens
        Handoff                 (CrewAI: "explicit context" · AutoGen: "shared history")
        Termination              (CrewAI: "task list ends" · AutoGen: "explicit condition")
    IF cw is None:
        show "—" in the CrewAI column instead, and print a note to run Lab 2 first

    PRINT three reflection questions (see below)

    WRITE {"crewai": cw, "autogen": ag} as JSON (indent=2) to "framework_comparison.json"
```

Reflection questions to print and then actually answer in your own words:
1. Which output was better, and on what evidence?
2. Which was cheaper?
3. Which would you rather maintain in twelve months?

## Part F — Main flow (this is your exercise)

```
ASYNC FUNCTION main():
    topic = load_topic()
    model_client = OpenAIChatCompletionClient(model=MODEL)
    TRY:
        team = build_team(build_agents(model_client))
        task_prompt = "Produce an APPROVED 200-word brief on: {topic}\n
                       researcher: gather findings with sources. summarizer:
                       write the brief from those findings only. critic:
                       check every claim against the findings and reply
                       APPROVED when the brief is clean."

        IF UNBOUNDED:
            PRINT a loud warning: this run has no message ceiling, it is
                  billed per turn, press Ctrl-C after ~30 seconds

        start = now()
        TRY:
            stream the team's run to the console, counting messages as they arrive
        CATCH KeyboardInterrupt:
            PRINT how long it ran and how many messages were seen before you
                  stopped it; note that there was no reachable termination
                  condition
            RETURN early

        wall_clock_seconds = round(now() - start, 1)
        messages = result.messages
        prompt_tokens, completion_tokens, total_tokens = sum_tokens(messages)
        IF total_tokens is None:
            PRINT a note that models_usage wasn't present, token fields will be null

        metrics = {
            "framework": "autogen", "topic": topic,
            "wall_clock_seconds": wall_clock_seconds, "model": MODEL, "agents": 3,
            "messages": len(messages),
            "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_inr": None,
            "flags": {"unbounded": UNBOUNDED},
            "final_output": final_text(messages),
        }
        WRITE metrics as JSON (indent=2) to "lab3_metrics.json"
        print_comparison(metrics)
    FINALLY:
        ALWAYS close model_client, even if an error or KeyboardInterrupt occurred
```

Run this with `asyncio.run(main())` as the script's entry point, and handle
a top-level `KeyboardInterrupt` gracefully (print a short "stopped" message
instead of a raw traceback).

## Experiment — run it twice

1. Run once with `UNBOUNDED = False`. Confirm it terminates and produces a
   comparison table against Lab 2.
2. Set `UNBOUNDED = True`, run again, and press **Ctrl-C after about 30
   seconds** — this run is billed per turn, don't let it run unattended.
   Watch the critic never say APPROVED and the message count climb with no
   ceiling.
3. Compare token totals between CrewAI (Lab 2) and AutoGen (Lab 3) for the
   *same* topic and model. AutoGen using noticeably more tokens is expected
   and structural — every agent sees the full shared conversation history on
   every turn, unlike CrewAI's explicit per-task context — not a sign
   something is broken.

## Acceptance checklist

- [ ] Missing `OPENAI_API_KEY` fails immediately with a clear message.
- [ ] With `UNBOUNDED = False`, the run terminates on its own (either APPROVED or the 12-message cap) without you pressing Ctrl-C.
- [ ] `lab3_metrics.json` and `framework_comparison.json` are both written after a normal run.
- [ ] The comparison table shows real numbers in the CrewAI column when `lab2_metrics.json` exists, and gracefully shows `—` when it doesn't.
- [ ] You've done the `UNBOUNDED = True` run under supervision, stopped it yourself, and can explain in one sentence why it never terminated on its own.
- [ ] You have written answers (not just printed questions) to the three reflection questions.
