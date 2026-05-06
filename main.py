"""
main.py — نقطه ورود اصلی

حالت‌های اجرا:
  step1   : فقط استخراج تصاویر از PDF
  step2   : فقط OCR (نیاز به اجرای step1 قبلاً)
  step3   : فقط تحلیل آماری (نیاز به اجرای step2 قبلاً)
  all     : اجرای هر سه مرحله پشت سر هم

هدف:
  --pdf <path>   : یک فایل PDF مشخص
  --all-pdfs     : تمام PDFهای موجود در inputs/pdfs/
"""

import sys
import argparse
from pathlib import Path

from config.settings import INPUTS_DIR, OCR_RESULTS_DIR, IMAGES_DIR
from src.pdf_processor import PDFExtractor
from src.ocr import GeminiOCR
from src.analyzer import StatisticalAnalyzer
from src.utils import setup_logger, load_text

logger = setup_logger("Main")


# ══════════════════════════════════════════════════════════════════════
#  ابزارهای کمکی
# ══════════════════════════════════════════════════════════════════════

def _banner(title: str) -> None:
    logger.info("╔" + "═" * 58 + "╗")
    logger.info(f"║  {title:<56}║")
    logger.info("╚" + "═" * 58 + "╝")


def _find_latest_ocr(pdf_name: str) -> Path | None:
    """جدیدترین فایل OCR مربوط به یک PDF را پیدا می‌کند."""
    stem = Path(pdf_name).stem
    matches = sorted(OCR_RESULTS_DIR.glob(f"{stem}_ocr_*.txt"))
    return matches[-1] if matches else None


def _find_latest_images(pdf_name: str) -> list[Path]:
    """تصاویر استخراج‌شده مربوط به یک PDF را برمی‌گرداند."""
    stem = Path(pdf_name).stem
    img_dir = IMAGES_DIR / stem
    if not img_dir.exists():
        return []
    return sorted(img_dir.glob("page_*.png"))


# ══════════════════════════════════════════════════════════════════════
#  مرحله ۱ — استخراج تصاویر
# ══════════════════════════════════════════════════════════════════════

def run_step1(pdf_path: Path) -> list[dict]:
    """
    استخراج تمام صفحات PDF به‌صورت تصویر PNG.

    Returns:
        لیست اطلاعات صفحات (خروجی PDFExtractor.extract)
    """
    _banner(f"مرحله ۱ — استخراج تصاویر  |  {pdf_path.name}")

    extractor = PDFExtractor()

    info = extractor.pdf_info(pdf_path)
    logger.info(f"  عنوان  : {info['title']}")
    logger.info(f"  صفحات  : {info['pages']}")
    logger.info(f"  حجم    : {info['size_mb']} MB")
    logger.info("")

    pages = extractor.extract(pdf_path)

    logger.info("")
    logger.info(f"  ✓ {len(pages)} تصویر با موفقیت استخراج شد.")
    logger.info(
        f"  مسیر ذخیره: outputs/images/{pdf_path.stem}/"
    )
    logger.info("")

    # نمایش خلاصه صفحات
    logger.info("  خلاصه صفحات استخراج‌شده:")
    for p in pages:
        logger.info(
            f"    صفحه {p['page_number']:>3} → {p['image_path'].name}"
            f"  ({p['width']}×{p['height']}px)"
        )

    logger.info("")
    return pages


# ══════════════════════════════════════════════════════════════════════
#  مرحله ۲ — OCR
# ══════════════════════════════════════════════════════════════════════

def run_step2(pdf_path: Path, pages: list[dict] | None = None) -> str:
    """
    OCR تصاویر استخراج‌شده با Gemini Flash.

    Args:
        pdf_path: مسیر PDF اصلی
        pages:    اگر None باشد، تصاویر از دیسک بارگذاری می‌شوند.

    Returns:
        متن کامل OCR‌شده
    """
    _banner(f"مرحله ۲ — OCR  |  {pdf_path.name}")

    # اگر pages از مرحله ۱ نیامده، از دیسک می‌خوانیم
    if pages is None:
        image_paths = _find_latest_images(pdf_path.name)
        if not image_paths:
            logger.error(
                f"  ✗ هیچ تصویری برای «{pdf_path.name}» پیدا نشد.\n"
                "    ابتدا مرحله ۱ را اجرا کنید:  python main.py step1 --pdf ..."
            )
            sys.exit(1)

        # ساختن لیست pages از فایل‌های دیسک
        pages = [
            {
                "page_number": int(p.stem.split("_")[1]),
                "image_path":  p,
                "width":       0,
                "height":      0,
            }
            for p in image_paths
        ]
        logger.info(f"  {len(pages)} تصویر از دیسک بارگذاری شد.")

    logger.info(f"  تعداد صفحات برای OCR: {len(pages)}")
    logger.info("")

    ocr_result = GeminiOCR().run(pages, pdf_path.name)
    ocr_text   = ocr_result["full_text"]

    logger.info("")
    logger.info(f"  ✓ OCR کامل شد.")
    logger.info(f"  کل کاراکتر : {len(ocr_text)}")
    logger.info(f"  فایل ذخیره : {ocr_result['saved_txt'].name}")
    logger.info("")

    # پیش‌نمایش ۳۰۰ کاراکتر اول
    preview = ocr_text[:300].replace("\n", " ")
    logger.info(f"  پیش‌نمایش متن:\n  « {preview} … »")
    logger.info("")

    return ocr_text


# ══════════════════════════════════════════════════════════════════════
#  مرحله ۳ — تحلیل آماری
# ══════════════════════════════════════════════════════════════════════

