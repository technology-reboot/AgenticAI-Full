from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()

GENERATOR_MODEL = "gpt-4o"
GRADER_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 4

grader_llm = ChatOpenAI(model_name=GRADER_MODEL, temperature=0)
generator_llm = ChatOpenAI(model_name=GENERATOR_MODEL, temperature=0)

CORPUS_PATH = Path(__file__).resolve().parent / "data"/"lab1_corpus.json"

def load_corpus() -> list[dict[str,str]]:
    if not CORPUS_PATH.exists():
        sys.exit(f"Corpus file not found: expected at {CORPUS_PATH}")
    entries=json.loads(CORPUS_PATH.read_text(encoding="utf-8"))    
    for entry in entries:
        entry["text"] = " ".join(entry["text"].split())
    return entries

CORPUS:list[dict[str,str]] = load_corpus()

def build_vectorstore() -> FAISS:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, 
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )

    docs: list[Document] = []
    for entry in CORPUS:
        clean = textwrap.dedent(entry["text"]).strip()
        for chunk in splitter.split_text(clean):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"doc_id": entry["id"], "title": entry["title"]},
                )
            )

    print(f"Indexed {len(docs)} document chunks from {len(CORPUS)} documents.")
    return FAISS.from_documents(
        documents=docs,
        embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )

BASIC_RAG_PROMPT = """You are Meridian's internal policy assistant. Answer the following questions using the context below

Context: {context}

Question: {question}
Answer:"""

def basic_rag(store: FAISS, question: str)-> tuple[str, list[dict[Document]]]:

    docs = store.similarity_search(question, k=TOP_K)
    context = "\n\n".join(
        f"[{doc.metadata['doc_id']} - {doc.metadata['title']}\n {doc.page_content}]" for doc in docs
    )
    prompt = BASIC_RAG_PROMPT.format(context=context, question=question)
    answer = generator_llm.invoke(prompt).content
    return answer, docs


class RelevanceGrade(BaseModel):
    """Structured verdict from the retrieval evaluator"""
    score: Literal["relevant", "ambiguous", "irrelevant"] = Field(
        description=(
        "'relevant' if the document contains information that directly "
            "helps answer the question. 'ambiguous' if it is on a related "
            "topic but does not contain the answer. 'irrelevant' if it is "
            "about something else entirely."
        )
    )

    reason: str = Field(description="Once short sentence justifying the score")

grader = grader_llm.with_structured_output(RelevanceGrade)

GRADER_PROMPT = """You are grading whether a retrieved document is useful for \
answering a user's question.

Be strict. A document that merely shares vocabulary with the question is not
relevant. A document is only 'relevant' if a careful reader could extract part
of the answer from it.

Question: {question}

Document:
{document}
"""

def grade_document(question: str, doc: Document) -> RelevanceGrade:
    """One LLM Call - the retrieval evaluatior"""
    return grader.invoke(GRADER_PROMPT.format(question=question, document=doc.page_content))


REFINE_PROMPT = """Extract only the sentences from the document below that help \
answer the question. Copy them verbatim. Drop everything else. If nothing in the
document helps, reply with exactly: NONE

Question: {question}

Document:
{document}
"""

def refine_document(question: str, doc: Document) -> str:

    result = grader_llm.invoke(REFINE_PROMPT.format(question=question, document=doc.page_content)).content
    return "" if result.strip().upper().startswith("NONE") else result.strip()

REWRITE_PROMPT = """Rewrite the user's question as a short, keyword-style web \
search query. Strip any company-internal names that a public search engine would
not know. Return only the query, nothing else.

Question: {question}
"""

def rewrite_for_web(question: str) -> str:
    """One LLM call - rewrite the question for a web search"""
    return generator_llm.invoke(REWRITE_PROMPT.format(question=question)).content.strip().strip('"')


def web_search(query: str, max_results: int = 4) -> str:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
        if not hits:
            return "No Web results found. The external search returned nothing"    

        return "n\n".join(
            f"[{hit['title',""]}\n{hit['body','']}\n{hit['href' '']}]" for hit in hits
        )
    except Exception as e:
        return f"Web search failed: {e}"


CRAG_PROMPT = """You are Meridian's internal policy assistant.

Answer the question using the knowledge below. The knowledge is labelled by
source. Internal policy is authoritative for Meridian's own rules; web results
are supporting context only and may be out of date.

If the knowledge does not contain the answer, say so plainly. Do not guess, and
do not fill gaps from your own training data.

Knowledge:
{knowledge}

Question: {question}

Answer:"""


def crag(store: FAISS, question: str) -> str:

    docs = store.similarity_search(question, k=TOP_K)
    print(f" retrievd {len(docs)} chunks")

    grades = []
    for doc in docs:
        g = grade_document(question, doc)
        grades.append((doc,g))
        print(f"  {doc.metadata['doc_id']:<8} {g.score:<11} {g.reason}")

    relevant = [d for d, g in grades if g.score == "relevant"]
    irrelevant = [d for d, g in grades if g.score == "irrelevant"]

    if relevant and not irrelevant:
        action = "CORRECT"
    elif not relevant:
        action = "INCORRECT"
    else:
        action = "AMBIGUOUS"

    print(f"\n ACTION: {action}")

    knowledge_parts: list[str] = []

    if action in ("CORRECT", "AMBIGUOUS"):
        print(f" refining {len(relevant)} relevant documents(s)...")
        for doc in relevant:
            strips = refine_document(question, doc)
            if strips:
                knowledge_parts.append(
                    f"[internal policy {doc.metadata['doc_id']} - {doc.metadata['title']}]\n{strips}"
                )

    if action in ("INCORRECT", "AMBIGUOUS"):
        query = rewrite_for_web(question)
        print(f" web query: {query}")
        knowledge_parts.append(web_search(query))

    knowledge = "\n\n".join(knowledge_parts) if knowledge_parts else "No relevant knowledge found."

    return generator_llm.invoke(CRAG_PROMPT.format(knowledge=knowledge, question=question)).content


QUESTIONS = [
    (
        "Q2",
        "How does Meridian's maternity leave compare with the statutory "
        "minimum required under Indian law?",
        "Half in the corpus, half not. Expect AMBIGUOUS: the internal policy "
        "is retrievable, the statutory minimum is not. Watch what basic RAG "
        "does with the half it cannot find.",
    ),
    (
        "Q3",
        "What do the RBI's digital lending guidelines require regarding "
        "loan disbursal to borrower bank accounts?",
        "Nothing in the corpus touches this. Expect INCORRECT — retrieval is "
        "discarded entirely. This is where basic RAG is at its most dangerous, "
        "because it will still return four confident-looking policy chunks.",
    ),
]



def main() -> None:
    print("Building vector store...")
    store = build_vectorstore()
    print("Vector store built.")

    basic_answer, basic_docs = basic_rag(store, "What do the RBI's digital lending guidelines require regarding loan disbursal to borrower bank accounts?") 
    print(f"Answer: {basic_answer}")
    print(f"Sources: {basic_docs}")

    print("Corective RAG")
    crag_answer = crag(store, "What do the RBI's digital lending guidelines require regarding loan disbursal to borrower bank accounts?")
    print("\n" + textwrap.indent(textwrap.fill(crag_answer, width=80), prefix='| '))



if __name__ == "__main__":
    main()