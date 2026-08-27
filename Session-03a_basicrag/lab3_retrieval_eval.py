import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_openai import OpenAIEmbeddings


PERSIST_DIR = "./faiss_index"
COLLECTION_NAME = "it_companies"


# Must match how lab1 built the index (see lab1_vector_store.py).
STORE_KWARGS = dict(normalize_L2=True, distance_strategy=DistanceStrategy.EUCLIDEAN_DISTANCE)


def cosine_relevance(distance):
    return 1.0 - distance / 2.0


EVAL_PATH = Path("eval_set.json")
OUTPUT_DIR = Path("outputs")
THRESHOLDS = [0.5, 0.7, 0.8]
DEFAULT_EVAL = [
    {"id": "q01", "question": "Who is the CEO of TCS?", "gold_companies": ["TCS"], "type": "single"},
    {"id": "q02", "question": "When was Infosys founded and by whom?", "gold_companies": ["Infosys"], "type": "single"},
    {"id": "q03", "question": "What is Infosys revenue growth guidance for FY2025?", "gold_companies": ["Infosys"], "type": "single"},
    {"id": "q04", "question": "In how many countries does Wipro serve clients?", "gold_companies": ["Wipro"], "type": "single"},
    {"id": "q05", "question": "Where is HCLTech headquartered?", "gold_companies": ["HCLTech"], "type": "single"},
    {"id": "q06", "question": "Which group does Tech Mahindra belong to?", "gold_companies": ["TechMahindra"], "type": "single"},
    {"id": "q07", "question": "Compare the founding years of TCS and Infosys", "gold_companies": ["TCS", "Infosys"], "type": "multi_hop"},
    {"id": "q08", "question": "Which of these companies is headquartered in Pune?", "gold_companies": ["TechMahindra", "Infosys"], "type": "multi_hop"},
    {"id": "q09", "question": "Which company started as a vegetable products business?", "gold_companies": ["Wipro"], "type": "single"},
    {"id": "q10", "question": "Who won the FIFA World Cup in 2022?", "gold_companies": [], "type": "out_of_domain"},
]


def require_api_key():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")


def load_eval_set():
    if not EVAL_PATH.exists():
        EVAL_PATH.write_text(json.dumps(DEFAULT_EVAL, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {EVAL_PATH}")
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))


def verify_store():
    if not (Path(PERSIST_DIR) / f"{COLLECTION_NAME}.faiss").exists():
        raise SystemExit("FAISS store is missing; run lab1_vector_store.py first.")


def evaluate_question(retrieved, gold):
    companies = [document.metadata.get("company") for document in retrieved]
    relevant = sum(company in gold for company in companies)
    if not gold:
        return (1.0 if not retrieved else 0.0), None, 0
    covered = len(set(companies) & set(gold))
    return relevant / len(retrieved) if retrieved else 0.0, covered / len(gold), covered


def main():
    require_api_key()
    verify_store()
    evaluation = load_eval_set()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.load_local(
        PERSIST_DIR, embeddings, COLLECTION_NAME, allow_dangerous_deserialization=True,
        relevance_score_fn=cosine_relevance, **STORE_KWARGS,
    )
    count = vectorstore.index.ntotal
    if count == 0:
        raise SystemExit("The it_companies collection is empty; run lab1_vector_store.py first.")
    print(f"Collection {COLLECTION_NAME} count: {count}")
    rows = []
    for threshold in THRESHOLDS:
        retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": threshold, "k": 5})
        for item in evaluation:
            retrieved = retriever.invoke(item["question"])
            precision, recall, covered = evaluate_question(retrieved, item["gold_companies"])
            rows.append({"threshold": threshold, "id": item["id"], "type": item["type"], "retrieved": len(retrieved), "relevant": sum(document.metadata.get("company") in item["gold_companies"] for document in retrieved), "gold_covered": f"{covered}/{len(item['gold_companies'])}" if item["gold_companies"] else "-", "precision": precision, "recall": recall})
        detail = pd.DataFrame([row for row in rows if row["threshold"] == threshold])
        print(f"\nTHRESHOLD {threshold:.2f}")
        print(detail[["id", "type", "retrieved", "relevant", "gold_covered", "precision", "recall"]].to_string(index=False, float_format=lambda value: f"{value:.3f}"))
        print("MACRO MEAN", f"precision={detail.precision.mean():.3f}", f"recall={detail.recall.dropna().mean():.3f}")

    summary = []
    for threshold in THRESHOLDS:
        detail = pd.DataFrame([row for row in rows if row["threshold"] == threshold])
        precision = detail.precision.mean()
        recall = detail.recall.dropna().mean()
        summary.append({"threshold": threshold, "precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0, "mean_chunks_retrieved": detail.retrieved.mean()})
    summary_frame = pd.DataFrame(summary)
    OUTPUT_DIR.mkdir(exist_ok=True)
    summary_frame.to_csv(OUTPUT_DIR / "threshold_results.csv", index=False)
    print("\nSUMMARY")
    print(summary_frame.to_string(index=False, float_format=lambda value: f"{value:.3f}"))

    plt.figure(figsize=(8, 5))
    plt.plot(summary_frame.threshold, summary_frame.precision, marker="o", label="Precision")
    plt.plot(summary_frame.threshold, summary_frame.recall, marker="o", label="Recall")
    for metric in ("precision", "recall"):
        for _, row in summary_frame.iterrows():
            plt.annotate(f"{row[metric]:.2f}", (row.threshold, row[metric]), textcoords="offset points", xytext=(0, 8), ha="center")
    plt.axhline(0.80, linestyle="--", label="Precision target 0.80")
    plt.axhline(0.75, linestyle="--", label="Recall target 0.75")
    plt.title("Retrieval precision vs recall by score threshold (it_companies, k=5)")
    plt.ylim(0, 1.05)
    plt.xlabel("Similarity threshold")
    plt.ylabel("Macro score")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plot_path = OUTPUT_DIR / "precision_recall.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {plot_path} and {OUTPUT_DIR / 'threshold_results.csv'}")

    qualifying = summary_frame[(summary_frame.precision >= 0.80) & (summary_frame.recall >= 0.75)]
    recommendation = (qualifying.sort_values("f1").iloc[-1] if not qualifying.empty else summary_frame.sort_values("f1").iloc[-1])
    if qualifying.empty:
        missed = []
        if recommendation.precision < 0.80:
            missed.append(f"precision by {0.80 - recommendation.precision:.3f}")
        if recommendation.recall < 0.75:
            missed.append(f"recall by {0.75 - recommendation.recall:.3f}")
        print(f"No threshold clears both targets; recommend {recommendation.threshold:.2f} by highest F1, missing {' and '.join(missed)}.")
    else:
        print(f"Recommended threshold: {recommendation.threshold:.2f} (highest F1 among thresholds clearing both targets).")

    q10 = pd.DataFrame([row for row in rows if row["id"] == "q10"])
    print("\nOUT-OF-DOMAIN q10")
    print(q10[["threshold", "retrieved", "precision"]].to_string(index=False))
    empty_threshold = next((row.threshold for _, row in q10.sort_values("threshold").iterrows() if row.retrieved == 0), "never")
    multi = pd.DataFrame([row for row in rows if row["type"] == "multi_hop"]).groupby("id").recall.mean()
    degraded = ", ".join(multi[multi < multi.max()].index) or "none"
    print(f"Q10 first returns nothing at {empty_threshold}; raising the threshold can reduce multi-hop recall, with degraded questions: {degraded}.")


if __name__ == "__main__":
    main()