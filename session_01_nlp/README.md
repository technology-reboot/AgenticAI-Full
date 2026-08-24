# Session 1 — NLP & Language Model Foundations: Labs

**Programme:** Agentic AI Training · Technology Reboot
**Lab time:** 30 minutes (3 labs, ~10 min each)

This folder contains three short, hands-on notebooks that build up core NLP
concepts from the session slides:

| Lab | Notebook | What you'll do |
|---|---|---|
| 1 | `lab1_spacy_pipeline.ipynb` | Tokenize, lemmatize, remove stop words, extract named entities with spaCy |
| 2 | `lab2_embeddings_explorer.ipynb` | Generate sentence embeddings, compare similarity, visualise clusters with PCA |
| 3 | `lab3_huggingface_inference.ipynb` | Run Hugging Face sentiment & summarisation pipelines, compare model sizes |

---

## 1. Prerequisites

- Python 3.10 or 3.11
- ~1.5 GB free disk space (for downloaded models — spaCy model, MiniLM,
  DistilBERT, BERT-base, BART are all downloaded on first use)
- An internet connection (for the one-time model downloads)
- An OpenAI API key (only needed for Lab 2, Cell 5 — optional)

---

## 2. Setup

All commands below assume your terminal's current directory is this folder
(`labs/session_01_nlp`).

### Step 1 — Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

> The spaCy English model (`en_core_web_sm`) is listed directly in
> `requirements.txt` as a wheel URL, so a separate download step usually
> isn't needed. If it's missing for any reason, install it explicitly:
> ```bash
> python -m spacy download en_core_web_sm
> ```

### Step 3 — Configure your OpenAI API key (optional, Lab 2 only)

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Then open `.env` and replace `your_key_here` with your actual OpenAI API key.
If you skip this, every lab still runs except Lab 2 Cell 5 (the OpenAI
embeddings comparison).

### Step 4 — Launch Jupyter

```bash
jupyter notebook
```

or, if you prefer JupyterLab / VS Code's built-in notebook support:

```bash
jupyter lab
```

In VS Code, you can also simply open any `.ipynb` file and run cells
directly using the built-in Jupyter extension (select the `venv`
interpreter as the kernel when prompted).

---

## 3. Running the labs

Open the notebooks in order and run all cells top to bottom
(Cell → Run All, or `Shift+Enter` cell by cell):

1. `lab1_spacy_pipeline.ipynb`
2. `lab2_embeddings_explorer.ipynb`
3. `lab3_huggingface_inference.ipynb`

**Tip:** the first time you run each lab, it needs to download a model
(spaCy ~13MB, MiniLM ~80MB, DistilBERT ~250MB, BART ~400MB). Kick off Lab 3
Cell 1–2 early if you're short on time, since BART is the largest download.

---

## 4. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `OSError: [E050] Can't find model 'en_core_web_sm'` | spaCy model not installed | `python -m spacy download en_core_web_sm` |
| `UserWarning: [W007] The model has no word vectors` | Using `en_core_web_sm` for similarity | Expected — this model ships with small vectors. Use `en_core_web_lg` for better accuracy. |
| Slow first run in Lab 2 (~2 min) | Downloading the MiniLM model | Normal, only happens once — subsequent runs use the local cache |
| `AuthenticationError` in Lab 2, Cell 5 | Missing/invalid OpenAI API key | Check that `.env` exists and contains a valid `OPENAI_API_KEY`, and that `load_dotenv()` ran before the client is created |
| First run of Lab 3 is very slow (3–8 min) | Downloading DistilBERT, BERT-base and BART (~1GB combined) | Normal, only happens once — start this lab early if time is tight |
| `CUDA out of memory` | GPU memory insufficient | All pipelines in this repo already use `device=-1` (CPU) by default |
| `OSError: We couldn't connect to HuggingFace Hub` | No internet access from your machine/VM | Pre-download models ahead of time, or ask your instructor for an offline model cache |

---

## 5. Repo layout

```
session_01_nlp/
├── README.md                       # this file
├── requirements.txt                # Python dependencies
├── .env.example                    # template for your OpenAI API key
├── data/
│   └── sample_text.txt             # business news snippet used in Lab 1
├── lab1_spacy_pipeline.ipynb
├── lab2_embeddings_explorer.ipynb
└── lab3_huggingface_inference.ipynb
```