def run_step3(pdf_path: Path, ocr_text: str | None = None) -> dict:
    """
    تحلیل آماری متن با ۴ مدل هوش مصنوعی.

    Args:
        pdf_path: مسیر PDF اصلی
        ocr_text: اگر None باشد، از جدیدترین فایل OCR دیسک خوانده می‌شود.

    Returns:
        دیکشنری نتایج هر مدل
    """
    _banner(f"مرحله ۳ — تحلیل آماری  |  {pdf_path.name}")

    # اگر متن از مرحله ۲ نیامده، از دیسک می‌خوانیم
    if ocr_text is None:
        ocr_file = _find_latest_ocr(pdf_path.name)
        if ocr_file is None:
            logger.error(
                f"  ✗ هیچ فایل OCR برای «{pdf_path.name}» پیدا نشد.\n"
                "    ابتدا مرحله ۲ را اجرا کنید:  python main.py step2 --pdf ..."
            )
            sys.exit(1)
        logger.info(f"  فایل OCR بارگذاری شد: {ocr_file.name}")
        ocr_text = load_text(ocr_file)

    logger.info(f"  طول متن ورودی: {len(ocr_text)} کاراکتر")
    logger.info("")

    results = StatisticalAnalyzer().run(ocr_text, pdf_path.name)

    logger.info("")
    logger.info("  خلاصه نتایج تحلیل:")
    logger.info(f"  {'مدل':<14} {'ارائه‌دهنده':<16} {'وضعیت':<8} {'کاراکتر'}")
    logger.info("  " + "─" * 52)
    for key, data in results.items():
        icon   = "✓" if data["status"] == "ok" else "✗"
        logger.info(
            f"  {icon} {data['model']:<30} {data['provider']:<14}"
            f" {len(data['text'])}"
        )
    logger.info("")
    logger.info(
        f"  نتایج در: outputs/analysis_results/{pdf_path.stem}/"
    )
    logger.info("")

    return results


# ══════════════════════════════════════════════════════════════════════
#  اجرای کامل (هر سه مرحله)
# ══════════════════════════════════════════════════════════════════════

def run_all(pdf_path: Path) -> None:
    """اجرای هر سه مرحله پشت سر هم برای یک PDF."""
    _banner(f"اجرای کامل  |  {pdf_path.name}")
    logger.info("")

    pages    = run_step1(pdf_path)
    ocr_text = run_step2(pdf_path, pages=pages)
    run_step3(pdf_path, ocr_text=ocr_text)

    _banner(f"✓ پردازش کامل انجام شد  |  {pdf_path.name}")


# ══════════════════════════════════════════════════════════════════════
#  پردازش چند PDF
# ══════════════════════════════════════════════════════════════════════

def process_all_pdfs(command: str) -> None:
    """اجرای یک command روی تمام PDFهای موجود در inputs/pdfs/"""
    pdfs = sorted(INPUTS_DIR.glob("*.pdf"))
    if not pdfs:
        logger.warning(
            f"هیچ فایل PDF در {INPUTS_DIR} یافت نشد.\n"
            "فایل‌های PDF را در پوشه inputs/pdfs/ قرار دهید."
        )
        return

    logger.info(f"{len(pdfs)} فایل PDF یافت شد.\n")

    for i, pdf in enumerate(pdfs, start=1):
        logger.info(f"{'▶'*3} [{i}/{len(pdfs)}] {pdf.name}")
        try:
            if command == "step1":
                run_step1(pdf)
            elif command == "step2":
                run_step2(pdf)
            elif command == "step3":
                run_step3(pdf)
            elif command == "all":
                run_all(pdf)
        except Exception as exc:
            logger.error(f"  ✗ خطا در پردازش {pdf.name}: {exc}")
        logger.info("")


# ══════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="تحلیل آماری مقالات دندانپزشکی",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
دستورات:
  step1     استخراج تصاویر از PDF
  step2     OCR تصاویر (با Gemini Flash)
  step3     تحلیل آماری با ۴ مدل AI
  all       هر سه مرحله پشت سر هم

هدف پردازش (یکی را انتخاب کنید):
  --pdf <path>   یک فایل PDF مشخص
  --all-pdfs     تمام PDFهای داخل inputs/pdfs/

مثال‌ها:
  python main.py step1 --pdf inputs/pdfs/article.pdf
  python main.py step2 --pdf inputs/pdfs/article.pdf
  python main.py step3 --pdf inputs/pdfs/article.pdf
  python main.py all   --pdf inputs/pdfs/article.pdf

  python main.py step1 --all-pdfs
  python main.py all   --all-pdfs
        """,
    )

    parser.add_argument(
        "command",
        choices=["step1", "step2", "step3", "all"],
        help="مرحله‌ای که می‌خواهید اجرا کنید",
    )

    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--pdf",
        type=str,
        metavar="PATH",
        help="مسیر یک فایل PDF",
    )
    target.add_argument(
        "--all-pdfs",
        action="store_true",
        help="پردازش تمام PDFهای موجود در inputs/pdfs/",
    )

    return parser


def main() -> None:
    parser = build_parser()

    # نمایش راهنما اگر هیچ آرگومانی داده نشده
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # ── هدف: تمام PDFها ─────────────────────────────────────────────
    if args.all_pdfs:
        process_all_pdfs(args.command)
        return

    # ── هدف: یک PDF مشخص ────────────────────────────────────────────
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"فایل یافت نشد: {pdf_path}")
        sys.exit(1)

    if args.command == "step1":
        run_step1(pdf_path)

    elif args.command == "step2":
        run_step2(pdf_path)

    elif args.command == "step3":
        run_step3(pdf_path)

    elif args.command == "all":
        run_all(pdf_path)


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()