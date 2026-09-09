import os
import re
from typing import Any, Dict, List, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import numpy as np
import faiss

app = FastAPI(title="Customer Suppport RAG Agent", version = "1.0.0")

EMBED_MODEL = "text-embedding-3-small"  # OpenAI embedding model used when an API key is available
EMBED_DIM = 256  # Dimensionality of the offline hashing embedding fallback
STOPWORDS = {
    "the", "and", "for", "you", "your", "are", "can", "with", "from", "this",
    "that", "have", "has", "not", "but", "will", "please",
}

class AgentRequest(BaseModel):
    question: str
    context: str | None = None

FAQ_KB: Dict[str, str] = {
    "refund": "Refunds are processed within 5-7 business days for eligible orders. To request a refund, open the billing section in your account and select 'Request refund'.",
    "password": "Reset your password from the sign-in screen by selecting 'Forgot password'. If you are locked out, contact support with your account email for manual assistance.",
    "billing": "Billing updates are available in the Settings > Billing page. You can add a payment method, review invoices, and update your subscription plan there.",
    "shipping": "Standard shipping usually arrives in 3-5 business days. Tracking details are shown in the order history section once the shipment has been dispatched.",
    "subscription": "You can downgrade or cancel your plan from Settings > Subscription. Changes take effect at the end of the current billing cycle.",
    "delivery": "If your package is delayed, please check the tracking link or contact support with your order number and courier reference.",
}

def fallback_rag_answer(question: str) -> str:
    q = question.lower()
    for keyword, answer in FAQ_KB.items():
        if keyword in q:
            return answer
    return(
        "I can help with account, biling, shipping and subscription issues."
        "please share your order number or account email if you need a specific resolution"
    )


def _hash_embedding(text: str, dim: int = EMBED_DIM) -> np.ndarray:  # Deterministic offline embedding (no network)
    vector = np.zeros(dim, dtype="float32")  # Start with an all-zeros vector of the target dimensionality
    for token in re.findall(r"[a-z0-9]+", text.lower()):  # Lowercase then split into alphanumeric word tokens
        if len(token) < 3 or token in STOPWORDS:  # Skip very short and low-signal tokens that only add noise
            continue  # Move on to the next token
        vector[hash(token) % dim] += 1.0  # Bag-of-words hashing trick: bump the bucket this token maps to
    norm = float(np.linalg.norm(vector))  # L2 norm of the vector (0.0 if the text had no usable tokens)
    return vector / norm if norm else vector  # Return a unit vector so dot products act as cosine similarity


def embed_texts(texts: List[str]) -> Tuple[np.ndarray, str]:  # Embed a batch of texts, reporting which backend ran
    api_key = os.getenv("OPENAI_API_KEY")  # Read the OpenAI API key from the environment (None if unset)
    if api_key and OpenAI is not None:  # Only call the API if we have both a key and the client library
        try:  # Network/API calls can fail; fall back to the offline embedding on any error
            client = OpenAI(api_key=api_key)  # Instantiate the OpenAI client with the provided key
            response = client.embeddings.create(model=EMBED_MODEL, input=texts)  # Request one embedding per input
            matrix = np.array([item.embedding for item in response.data], dtype="float32")  # Stack into a 2D array
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)  # Per-row L2 norms for normalisation
            norms[norms == 0] = 1.0  # Guard against divide-by-zero for any all-zero row
            return matrix / norms, "openai"  # Unit-normalised embeddings, tagged with the backend used
        except Exception:  # Any error (auth, rate limit, network, parsing) -> degrade to offline embeddings
            pass  # Fall through to the hashing embedding below
    return np.vstack([_hash_embedding(text) for text in texts]), "hashing"  # Offline fallback embedding matrix


class FaissVectorStore:  # In-process vector database backed by a FAISS index: replaces the ChromaDB dependency
    def __init__(self, documents: Dict[str, str]) -> None:  # Build the index from a {key: text} knowledge base
        self.keys: List[str] = list(documents.keys())  # Stable ordered list of document keys (topic names)
        self.texts: List[str] = list(documents.values())  # Matching ordered list of document bodies (answers)
        passages = [f"{key}: {text}" for key, text in zip(self.keys, self.texts)]  # Combine key + body per doc
        matrix, self.backend = embed_texts(passages)  # Embed every document; remember which backend produced it
        self.dim: int = matrix.shape[1]  # Embedding dimensionality (depends on which backend produced the vectors)
        self.index = faiss.IndexFlatIP(self.dim)  # Flat index over inner product; unit vectors -> cosine similarity
        self.index.add(np.ascontiguousarray(matrix, dtype="float32"))  # Load all document vectors into the index

    def search(self, query: str, top_k: int = 1) -> List[Tuple[str, str, float]]:  # Nearest-neighbour lookup
        query_matrix, _ = embed_texts([query])  # Embed the query with the same backend logic as the documents
        vectors = np.ascontiguousarray(query_matrix, dtype="float32")  # FAISS needs a contiguous float32 array
        scores, indices = self.index.search(vectors, min(top_k, len(self.keys)))  # Top-k search: scores + row ids
        return [  # Map FAISS row ids back to (key, answer, score) tuples, best match first
            (self.keys[idx], self.texts[idx], float(score))
            for score, idx in zip(scores[0], indices[0])
            if idx != -1  # FAISS returns -1 for empty slots when fewer than top_k results exist
        ]

VECTOR_STORE = FaissVectorStore(FAQ_KB)  # Build the FAISS-backed vector store once at startup from the FAQ KB

def retrieve_context(question: str) ->str | None:
    matches = VECTOR_STORE.search(question, top_k=1)
    if matches and matches[0][2] >= 0.2:
        return matches[0][1]
    return None

def get_rag_answer(question: str) -> str:
    context = retrieve_context(question)
    model = "gpt-4o-mini"
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=api_key)
            user_content = question if not context else(
                f"Knowledge base context:\n{context}\n\nCustomer question:  {question}"
            )            
            response = client.chat.completions.create(
                model = model,
                messages=[
                    {
                        "role" : "system",
                        "content" : (
                            "You are a helpful customer support agent. Answer clearly and concisely "
                            "using only the information in the knowledge base context and avoid making up unsupported details"
                        )
                    },
                    {
                        "role": "user",
                        "content" : user_content
                    }
                ],
                temperature=0.3, 
                max_tokens=250,
            )
            return (response.choices[0].message.content or "").strip() or fallback_rag_answer(question)
        except Exception:
            return fallback_rag_answer(question)
    return fallback_rag_answer(question)

@app.post("/agent")
def agent_route(payload : AgentRequest) -> Dict[str, Any]:
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    answer = get_rag_answer(question)
    return{
        "question" : question,
        "answer" : answer,
        "status" : "ok",
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host = "0.0.0.0", port=8000, reload = True)