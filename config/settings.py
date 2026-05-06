import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# مسیرهای پروژه
# ============================================================
BASE_DIR    = Path(__file__).resolve().parent.parent
INPUTS_DIR  = BASE_DIR / "inputs" / "pdfs"
OUTPUTS_DIR = BASE_DIR / "outputs"

IMAGES_DIR          = OUTPUTS_DIR / "images"
OCR_RESULTS_DIR     = OUTPUTS_DIR / "ocr_results"
ANALYSIS_RESULTS_DIR = OUTPUTS_DIR / "analysis_results"

for _dir in [INPUTS_DIR, IMAGES_DIR, OCR_RESULTS_DIR, ANALYSIS_RESULTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# تنظیمات API (یک کلید، یک base_url برای همه مدل‌ها)
# ============================================================
API_KEY  = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.gapgpt.app/v1")

if not API_KEY:
    raise EnvironmentError(
        "متغیر محیطی API_KEY تنظیم نشده است.\n"
        "فایل .env را بسازید و API_KEY را در آن قرار دهید."
    )

# ============================================================
# تنظیمات استخراج تصویر
# ============================================================
IMAGE_DPI    = 300
IMAGE_FORMAT = "PNG"

# ============================================================
# مدل OCR
# ============================================================
OCR_MODEL = "gemini-3-flash-preview"

# ============================================================
# مدل‌های تحلیل آماری
# ============================================================
ANALYSIS_MODELS = [
    {
        "key":      "gemini-3.1-pro-preview",
        "name":     "gemini-3.1-pro-preview",
        "provider": "Google",
    },
    {
        "key":      "gpt-5.2",
        "name":     "gpt-5.2",
        "provider": "OpenAI",
    },
    {
        "key":      "gpt-4o",
        "name":     "gpt-4o",
        "provider": "OpenAI",
    },
    {
        "key":      "gpt-5.1",
        "name":     "gpt-5.1",
        "provider": "OpenAI",
    },
]

# ============================================================
# پرامپت تحلیل آماری
# ============================================================
STATISTICAL_PROMPT = """\
You are a biostatistician. You will be provided with the Introduction \
and Methods sections of a published dental research article. Read the \
text carefully, extract all relevant methodological information, and \
provide a comprehensive statistical analysis plan.

TASK 1: INFORMATION EXTRACTION
Identify and extract all relevant study characteristics from the \
provided text, including but not limited to: study design, objectives, \
groups, sample size, variables, measurements, and data collection methods.

TASK 2: STATISTICAL ANALYSIS PLAN
Based on your extracted information, recommend all appropriate \
statistical tests in three categories:

CATEGORY A – MANDATORY
Tests without which the analysis would be incomplete.

CATEGORY B – RECOMMENDED
Tests that enhance the quality and rigor of the analysis.

CATEGORY C – OPTIONAL
Tests that provide supplementary insights.

For each test, provide:
- Test name
- Purpose
- Why appropriate (minimum 2 reasons)
- Why it may not be appropriate (minimum 1 reason)
- When this test should NOT be used
- Alternative if assumptions are violated

TASK 3: INAPPROPRIATE TESTS
List tests that should NOT be used for this study and explain why.

TASK 4: SUMMARY
Briefly justify the overall analytical approach.

================================================================
ARTICLE TEXT:
{ocr_text}
"""