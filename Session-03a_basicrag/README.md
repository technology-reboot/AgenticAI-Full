# Session 3A — Basic RAG & Vector Databases · Lab specifications

Three Claude-Code-ready specs derived from `basic_rag_session.pptx` (slides 13–15).
Hand Claude Code **one spec file at a time** — each is self-contained.

| Spec | Generates | Slide |
|---|---|---|
| `LAB1_vector_store.md` | `lab1_vector_store.py` + `data/company_profiles/*.txt` | 13 |
| `LAB2_lcel_rag_chain.md` | `lab2_rag_chain.py` | 14 |
| `LAB3_retrieval_eval.md` | `lab3_retrieval_eval.py` + `eval_set.json` + chart/CSV | 15 |

## Run order

Lab 1 must run first — it creates the corpus and the persisted Chroma store at `./chroma_db`
(collection `it_companies`) that Labs 2 and 3 both read. Labs 2 and 3 are independent of each
other and can run in either order.

```
project/
├── .env                       # OPENAI_API_KEY
├── requirements.txt
├── data/company_profiles/     # created by Lab 1
├── chroma_db/                 # created by Lab 1
├── outputs/                   # created by Lab 3
├── lab1_vector_store.py
├── lab2_rag_chain.py
└── lab3_retrieval_eval.py
```

## Deviations from the slides — deliberate

1. **Python scripts, not notebooks.** All three slides list "Jupyter Notebook" under Tools;
   every spec overrides that. Update the Tools column on slides 13–15 before delivery so the
   deck and the code agree.
2. **No shared helper module.** Each lab is a single standalone file; the only thing they
   share is the persisted store on disk. Keeps each lab handout-able on its own.
3. **Cosine space is pinned explicitly** (`hnsw:space: cosine`) on the collection. Chroma
   defaults to L2, under which the 0.4–0.8 thresholds discussed on slides 8, 13 and 15 don't
   correspond to the cosine-similarity numbers taught.
4. **Corpus is generated, not supplied.** Lab 1 writes the 5 profiles with the exact facts
   the Lab 2 and Lab 3 questions probe, and with the exact gaps they probe for (no stock
   prices, no World Cup). Sized at 3,500–4,500 chars each so `chunk_size=400` yields the
   40–60 chunks the slide promises.
5. **Lab 3 is allowed to fail its own targets.** If no threshold clears precision ≥ 0.80 and
   recall ≥ 0.75 on a 5-document corpus, the script reports that honestly rather than
   massaging the numbers. Worth a word in the facilitator notes — it makes the point about
   evaluation better than a clean pass would.

## Cost

Roughly 60 embedding calls at index time plus ~40 query embeddings, and about 6 `gpt-4o-mini`
completions in Lab 2. Well under ₹10 per learner per full run. Lab 1's rebuild guard and
Lab 2's `RUN_ABLATION` flag exist to keep re-runs cheap for a 35-person batch.
