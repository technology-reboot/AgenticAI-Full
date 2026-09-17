from __future__ import annotations
 
import os
import sys
import json
import textwrap
 
from pathlib import Path
from typing import Literal
 
from dotenv import load_dotenv
from pydantic import BaseModel, Field
 
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
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
        sys.exit(f"Corpus path not found: {CORPUS_PATH}")
    entries=json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    for entry in entries:
        entry["text"] = "".join(entry["text"].split())
    return entries
 
CORPUS:list[dict[str,str]] = load_corpus()
 
def build_vectorstore() -> Chroma:
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "],
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
 
        print(f"Indexd {len(docs)} document chunks from {len(CORPUS)} docuemnts.")
        chroma = Chroma.from_documents(
            documents=docs,
            embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
            collection_name="meridian_policies",
        )
        return chroma
    except Exception as e:
        print(e)
 
BASIC_RAG_PROMPT = """You are Meridian's internal policy assistant. Answer the following questions using the context below
 
Context: {context}
 
Question: {question}
Answer:"""
 
def basic_rag(store: Chroma, question: str) -> tuple[str, list[dict[Document]]]:
    docs = store.similarity_search(question, k=TOP_K)
    context = "\n\n".join(
        f"[{doc.metadata['doc_id']} - {doc.metadata['title']}\n {doc.page_content}]" for doc in docs
    )
    prompt = BASIC_RAG_PROMPT.format(context=context, question=question)
    answer = generator_llm.invoke(prompt).content
    return answer, docs
 
def main() -> None:
    print("Building vector store...")
    store = build_vectorstore()
    print("Vector store built.")
 
    basic_answer, basic_docs = basic_rag(store, "What is Meridian's policy on remote work?")
    print(f"Answer: {basic_answer}")
    print(f"Sources: {[doc.metadata for doc in basic_docs]}")
 
if __name__  == "__main__":
    main()