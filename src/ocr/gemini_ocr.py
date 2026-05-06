import time
from pathlib import Path
from typing import List, Dict

from openai import OpenAI
from PIL import Image
import base64
import io

from config.settings import API_KEY, BASE_URL, OCR_MODEL, OCR_RESULTS_DIR
from src.utils import setup_logger, save_text, save_json, timestamp

logger = setup_logger("GeminiOCR")

# ── پرامپت OCR ───────────────────────────────────────────────────────
_OCR_PROMPT = """\
Perform complete and accurate OCR on this image.

Rules:
1. Extract ALL visible text, preserving original structure and order.
2. Keep paragraph breaks and section headers intact.
3. Reproduce numbers, statistics, and special characters exactly.
4. Mark any masked/blacked-out area as [REDACTED].
5. Render table content with aligned columns when possible.
6. Output ONLY the extracted text — no commentary, no preamble.
"""


def _image_to_base64(image_path: Path) -> str:
    """تبدیل تصویر به رشته base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class GeminiOCR:
    """OCR صفحات PDF با مدل Gemini از طریق OpenAI-compatible API."""

    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        logger.info(f"GeminiOCR آماده — مدل: {OCR_MODEL}")

    # ------------------------------------------------------------------
    def _ocr_page(self, image_path: Path) -> str:
        """OCR یک صفحه و برگرداندن متن آن."""
        b64 = _image_to_base64(image_path)

        response = self.client.chat.completions.create(
            model=OCR_MODEL,
            temperature=0.1,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": _OCR_PROMPT,
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    def run(
        self,
        pages: List[Dict],
        pdf_name: str,
        delay: float = 2.0,
    ) -> Dict:
        """
        OCR تمام صفحات و ذخیره نتایج.

        Args:
            pages:    خروجی PDFExtractor.extract()
            pdf_name: نام فایل PDF (برای نام‌گذاری خروجی)
            delay:    تاخیر بین درخواست‌ها (ثانیه)

        Returns:
            دیکشنری شامل:
              full_text  — کل متن به‌هم‌پیوسته
              pages      — متن هر صفحه به‌تنها
              saved_txt  — مسیر فایل متنی ذخیره‌شده
        """
        total = len(pages)
        logger.info(f"شروع OCR — {total} صفحه از «{pdf_name}»")

        page_texts: Dict[int, str] = {}
        blocks: List[str] = []

        for idx, page_info in enumerate(pages):
            page_num  = page_info["page_number"]
            img_path  = page_info["image_path"]

            logger.info(f"  OCR صفحه {page_num}/{total}: {img_path.name}")

            try:
                text = self._ocr_page(img_path)
            except Exception as exc:
                text = f"[خطا در OCR این صفحه: {exc}]"
                logger.error(f"  ✗ صفحه {page_num}: {exc}")
            else:
                logger.info(f"  ✓ صفحه {page_num}: {len(text)} کاراکتر")

            page_texts[page_num] = text
            blocks.append(
                f"\n{'═'*60}\n"
                f"PAGE {page_num}\n"
                f"{'═'*60}\n"
                f"{text}"
            )

            if idx < total - 1:
                time.sleep(delay)

        full_text = "\n".join(blocks)

        # ── ذخیره ──────────────────────────────────────────────────────
        ts       = timestamp()
        stem     = Path(pdf_name).stem
        txt_path = OCR_RESULTS_DIR / f"{stem}_ocr_{ts}.txt"
        save_text(txt_path, full_text)

        meta_path = OCR_RESULTS_DIR / f"{stem}_ocr_meta_{ts}.json"
        save_json(
            meta_path,
            {
                "pdf_name":    pdf_name,
                "total_pages": total,
                "total_chars": len(full_text),
                "pages": {
                    str(p): len(t) for p, t in page_texts.items()
                },
            },
        )

        logger.info(
            f"OCR تمام شد — {len(full_text)} کاراکتر کل\n"
            f"  متن   → {txt_path}\n"
            f"  متادیتا → {meta_path}"
        )

        return {
            "full_text": full_text,
            "pages":     page_texts,
            "saved_txt": txt_path,
        }