"""
test_analysis.py — Quick test for Step 3 (Statistical Analysis) with single model
"""

import sys
import argparse
import re
from pathlib import Path
from openai import OpenAI

from config.settings import (
    API_KEY,
    BASE_URL,
    STATISTICAL_PROMPT,
    OCR_RESULTS_DIR,
    ANALYSIS_RESULTS_DIR,
)

from src.utils import setup_logger, load_text, save_text, timestamp

logger = setup_logger("TestAnalysis")


# ══════════════════════════════════════════════════════════════════════
# Model Configuration
# ══════════════════════════════════════════════════════════════════════
TEST_MODEL = {
        "key":      "gpt-4.1-mini",
        "name":     "gpt-4.1-mini",
        "provider": "OpenAI",
    }


# ══════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════
def safe_stem(name: str, max_length: int = 60) -> str:
    """
    Make a filesystem‑safe short name to avoid Windows path length issues.
    """
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-]", "_", stem)
    return stem[:max_length]


def find_latest_ocr(pdf_name: str) -> Path | None:
    """Find the most recent OCR file for a given PDF."""
    stem = Path(pdf_name).stem
    matches = sorted(OCR_RESULTS_DIR.glob(f"{stem}_ocr_*.txt"))
    return matches[-1] if matches else None


# ══════════════════════════════════════════════════════════════════════
def test_analysis(ocr_text: str, pdf_name: str) -> None:
    """Run statistical analysis test with a single model."""

    logger.info("╔" + "═" * 68 + "╗")
    logger.info(f"║  Statistical Analysis Test with {TEST_MODEL['name']:<42}║")
    logger.info("╚" + "═" * 68 + "╝\n")

    logger.info(f"  PDF           : {pdf_name}")
    logger.info(f"  OCR text size : {len(ocr_text):,} characters")
    logger.info(f"  Model         : {TEST_MODEL['name']}")
    logger.info(f"  Provider      : {TEST_MODEL['provider']}")
    logger.info(f"  Base URL      : {BASE_URL}\n")

    # ────────────────────────────────────────────────────────────────
    # Prepare prompt
    # ────────────────────────────────────────────────────────────────
    prompt = STATISTICAL_PROMPT.format(ocr_text=ocr_text)

    logger.info(f"  Prompt size   : {len(prompt):,} characters\n")
    logger.info("  ▶ Sending request to API...\n")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    try:
        response = client.chat.completions.create(
            model=TEST_MODEL["name"],
            temperature=0.3,
            max_tokens=8192,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert biostatistician specializing "
                        "in dental and clinical research methodology."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        result = response.choices[0].message.content.strip()
        status = "Success"

        logger.info("  ✓ Response received")
        logger.info(f"  Response size : {len(result):,} characters\n")

    except Exception as exc:
        result = f"[Error receiving response: {exc}]"
        status = "Error"

        logger.error("  ✗ API request failed")
        logger.error(f"  {exc}\n")

    # ────────────────────────────────────────────────────────────────
    # Show preview
    # ────────────────────────────────────────────────────────────────
    if status == "Success":
        preview_lines = result.split("\n")[:20]

        logger.info("  Response preview (first 20 lines)")
        logger.info("  " + "─" * 66)

        for line in preview_lines:
            logger.info(f"  {line}")

        logger.info("  " + "─" * 66 + "\n")

    # ────────────────────────────────────────────────────────────────
    # Save result
    # ────────────────────────────────────────────────────────────────
    ts = timestamp()
    stem = safe_stem(pdf_name)

    out_dir = ANALYSIS_RESULTS_DIR / "test" / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{TEST_MODEL['key']}_{ts}.txt"
    filepath = out_dir / filename

    header = (
        f"{'═'*70}\n"
        f"TEST STATISTICAL ANALYSIS\n"
        f"Model   : {TEST_MODEL['name']} ({TEST_MODEL['provider']})\n"
        f"PDF     : {pdf_name}\n"
        f"Status  : {status}\n"
        f"Time    : {ts}\n"
        f"{'═'*70}\n\n"
    )

    save_text(filepath, header + result)

    logger.info("  ✓ Result saved")
    logger.info(f"    {filepath}\n")

    logger.info("╔" + "═" * 68 + "╗")
    logger.info(f"║  {'Test Completed':<66}  ║")
    logger.info("╚" + "═" * 68 + "╝")


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════
def main() -> None:

    parser = argparse.ArgumentParser(
        description="Quick statistical analysis model test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group(required=True)

    source.add_argument(
        "--pdf",
        type=str,
        help="PDF path (latest OCR will be used)",
    )

    source.add_argument(
        "--ocr-file",
        type=str,
        help="Direct OCR file path",
    )

    args = parser.parse_args()

    # ────────────────────────────────────────────────────────────────
    # Load OCR
    # ────────────────────────────────────────────────────────────────
    if args.pdf:

        pdf_path = Path(args.pdf)

        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            sys.exit(1)

        ocr_file = find_latest_ocr(pdf_path.name)

        if ocr_file is None:
            logger.error(
                f"No OCR file found for «{pdf_path.name}».\n"
                "Run step 2 first."
            )
            sys.exit(1)

        pdf_name = pdf_path.name

        logger.info(f"OCR file found: {ocr_file.name}\n")

    else:

        ocr_file = Path(args.ocr_file)

        if not ocr_file.exists():
            logger.error(f"OCR file not found: {ocr_file}")
            sys.exit(1)

        pdf_name = ocr_file.name.split("_ocr_")[0] + ".pdf"

    # Load text
    ocr_text = load_text(ocr_file)

    if not ocr_text.strip():
        logger.error("OCR file is empty.")
        sys.exit(1)

    # Run analysis
    test_analysis(ocr_text, pdf_name)


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
