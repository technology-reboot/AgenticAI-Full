# Let's import "os" module, which stands for "Operating System"
# The os module in Python provides a way to interact with the operating system for things like:
# (1) accessing Environment Variables
# (2) Creating, renaming, and deleting files/folders.
import os
import asyncio


# This will be used to load the API key from the .env file
from dotenv import load_dotenv
load_dotenv()

# Get the OpenAI API key from environment variables.
# The OpenAI Agents SDK automatically reads OPENAI_API_KEY from the environment,
# so we only need to make sure it is present.
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Add it to your .env file before running this script."
    )

print("OpenAI API key successfully loaded.")

# Let's view the first few characters in the key
print(openai_api_key[:5])

# Import the Agent and Runner classes to create, manage, and run AI agents.
# SQLiteSession gives the agent conversational memory backed by a SQLite database.
from agents import Agent, Runner, SQLiteSession

# Define the instructions for the fact-checker AI Agent
# Define the role and instructions for the AI agent
market_researcher_instructions = """
Context:
You are a market research assistant helping analyze companies, industries, and competitors.

Instructions:
When given a question, provide a short factual answer based on your knowledge.

Output:
Start with a verdict prefix: either "FACT:" or "UNKNOWN:"
Follow with a concise one-sentence explanation.
"""

# Create a session object that stores the conversation history.
# Passing an in-memory database (no file path) keeps history only for this run.
session = SQLiteSession("conversation")

# Create an instance of the Agent. The session is supplied to Runner.run(),
# not to the Agent constructor.
market_researcher_agent = Agent(name = "Market Researcher",
                                instructions = market_researcher_instructions,
                                model = "gpt-4.1-mini")

# Print a confirmation message that the agent was created
print(f"Agent '{market_researcher_agent.name}' created successfully!")


# Define an async function to run the agent
async def main():
    # Example: An AI Agent WITH memory (via the shared session)

    # Let's give our first question to the AI agent
    q1 = "What is the market share of Tesla in the US EV market?"

    # Display the user’s question
    print(f"You: '{q1}'")

    # Run the agent with the first question. Passing the session persists this
    # turn so later turns can refer back to it.
    resp1 = await Runner.run(
        starting_agent = market_researcher_agent,
        input = q1,
        session = session,
    )

    # Display the agent’s response
    print(f"Agent:\n{resp1.final_output}")

    q2 = "How does that compare to last year?"

    # Display the follow-up question
    print(f"\nYou: '{q2}'")

    # Run the agent again with the same session — it now recalls the first
    # question/answer and can resolve "that" from context.
    resp2 = await Runner.run(
        starting_agent = market_researcher_agent,
        input = q2,
        session = session,
    )

    # Display the agent’s response (should connect to the first question)
    print(f"Agent:\n{resp2.final_output}")


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
