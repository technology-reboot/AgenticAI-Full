# Lab 1 — Single Agent: Travel Planner with a Live Weather Tool

**Framework:** LangChain (`langchain.agents.create_agent`)
**You will write:** the whole script, from these instructions only. No source file to peek at.

## Learning objective

Build a single tool-calling agent and observe, by reading its trace, *when* it
decides to call a tool versus answer directly — and what happens when the
tool is broken.

## Setup (given, not an exercise)

- `.env` with `OPENAI_API_KEY` and `OPENWEATHER_API_KEY`.
- Load env vars at the top of the script; fail fast with a clear message if
  either is missing.
- A module-level flag `BREAK_TOOL = False` that you will flip to `True` later
  to simulate an outage.

## Part A — The weather tool

Design a tool function `get_weather(city)` that an LLM agent can call.

Requirements:
1. It must be decorated/registered as a tool for your framework (LangChain:
   `@tool` from `langchain_core.tools`).
2. **The docstring is not for you — it is the contract the model reads to
   decide when to call this tool and what argument to pass.** Write it so the
   model understands: what the tool does, *when* it should be called (before
   packing/timing advice that depends on current conditions), what the `city`
   argument should look like (plain name, e.g. "Pune"), and what shape the
   return value has.

Pseudocode for the body:

```
FUNCTION get_weather(city) -> string:
    IF BREAK_TOOL is True:
        RAISE a runtime error explaining the weather service is unavailable
        # do NOT catch this yourself — let it propagate up to the agent

    TRY:
        response = HTTP GET "https://api.openweathermap.org/data/2.5/weather"
            with query params: q=city, units="metric", appid=OPENWEATHER_API_KEY
            with timeout = 10 seconds
    CATCH any network/request exception AS exc:
        RETURN "Weather lookup failed for {city}: {exc}"   # return, don't raise

    IF response.status_code != 200:
        reason = response.json()["message"] IF present ELSE response.reason
        RETURN "Weather lookup failed for {city}: {reason}"

    data = response.json()
    description = data.weather[0].description
    temp        = data.main.temp
    feels_like  = data.main.feels_like
    RETURN "{description}, {temp formatted to 1 decimal}C, feels like {feels_like formatted to 1 decimal}C"
```

Design note: a **network failure** or **non-200 response** is handled
gracefully (returned as text so the agent can talk about it), but the
`BREAK_TOOL` simulated outage is left to **raise**, on purpose — that's the
scenario you're building toward in Part D.

## Part B — The agent

1. Write a `SYSTEM_PROMPT` string that instructs the assistant to: help plan
   short trips; check current weather with the tool *before* giving
   packing/timing advice; answer directly (no tool) for questions that don't
   depend on current conditions.
2. Build the agent using `create_agent(...)` from `langchain.agents` with:
   - a chat model (`ChatOpenAI`, model `"gpt-4o-mini"`, `temperature=0`)
   - `tools=[get_weather]`
   - `system_prompt=SYSTEM_PROMPT`

   Do **not** use `create_react_agent`, `AgentExecutor`, or
   `initialize_agent` — this course uses the newer `create_agent` API.

## Part C — Reading the trace

Agent frameworks return a list of messages. Write `print_trace(messages)` so
a human can scan a run in a few seconds:

```
FUNCTION print_trace(messages):
    PRINT "--- trace ---"
    FOR EACH msg IN messages:
        SWITCH msg.type:
            CASE "human":
                PRINT "[human]  " + one_line(msg.content)
            CASE "ai":
                FOR EACH call IN msg.tool_calls:
                    PRINT "[ai]     -> tool_call: {call.name}({call.args})"
                IF msg.content is non-empty:
                    PRINT "[ai]     " + one_line(msg.content)
            CASE "tool":
                PRINT '[tool]   {msg.name} -> "' + one_line(msg.content, limit=80) + '"'
```

`one_line(text, limit=100)` is a small helper you also need to write:
collapse all whitespace/newlines in `text` to single spaces, and if the
result is longer than `limit`, truncate it and append an ellipsis.

## Part D — Running scenarios

Write `run_scenario(banner, question)` that: prints a banner, invokes the
agent with the question as a single human message, calls `print_trace`,
prints the final answer (the last message's content), and prints a count of
how many tool calls happened across the whole run (sum of `len(tool_calls)`
over every AI message).

Then write `main()` that runs, **in this order**:

1. **Scenario 1 — needs the tool**: *"Should I pack a raincoat for Pune this
   week?"* — expect a `get_weather` call before the answer.
2. **Scenario 2 — doesn't need the tool**: *"What is a good time of year to
   visit Goa?"* — expect **no** tool call. If your agent calls the tool here,
   your system prompt is over-instructing it — that's worth noting.
3. **Scenario 3 — the tool is deliberately broken.** Set `BREAK_TOOL = True`,
   then re-run the *same* raincoat question from Scenario 1.

## What to observe and record (Scenario 3)

Watch the trace and the final answer for the broken-tool run, and write down
**one observation**: does the agent retry the tool, does it honestly report
the failure to the user, or does it answer from its own general knowledge as
if the tool had actually returned data? Keep this note — it's the seed for a
later discussion on how agents should handle tool failure as a fact rather
than hide it.

## Acceptance checklist

- [ ] Missing `OPENAI_API_KEY` or `OPENWEATHER_API_KEY` fails immediately with a clear message, not a stack trace deep in the framework.
- [ ] Scenario 1 shows a `get_weather` tool call in the trace.
- [ ] Scenario 2 shows **zero** tool calls.
- [ ] Scenario 3 raises inside the tool but the run still completes and prints something — not an unhandled crash of your whole script.
- [ ] You have a one-sentence observation written down for Scenario 3.
