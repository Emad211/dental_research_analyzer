"""
test_analysis.py — Quick test for Step 3 (Statistical Analysis) with single model

Usage:
  python test_analysis.py --pdf inputs/pdfs/article.pdf
  python test_analysis.py --ocr-file outputs/ocr_results/article_ocr_20240101_120000.txt

This script tests only one model (gpt-4.1-mini).
"""

import sys
import argparse
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
# Test Model Configuration
# ══════════════════════════════════════════════════════════════════════
TEST_MODEL = {
    "key":      "gpt-4.1-mini",
    "name":     "gpt-4.1-mini",
    "provider": "OpenAI",
}


# ══════════════════════════════════════════════════════════════════════
def find_latest_ocr(pdf_name: str) -> Path | None:
    """Find the most recent OCR file for a given PDF."""
    stem = Path(pdf_name).stem
    matches = sorted(OCR_RESULTS_DIR.glob(f"{stem}_ocr_*.txt"))
    return matches[-1] if matches else None


# ══════════════════════════════════════════════════════════════════════
def test_analysis(ocr_text: str, pdf_name: str) -> None:
    """Run statistical analysis test with gpt-4.1-mini model."""

    logger.info("╔" + "═" * 68 + "╗")
    logger.info(f"║  Statistical Analysis Test with {TEST_MODEL['name']:<42}║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")

    logger.info(f"  PDF           : {pdf_name}")
    logger.info(f"  OCR text size : {len(ocr_text):,} characters")
    logger.info(f"  Test model    : {TEST_MODEL['name']}")
    logger.info(f"  Provider      : {TEST_MODEL['provider']}")
    logger.info(f"  Base URL      : {BASE_URL}")
    logger.info("")

    # ─────────────────────────────────────────────────────────────────
    # Prepare prompt
    # ─────────────────────────────────────────────────────────────────
    prompt = STATISTICAL_PROMPT.format(ocr_text=ocr_text)
    logger.info(f"  Prompt size   : {len(prompt):,} characters")
    logger.info("")

    # ─────────────────────────────────────────────────────────────────
    # Send API request
    # ─────────────────────────────────────────────────────────────────
    logger.info("  ▶ Sending request to API...")
    logger.info("")

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
        icon   = "✓"

        logger.info(f"  {icon} Response received")
        logger.info(f"  Response size : {len(result):,} characters")
        logger.info("")

    except Exception as exc:
        result = f"[Error receiving response: {exc}]"
        status = "Error"
        icon   = "✗"

        logger.error(f"  {icon} Error occurred:")
        logger.error(f"  {exc}")
        logger.info("")

    # ─────────────────────────────────────────────────────────────────
    # Display preview
    # ─────────────────────────────────────────────────────────────────
    if status == "Success":
        preview_lines = result.split("\n")[:20]
        preview = "\n".join(preview_lines)

        logger.info("  Response preview (first 20 lines):")
        logger.info("  " + "─" * 66)
        for line in preview_lines:
            logger.info(f"  {line}")
        logger.info("  " + "─" * 66)
        logger.info("")

    # ─────────────────────────────────────────────────────────────────
    # Save result
    # ─────────────────────────────────────────────────────────────────
    ts      = timestamp()
    stem    = Path(pdf_name).stem
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

    logger.info(f"  ✓ Result saved:")
    logger.info(f"    {filepath}")
    logger.info("")

    # ─────────────────────────────────────────────────────────────────
    # Final summary
    # ─────────────────────────────────────────────────────────────────
    logger.info("╔" + "═" * 68 + "╗")
    logger.info(f"║  {'Test Completed':<66}  ║")
    logger.info("╚" + "═" * 68 + "╝")


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Quick test of {TEST_MODEL['name']} for statistical analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with latest OCR of a PDF
  python test_analysis.py --pdf inputs/pdfs/article.pdf

  # Test with specific OCR file
  python test_analysis.py --ocr-file outputs/ocr_results/article_ocr_20240101_120000.txt
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--pdf",
        type=str,
        metavar="PATH",
        help="PDF path (its latest OCR will be used)",
    )
    source.add_argument(
        "--ocr-file",
        type=str,
        metavar="PATH",
        help="Direct path to OCR file",
    )

    args = parser.parse_args()

    # ─────────────────────────────────────────────────────────────────
    # Load OCR text
    # ─────────────────────────────────────────────────────────────────
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            sys.exit(1)

        ocr_file = find_latest_ocr(pdf_path.name)
        if ocr_file is None:
            logger.error(
                f"No OCR file found for «{pdf_path.name}».\n"
                "Run step 2 first: python main.py step2 --pdf ..."
            )
            sys.exit(1)

        pdf_name = pdf_path.name
        logger.info(f"OCR file found: {ocr_file.name}\n")

    else:  # --ocr-file
        ocr_file = Path(args.ocr_file)
        if not ocr_file.exists():
            logger.error(f"OCR file not found: {ocr_file}")
            sys.exit(1)

        # Extract PDF name from OCR filename
        # e.g.: article_ocr_20240101_120000.txt -> article.pdf
        pdf_name = ocr_file.name.split("_ocr_")[0] + ".pdf"

    # Load text
    ocr_text = load_text(ocr_file)

    if not ocr_text.strip():
        logger.error("OCR file is empty.")
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────────
    # Run test
    # ─────────────────────────────────────────────────────────────────
    test_analysis(ocr_text, pdf_name)


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()