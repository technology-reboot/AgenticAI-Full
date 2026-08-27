import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


RUN_ABLATION = True
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "it_companies"
REFUSAL = "I don't have that information."

GROUNDED_PROMPT = ChatPromptTemplate.from_template("""Answer the question using ONLY the information in the context below.

If the answer is not in the context, reply exactly:
"I don't have that information."

Answer in 2-3 sentences. Start by directly answering the question.
After your answer, add a line beginning "Source:" citing the part of the
context you used.

Context:
{context}

Question: {question}

Answer:
""")

# This prompt differs by one variable only: it removes ONLY and the refusal rule.
UNGROUNDED_PROMPT = ChatPromptTemplate.from_template("""Use the context below to help you answer the question.

Answer in 2-3 sentences. Start by directly answering the question.
After your answer, add a line beginning "Source:" citing the part of the
context you used.

Context:
{context}

Question: {question}

Answer:
""")


def require_api_key():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")


def format_docs(docs):
    # Without this, the prompt receives Document reprs; --- separates readable context chunks.
    return "\n\n---\n\n".join(document.page_content for document in docs)


def verify_store():
    if not Path(PERSIST_DIR).exists():
        raise SystemExit("Chroma store is missing; run lab1_vector_store.py first.")
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    if not any(getattr(item, "name", item) == COLLECTION_NAME for item in client.list_collections()):
        raise SystemExit("The it_companies collection is missing; run lab1_vector_store.py first.")


def show_retrieval(vectorstore, query):
    # This is a second retrieval call for display purposes only.
    results = vectorstore.similarity_search_with_relevance_scores(query, k=3)
    print(f"Retrieved {len(results)} chunks:")
    for index, (document, score) in enumerate(results):
        preview = " ".join(document.page_content.split())[:70]
        print(f"   {index}. {score:.3f}  {document.metadata.get('company', '?'):<12} {document.metadata.get('source', '?'):<20} {preview}...")


def main():
    require_api_key()
    verify_store()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(collection_name=COLLECTION_NAME, persist_directory=PERSIST_DIR, embedding_function=embeddings, collection_metadata={"hnsw:space": "cosine"})
    count = vectorstore._collection.count()
    if count == 0:
        raise SystemExit("The it_companies collection is empty; run lab1_vector_store.py first.")
    print(f"Collection {COLLECTION_NAME} count: {count}")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    rag_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()} | GROUNDED_PROMPT | llm | StrOutputParser())
    ungrounded_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()} | UNGROUNDED_PROMPT | llm | StrOutputParser())

    tests = [("Who is the CEO of TCS?", "answerable", ["krithivasan"]), ("What is Infosys revenue guidance for FY2025?", "answerable", ["3", "4"]), ("What is the stock price of TCS today?", "unanswerable", [REFUSAL.lower()]), ("Compare the founding years of TCS and Infosys", "multi-hop", ["1968", "1981"]), ("Where is Wipro headquartered and how many countries does it serve?", "answerable", ["bengaluru", "66"])]
    passed = 0
    for index, (query, query_type, expected) in enumerate(tests, 1):
        print("\n" + "-" * 60)
        print(f"[Q{index}] {query} ({query_type})")
        show_retrieval(vectorstore, query)
        answer = rag_chain.invoke(query)
        normalized = answer.lower()
        okay = all(value.lower() in normalized for value in expected)
        passed += int(okay)
        print("Answer:\n   " + answer.replace("\n", "\n   "))
        print(f"Check: expected {query_type:<12} -> {'PASS' if okay else 'FAIL'}")
        if index == 4 and not okay:
            print("Hint: multi-hop retrieval missed a required chunk — this is the failure mode Session 3B addresses.")
    print(f"\nTally: {passed}/{len(tests)}")

    if RUN_ABLATION:
        query = tests[2][0]
        ungrounded = ungrounded_chain.invoke(query)
        verdict = "refused" if REFUSAL.lower() in ungrounded.lower() else "attempted an answer not supported by context"
        grounded = rag_chain.invoke(query)
        print("\nABLATION — the word ONLY")
        print(f"  WITH \"ONLY\":     {grounded}")
        print(f"  WITHOUT \"ONLY\":  {ungrounded}")
        print(f"  Verdict: {verdict}")
        print("  The ungrounded answer cannot be verified against any retrieved chunk.")
        print("  This is the FM-6 grounding failure mode that RAGAS automates in Session 5.4.")


if __name__ == "__main__":
    main()