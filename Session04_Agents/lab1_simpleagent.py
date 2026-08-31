# Let's import "os" module, which stands for "Operating System"
# The os module in Python provides a way to interact with the operating system for things like:
# (1) accessing Environment Variables
# (2) Creating, renaming, and deleting files/folders.
import os
import sys
import asyncio

# The agent's responses contain emoji (✅, ❌, 🤖). On Windows the default
# console encoding (cp1252) can't print those, so force UTF-8 output.
_reconfigure = getattr(sys.stdout, "reconfigure", None)
if callable(_reconfigure):
    _reconfigure(encoding="utf-8")

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

# Import the Agent and Runner classes to create, manage, and run AI agents
from agents import Agent, Runner

# Define the instructions for the fact-checker AI Agent
fact_checker_instructions = """
Context:
You are a fact-validator who validates the accuracy of statements.

Instructions:
When given a statement, carefully analyze its factual accuracy using your knowledge.

Input:
You will receive a statement that requires fact-validation.

Output:
Respond with:
1. A verdict prefix: either "✅ TRUE:" or "❌ FALSE:"
2. A brief, one-sentence explanation justifying your conclusion
"""

# Create a new agent called "Fact Validator"
fact_validator_agent = Agent(name = "Fact Validator",   # Name of the agent
                           instructions = fact_checker_instructions, # The rules and behavior for the agent
                           model = "gpt-4o-mini") # The AI model (LLM) to use

# Print a confirmation message that the agent was created
print(f"Agent '{fact_validator_agent.name}' created successfully!")


# Define an async function to run the agent
async def main():
    # A statement we want the Fact Validator agent to verify
    statement = "India is world's largest democracy"

    # Display the statement we're going to check
    print(f"Asking the Fact Validator to verify: '{statement}'")

    # Run the Fact Validator agent on the input statement
    # 'await' is used because running the agent is an asynchronous operation (it might take time)
    response = await Runner.run(
        starting_agent = fact_validator_agent,  # The agent we created earlier
        input = statement                 # The statement we want it to fact-validate
    )

    # Display the agent's response
    print("\n🤖 Agent's Response:\n")
    print(response.final_output)    # Shows the final verdict and explanation


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
