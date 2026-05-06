````markdown
# 📊 Dental Research Statistical Analysis System

> Automated PDF extraction, OCR, and multi-model statistical analysis for dental research articles.

---

## ⚙️ Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure API**
```bash
cp .env.example .env
```
```env
API_KEY=your_api_key_here
BASE_URL=https://api.gapgpt.app/v1
```

---

## 🗂️ First Time: Rename PDFs

> Files with spaces or `- Copy` in their names will cause errors.  
> Run this **once** before anything else:

```bash
python rename_pdfs.py
```

Place your PDFs in `inputs/pdfs/` before running.

---

## 🚀 How to Run

### Option A — Command Line (`main.py`)

3 independent steps + full pipeline:

| Command | Single PDF | All PDFs |
|---------|-----------|----------|
| Step 1 · Extract images | `python main.py step1 --pdf inputs/pdfs/article.pdf` | `python main.py step1 --all-pdfs` |
| Step 2 · OCR | `python main.py step2 --pdf inputs/pdfs/article.pdf` | `python main.py step2 --all-pdfs` |
| Step 3 · Analysis | `python main.py step3 --pdf inputs/pdfs/article.pdf` | `python main.py step3 --all-pdfs` |
| All steps | `python main.py all --pdf inputs/pdfs/article.pdf` | `python main.py all --all-pdfs` |

> Each step saves output to disk. You can run them separately without re-running previous steps.

---

### Option B — Interactive Mode (`run_interactive.py`)

No need to type filenames manually. Select PDF and step from a numbered list:

```bash
python run_interactive.py
```

---

### Option C — Quick Test (`test_analysis.py`)

Runs **Step 3 only** with a single lightweight model (`gpt-4.1-mini`).  
Use this to verify the analysis pipeline before running all 4 models.

```bash
# Auto-detect latest OCR for a PDF
python test_analysis.py --pdf inputs/pdfs/article.pdf

# Use a specific OCR file
python test_analysis.py --ocr-file outputs/ocr_results/article_ocr_20240125_143022.txt
```

---

## 🔄 Workflow

```
inputs/pdfs/article.pdf
        │
        ▼
[Step 1] PDFExtractor
        → outputs/images/article/page_001.png ...
        │
        ▼
[Step 2] GeminiOCR                          (~$0.15–0.20 per article)
        → outputs/ocr_results/article_ocr_<timestamp>.txt
        │
        ▼
[Step 3] StatisticalAnalyzer  ×4 models
        → outputs/analysis_results/article/
                ├── gemini-3.1-pro-preview_<timestamp>.txt
                ├── gpt-5.2_<timestamp>.txt
                ├── gpt-4o_<timestamp>.txt
                ├── gpt-5.1_<timestamp>.txt
                ├── combined_<timestamp>.txt
                └── metadata_<timestamp>.json
```

---

## 📁 Project Structure

```
dental_research_analyzer/
│
├── inputs/pdfs/                # Place PDFs here
├── outputs/
│   ├── images/                 # Extracted page images
│   ├── ocr_results/            # OCR text files
│   └── analysis_results/       # Analysis reports
│       └── test/               # Test run outputs
│
├── config/settings.py          # Models, DPI, prompt
├── src/                        # Core modules
│
├── main.py                     # CLI pipeline
├── run_interactive.py          # Interactive mode
├── test_analysis.py            # Single-model test
└── rename_pdfs.py              # Clean PDF filenames
```

---

## 🔧 Configuration (`config/settings.py`)

| Setting | Default |
|---------|---------|
| Image DPI | `300` |
| OCR Model | `gemini-3-flash-preview` |
| Analysis Models | 4 models (Gemini, GPT-5.2, GPT-4o, GPT-5.1) |

> To change models or the statistical prompt, edit `config/settings.py`.

---

> ⚠️ **OCR cost:** approximately **$0.15–0.20 per article**. Run `test_analysis.py` first to validate before batch processing.
````