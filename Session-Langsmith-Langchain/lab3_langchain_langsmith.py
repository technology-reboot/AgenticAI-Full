"""Training demo: LangChain orchestration with LangSmith tracing.

Set OPENAI_API_KEY and LANGSMITH_API_KEY before running this file. LangChain
runnables automatically send traces to LangSmith when LANGSMITH_TRACING=true.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI
from langsmith import traceable


BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "data" / "company_profiles" / "tcs.txt"


def load_company_context(_: str) -> str:
    """Load the local profile used by the company-question branch."""
    return PROFILE_PATH.read_text(encoding="utf-8")


def is_company_question(question: str) -> bool:
    """Route questions that can be answered from the local company profile."""
    company_terms = {"tcs", "tata", "consulting", "mumbai", "company"}
    return any(term in question.lower() for term in company_terms)


def build_chain():
    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    parser = StrOutputParser()

    company_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Answer using only the supplied context. If the context does not "
            "contain the answer, say you do not know.\n\nContext:\n{context}",
        ),
        ("human", "{question}"),
    ])
    general_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a concise and helpful assistant."),
        ("human", "{question}"),
    ])

    # RunnableParallel prepares inputs, then the prompt/model/parser stages run in order.
    company_chain = (
        RunnableParallel(
            context=RunnableLambda(load_company_context),
            question=RunnablePassthrough(),
        )
        | company_prompt
        | model
        | parser
    )
    general_chain = (
        RunnableParallel(question=RunnablePassthrough())
        | general_prompt
        | model
        | parser
    )

    return RunnableBranch(
        (is_company_question, company_chain),
        general_chain,
    ).with_config({"run_name": "support_router", "tags": ["llmops", "routing-demo"]})


@traceable(name="run_support_assistant", tags=["training-demo"])
def run_support_assistant(question: str) -> str:
    """Invoke the orchestrated chain inside a named LangSmith trace."""
    return build_chain().invoke(question)


def main():
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY before running this example.")

    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", "session-07-llmops")

    print("LangChain orchestration with LangSmith tracing")
    print(f"LangSmith project: {os.getenv('LANGSMITH_PROJECT')}")

    questions = [
        "Where is TCS headquartered?",
        "Give me one practical tip for improving a support assistant.",
    ]
    for question in questions:
        print(f"\nQuestion: {question}")
        print(f"Answer: {run_support_assistant(question)}")


if __name__ == "__main__":
    main()