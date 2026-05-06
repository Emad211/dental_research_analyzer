import io
from pathlib import Path
from typing import List, Dict

import fitz  # PyMuPDF
from PIL import Image

from config.settings import IMAGE_DPI, IMAGE_FORMAT, IMAGES_DIR
from src.utils import setup_logger

logger = setup_logger("PDFExtractor")


class PDFExtractor:
    """استخراج صفحات PDF به‌صورت تصویر با کیفیت بالا."""

    def __init__(self, dpi: int = IMAGE_DPI):
        self.dpi = dpi
        self.zoom = dpi / 72  # فاکتور بزرگ‌نمایی

    # ------------------------------------------------------------------
    def extract(self, pdf_path: Path) -> List[Dict]:
        """
        تبدیل تمام صفحات PDF به تصویر PNG.

        Returns:
            لیستی از دیکشنری با کلیدهای:
            page_number, image_path, width, height
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"فایل یافت نشد: {pdf_path}")

        out_dir = IMAGES_DIR / pdf_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        results: List[Dict] = []
        doc = fitz.open(str(pdf_path))
        total = len(doc)

        logger.info(f"PDF باز شد: «{pdf_path.name}» — {total} صفحه")

        matrix = fitz.Matrix(self.zoom, self.zoom)

        for i, page in enumerate(doc, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pixmap.tobytes("png")))

            filename = f"page_{i:03d}.{IMAGE_FORMAT.lower()}"
            img_path = out_dir / filename
            img.save(str(img_path), format=IMAGE_FORMAT)

            results.append(
                {
                    "page_number": i,
                    "image_path": img_path,
                    "width": img.width,
                    "height": img.height,
                }
            )
            logger.info(
                f"  صفحه {i:>3}/{total} ذخیره شد → {filename}"
                f"  ({img.width}×{img.height}px)"
            )

        doc.close()
        logger.info(f"استخراج تمام شد. تصاویر در: {out_dir}")
        return results

    # ------------------------------------------------------------------
    def pdf_info(self, pdf_path: Path) -> Dict:
        """اطلاعات کلی فایل PDF."""
        pdf_path = Path(pdf_path)
        doc = fitz.open(str(pdf_path))
        meta = doc.metadata
        info = {
            "filename":    pdf_path.name,
            "pages":       len(doc),
            "title":       meta.get("title", "—"),
            "author":      meta.get("author", "—"),
            "size_mb":     round(pdf_path.stat().st_size / 1_048_576, 2),
        }
        doc.close()
        return info