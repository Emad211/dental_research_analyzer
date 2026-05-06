### `README.md`

```markdown
# 📊 Dental Research Statistical Analysis System

> Automated PDF extraction, OCR, and multi-model statistical analysis pipeline for dental research articles.

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
pip install -r requirements.txt
```

### 2️⃣ Configuration

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```env
API_KEY=your_api_key_here
BASE_URL=https://api.gapgpt.app/v1
```

---

## 📋 Usage

### Main Pipeline Commands

The system has **3 independent steps** that can be run separately or together:

| Step | Description | Single PDF | All PDFs |
|:----:|-------------|------------|----------|
| **1** | Extract images from PDF | `python main.py step1 --pdf inputs/pdfs/article.pdf` | `python main.py step1 --all-pdfs` |
| **2** | OCR images with Gemini | `python main.py step2 --pdf inputs/pdfs/article.pdf` | `python main.py step2 --all-pdfs` |
| **3** | Statistical analysis (4 AI models) | `python main.py step3 --pdf inputs/pdfs/article.pdf` | `python main.py step3 --all-pdfs` |
| **ALL** | Run all 3 steps sequentially | `python main.py all --pdf inputs/pdfs/article.pdf` | `python main.py all --all-pdfs` |

---

### 🧪 Quick Test (Single Model)

Test **Step 3** with only `gpt-4.1-mini` model:

#### Option A: Auto-detect latest OCR
```bash
python test_analysis.py --pdf inputs/pdfs/article.pdf
```

#### Option B: Use specific OCR file
```bash
python test_analysis.py --ocr-file outputs/ocr_results/article_ocr_20240125_143022.txt
```

---

## 📁 Project Structure

```
dental_research_analyzer/
│
├── inputs/pdfs/              # 📥 Place your PDF files here
│
├── outputs/
│   ├── images/               # 🖼️  Extracted PNG images
│   ├── ocr_results/          # 📝 OCR text files
│   └── analysis_results/     # 📊 Statistical analysis reports
│       ├── <pdf_name>/       # Regular analysis (4 models)
│       └── test/             # Test analysis (1 model)
│
├── config/
│   └── settings.py           # ⚙️  Configuration
│
├── src/
│   ├── pdf_processor/        # 📄 PDF → Images
│   ├── ocr/                  # 🔍 Images → Text
│   ├── analyzer/             # 🧠 Text → Analysis
│   └── utils/                # 🛠️  Helpers
│
├── main.py                   # 🎯 Main entry point
├── test_analysis.py          # 🧪 Quick test script
└── requirements.txt
```

---

## 🔄 Workflow

```
┌─────────────────┐
│   PDF File      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  STEP 1         │  Extract images (300 DPI)
│  PDFExtractor   │  → outputs/images/<pdf_name>/page_001.png
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  STEP 2         │  OCR with Gemini Flash
│  GeminiOCR      │  → outputs/ocr_results/<pdf_name>_ocr_<timestamp>.txt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  STEP 3         │  Statistical analysis with 4 AI models
│  Analyzer       │  ├─ gemini-3.1-pro-preview
│                 │  ├─ gpt-5.2
│                 │  ├─ gpt-4o
│                 │  └─ gpt-5.1
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output Files   │  → outputs/analysis_results/<pdf_name>/
│                 │     ├─ gemini-3.1-pro-preview_<timestamp>.txt
│                 │     ├─ gpt-5.2_<timestamp>.txt
│                 │     ├─ gpt-4o_<timestamp>.txt
│                 │     ├─ gpt-5.1_<timestamp>.txt
│                 │     ├─ combined_<timestamp>.txt
│                 │     └─ metadata_<timestamp>.json
└─────────────────┘
```

---

## 💡 Examples

### Example 1: Process a single PDF (all steps)
```bash
python main.py all --pdf inputs/pdfs/dental_research_2024.pdf
```

### Example 2: Process all PDFs (all steps)
```bash
python main.py all --all-pdfs
```

### Example 3: Only extract images from all PDFs
```bash
python main.py step1 --all-pdfs
```

### Example 4: Only run analysis on a specific PDF
```bash
python main.py step3 --pdf inputs/pdfs/dental_research_2024.pdf
```

### Example 5: Quick test with single model
```bash
python test_analysis.py --pdf inputs/pdfs/dental_research_2024.pdf
```

---

## 🎯 Key Features

✅ **Modular Design** — Run steps independently or together  
✅ **High Quality OCR** — 300 DPI image extraction + Gemini Flash  
✅ **Multi-Model Analysis** — 4 AI models for comprehensive results  
✅ **Batch Processing** — Process single or multiple PDFs  
✅ **Quick Testing** — Test mode with single model  
✅ **Auto-Resume** — Each step saves to disk; next step auto-loads  

---

## 📦 Dependencies

- **pymupdf** — PDF processing
- **Pillow** — Image handling
- **openai** — API client (works with all providers)
- **python-dotenv** — Environment variables
- **tqdm** — Progress bars

---

## 🔧 Configuration

Edit `config/settings.py` to customize:

- **Image DPI** (default: 300)
- **OCR Model** (default: gemini-3-flash-preview)
- **Analysis Models** (default: 4 models)
- **Statistical Prompt** (biostatistics analysis template)

---

## 📝 Notes

> **💡 Tip:** Each step saves its output to disk, so you can run steps separately without re-processing previous steps.

> **⚠️ Important:** Make sure your `.env` file contains a valid `API_KEY` before running the scripts.

> **🚀 Performance:** Step 2 (OCR) includes 2-second delays between pages to respect API rate limits. Step 3 includes 3-second delays between models.

---

## 📄 License

This project is for research purposes.

---

**Made with ❤️ for dental research analysis**
```