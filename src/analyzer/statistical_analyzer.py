import time
from pathlib import Path
from typing import Dict, List

from openai import OpenAI

from config.settings import (
    API_KEY,
    BASE_URL,
    ANALYSIS_MODELS,
    STATISTICAL_PROMPT,
    ANALYSIS_RESULTS_DIR,
)
from src.utils import setup_logger, save_text, save_json, timestamp

logger = setup_logger("StatisticalAnalyzer")


class StatisticalAnalyzer:
    """
    تحلیل آماری متن OCR‌شده با چند مدل هوش مصنوعی
    از طریق یک کلاینت OpenAI-compatible واحد.
    """

    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        logger.info(
            f"StatisticalAnalyzer آماده — {len(ANALYSIS_MODELS)} مدل تعریف شده"
        )

    # ------------------------------------------------------------------
    def _call_model(self, model_name: str, prompt: str) -> str:
        """ارسال درخواست به یک مدل و دریافت پاسخ."""
        response = self.client.chat.completions.create(
            model=model_name,
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
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    def run(
        self,
        ocr_text: str,
        pdf_name: str,
        delay: float = 3.0,
    ) -> Dict:
        """
        اجرای تحلیل آماری با تمام مدل‌های تعریف‌شده.

        Args:
            ocr_text: متن استخراج‌شده توسط OCR
            pdf_name: نام فایل PDF (برای نام‌گذاری خروجی)
            delay:    تاخیر بین درخواست‌ها (ثانیه)

        Returns:
            دیکشنری شامل نتیجه هر مدل
        """
        prompt  = STATISTICAL_PROMPT.format(ocr_text=ocr_text)
        results: Dict[str, Dict] = {}

        logger.info(f"شروع تحلیل آماری — {len(ANALYSIS_MODELS)} مدل")
        logger.info("─" * 60)

        for idx, model_cfg in enumerate(ANALYSIS_MODELS):
            key      = model_cfg["key"]
            name     = model_cfg["name"]
            provider = model_cfg["provider"]

            logger.info(
                f"[{idx+1}/{len(ANALYSIS_MODELS)}] {provider} — {name}"
            )

            try:
                answer = self._call_model(name, prompt)
                status = "ok"
                logger.info(f"  ✓ دریافت شد: {len(answer)} کاراکتر")
            except Exception as exc:
                answer = f"[خطا: {exc}]"
                status = "error"
                logger.error(f"  ✗ خطا: {exc}")

            results[key] = {
                "provider": provider,
                "model":    name,
                "status":   status,
                "text":     answer,
            }

            if idx < len(ANALYSIS_MODELS) - 1:
                time.sleep(delay)

        # ── ذخیره ──────────────────────────────────────────────────────
        self._save(results, pdf_name)

        logger.info("─" * 60)
        logger.info("تمام تحلیل‌ها کامل شدند.")
        return results

    # ------------------------------------------------------------------
    def _save(self, results: Dict, pdf_name: str) -> None:
        """ذخیره نتایج هر مدل + گزارش ترکیبی."""
        ts       = timestamp()
        stem     = Path(pdf_name).stem
        out_dir  = ANALYSIS_RESULTS_DIR / stem
        out_dir.mkdir(parents=True, exist_ok=True)

        # فایل جداگانه برای هر مدل
        for key, data in results.items():
            header = (
                f"{'═'*70}\n"
                f"STATISTICAL ANALYSIS — {data['provider']} / {data['model']}\n"
                f"PDF : {pdf_name}\n"
                f"Time: {ts}\n"
                f"{'═'*70}\n\n"
            )
            save_text(out_dir / f"{key}_{ts}.txt", header + data["text"])

        # گزارش ترکیبی
        combined = self._build_combined(results, pdf_name, ts)
        save_text(out_dir / f"combined_{ts}.txt", combined)

        # متادیتا JSON
        save_json(
            out_dir / f"metadata_{ts}.json",
            {
                "pdf_name":  pdf_name,
                "timestamp": ts,
                "models": {
                    k: {
                        "provider": v["provider"],
                        "model":    v["model"],
                        "status":   v["status"],
                        "chars":    len(v["text"]),
                    }
                    for k, v in results.items()
                },
            },
        )

        logger.info(f"نتایج ذخیره شدند → {out_dir}")

    # ------------------------------------------------------------------
    @staticmethod
    def _build_combined(results: Dict, pdf_name: str, ts: str) -> str:
        """ساخت گزارش یکپارچه از تمام مدل‌ها."""
        sep = "═" * 70
        parts = [
            sep,
            "COMBINED STATISTICAL ANALYSIS REPORT",
            f"PDF : {pdf_name}",
            f"Time: {ts}",
            f"Models: {len(results)}",
            sep,
        ]
        for i, (key, data) in enumerate(results.items(), start=1):
            parts += [
                f"\n{'─'*70}",
                f"MODEL {i}: {data['provider']} — {data['model']}",
                f"{'─'*70}\n",
                data["text"],
            ]
        return "\n".join(parts)