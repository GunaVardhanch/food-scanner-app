# RAG Pipeline — Food Label Analyser

A **fully offline, non-intrusive** RAG side pipeline for the Food Scanner backend.  
Zero changes to the core barcode/ML pipeline. Activate with one environment variable.

## What it does

Analyses food label OCR text against a curated FSSAI knowledge base to produce:

| Output | Example |
|--------|---------|
| `additive_flags` | `[{code: "INS 621", name: "MSG", risk: "moderate"}]` |
| `warnings` | `["High Sodium", "Contains Trans Fat"]` |
| `fssai_compliance` | `true` / `false` |
| `score` | `4.5 / 10` |
| `score_grade` | `GREEN` / `YELLOW` / `RED` |
| `allergens_detected` | `["gluten", "milk"]` |
| `healthy_alternative` | `"Choose fresh fruit instead of..."` |

## Setup

### 1. Install dependencies

```bash
cd food-scanner-app/backend
.venv\Scripts\pip.exe install -r rag_pipeline/requirements.txt
```

> **First run** (~1 min): sentence-transformers will download the `all-MiniLM-L6-v2` model (~90MB).  
> Subsequent runs use the cached FAISS index under `rag_pipeline/vector_store/`.

### 2. Run the standalone test (no server needed)

```bash
cd food-scanner-app/backend
.venv\Scripts\python.exe rag_pipeline\test_rag.py
```

Expected: 3 Indian product analyses printed + `All assertions passed!`

### 3. Enable in the live API

Set the environment variable before starting the server:

```powershell
# PowerShell
$env:RAG_ENABLED = "true"
.venv\Scripts\python.exe run.py
```

The `/api/scan` response will then include a `rag_analysis` key with the full structured output.

## Architecture

```
OCR text (or pre-parsed nutrition dict from barcode DB)
    │
    ▼
utils/ocr_parser.py  ──► nutrition dict + ingredients list
    │
    ├── Fuzzy match vs. fssai_additives.json   (rapidfuzz)
    ├── FAISS context retrieval                 (sentence-transformers)
    ├── Rule engine vs. harmful_flags.json      (pure Python)
    └── Scoring vs. nutrition_guidelines.json
    │
    ▼
Validated dict  →  response_body["rag_analysis"]
```

## Knowledge Base

| File | Contents |
|------|----------|
| `knowledge_base/fssai_additives.json` | 100+ INS/E codes with safety ratings and health risks |
| `knowledge_base/harmful_flags.json` | Risk tiers, allergens, FSSAI daily limits |
| `knowledge_base/nutrition_guidelines.json` | Traffic light thresholds, score weights |

## Files

```
rag_pipeline/
├── __init__.py              ← Public API: analyze_label_text()
├── rag_analyzer.py          ← Main pipeline engine
├── output_schemas.py        ← Pydantic v2 output models
├── requirements.txt         ← New dependencies only
├── test_rag.py              ← Standalone tests (Maggi, Parle-G, Amul)
├── knowledge_base/
│   ├── fssai_additives.json
│   ├── harmful_flags.json
│   └── nutrition_guidelines.json
├── vector_store/
│   └── index.faiss          ← Built at first run, gitignored
└── utils/
    ├── ocr_parser.py        ← OCR text → structured nutrition + ingredients
    ├── embedder.py          ← FAISS index builder + retrieval
    └── llm_prompts.py       ← Warning explanation templates
```

## Gitignore

Add to `.gitignore`:
```
rag_pipeline/vector_store/index.faiss
rag_pipeline/vector_store/id_map.json
```
(The FAISS index is rebuilt from JSON on first run — no need to commit the binary.)
