import re
import time
from pathlib import Path
from typing import Dict, Optional

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

_SYSTEM_PROMPT = (
    "You are an expert biostatistician specializing "
    "in dental and clinical research methodology."
)


def _normalize_name(s: str) -> str:
    """
    نرمال‌سازی برای match کردن اسم پوشه‌ها با stem:
    - lower
    - حذف فاصله/underscore/dash
    - نگه داشتن فقط a-z0-9 و نقطه (چون توی stemهایی مثل JOCPD45.3.3 مهمه)
    """
    s = s.lower().strip()
    s = s.replace(" ", "").replace("_", "").replace("-", "")
    s = re.sub(r"[^a-z0-9.]+", "", s)
    return s


class StatisticalAnalyzer:
    """
    همه مدل‌ها از طریق OpenAI-compatible SDK صدا زده می‌شوند.
    همچنین:
      - پوشه جدید ساخته نمی‌شود (فقط همان پوشه موجود برای PDF استفاده می‌شود)
      - combined جدید ساخته نمی‌شود (combined موجود append می‌شود)
    """

    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        logger.info(f"StatisticalAnalyzer ready — {len(ANALYSIS_MODELS)} models configured")

    # ------------------------------------------------------------------
    def _call_model(self, model_name: str, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            max_tokens=8192,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    def _resolve_existing_out_dir(self, pdf_name: str) -> Path:
        """
        دقیقاً پوشه‌ای را پیدا می‌کند که قبلاً برای این PDF ساخته شده.
        هیچ پوشه‌ی جدیدی ساخته نمی‌شود.
        """
        stem = Path(pdf_name).stem

        # 1) بهترین حالت: پوشه دقیقاً همنام stem
        direct = ANALYSIS_RESULTS_DIR / stem
        if direct.exists() and direct.is_dir():
            return direct

        # 2) fallback: case-insensitive + normalize match
        wanted = _normalize_name(stem)
        candidates = []
        for d in ANALYSIS_RESULTS_DIR.iterdir():
            if d.is_dir() and _normalize_name(d.name) == wanted:
                candidates.append(d)

        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            # اگر چندتا بود، جدیدترین پوشه (mtime) را انتخاب می‌کنیم
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            logger.warning(
                "Multiple matching output directories found; using the most recently modified: "
                f"{candidates[0].name}"
            )
            return candidates[0]

        # 3) اگر پیدا نشد: طبق درخواست تو، پوشه جدید نمی‌سازیم → خطا می‌دهیم
        raise FileNotFoundError(
            "No existing analysis_results folder found for this PDF.\n"
            f"Expected something like: {direct}\n"
            "طبق تنظیمات فعلی شما، قرار است پوشه از قبل وجود داشته باشد "
            "(مثلاً خروجی مدل‌های قبلی)."
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _latest_file(out_dir: Path, pattern: str) -> Optional[Path]:
        files = sorted(out_dir.glob(pattern))
        return files[-1] if files else None

    # ------------------------------------------------------------------
    @staticmethod
    def _next_model_index(combined_text: str) -> int:
        """
        بزرگترین شماره MODEL را از داخل combined پیدا می‌کند.
        اگر نبود، از 1 شروع می‌کند.
        """
        nums = [int(m.group(1)) for m in re.finditer(r"\bMODEL\s+(\d+)\s*:", combined_text)]
        return (max(nums) + 1) if nums else 1

    # ------------------------------------------------------------------
    def run(self, ocr_text: str, pdf_name: str, delay: float = 3.0) -> Dict:
        prompt = STATISTICAL_PROMPT.format(ocr_text=ocr_text)
        results: Dict[str, Dict] = {}

        logger.info(f"Starting statistical analysis — {len(ANALYSIS_MODELS)} models")
        logger.info("─" * 60)

        for idx, model_cfg in enumerate(ANALYSIS_MODELS):
            key = model_cfg["key"]
            name = model_cfg["name"]
            provider = model_cfg["provider"]

            logger.info(f"[{idx+1}/{len(ANALYSIS_MODELS)}] {provider} — {name}")
            logger.info("    → Using OpenAI-compatible SDK")

            try:
                answer = self._call_model(name, prompt)
                status = "ok"
                logger.info(f"  ✓ Received: {len(answer):,} characters")
            except Exception as exc:
                answer = f"[Error: {exc}]"
                status = "error"
                logger.error(f"  ✗ Error: {exc}")

            results[key] = {
                "provider": provider,
                "model": name,
                "status": status,
                "text": answer,
            }

            if idx < len(ANALYSIS_MODELS) - 1:
                time.sleep(delay)

        self._save(results, pdf_name)
        logger.info("─" * 60)
        logger.info("All analyses completed.")
        return results

    # ------------------------------------------------------------------
    def _save(self, results: Dict, pdf_name: str) -> None:
        ts = timestamp()

        # ✅ مهم: پوشه را از قبل موجود پیدا کن؛ پوشه جدید نساز
        out_dir = self._resolve_existing_out_dir(pdf_name)

        # 1) ذخیره خروجی مدل جدید (این فایل‌ها طبیعی است که جدید باشند)
        for key, data in results.items():
            header = (
                f"{'═'*70}\n"
                f"STATISTICAL ANALYSIS — {data['provider']} / {data['model']}\n"
                f"PDF    : {pdf_name}\n"
                f"Status : {data['status']}\n"
                f"Time   : {ts}\n"
                f"{'═'*70}\n\n"
            )
            save_text(out_dir / f"{key}_{ts}.txt", header + data["text"])

        # 2) combined: اگر موجود است، همان را append کن؛ combined جدید نساز
        combined_path = self._latest_file(out_dir, "combined_*.txt")
        if combined_path is None:
            # اگر واقعاً هیچ combinedای وجود ندارد، اولین combined را می‌سازیم (به ناچار)
            combined_path = out_dir / f"combined_{ts}.txt"
            initial = (
                f"{'═'*70}\n"
                f"COMBINED STATISTICAL ANALYSIS REPORT\n"
                f"PDF  : {pdf_name}\n"
                f"Created: {ts}\n"
                f"{'═'*70}\n"
            )
            save_text(combined_path, initial)

        combined_text = combined_path.read_text(encoding="utf-8")
        model_index = self._next_model_index(combined_text)

        blocks = []
        for _, data in results.items():
            blocks.append(
                "\n" +
                ("─" * 70) + "\n" +
                f"MODEL {model_index}: {data['provider']} — {data['model']}  [OpenAI-compatible SDK]\n"
                f"RUN  : {ts}\n" +
                ("─" * 70) + "\n\n" +
                data["text"].strip() + "\n"
            )
            model_index += 1

        with combined_path.open("a", encoding="utf-8") as f:
            f.write("".join(blocks))

        # 3) metadata (اختیاری): من همچنان metadata جدید می‌سازم چون گفتی فقط combined جدید نساز.
        # اگر خواستی این هم "آپدیت" شود و فایل جدید نسازد، بگو تا همان فایل metadata موجود را هم merge کنم.
        save_json(
            out_dir / f"metadata_{ts}.json",
            {
                "pdf_name": pdf_name,
                "timestamp": ts,
                "models": {
                    k: {
                        "provider": v["provider"],
                        "model": v["model"],
                        "status": v["status"],
                        "chars": len(v["text"]),
                    }
                    for k, v in results.items()
                },
            },
        )

        logger.info(f"Results saved → {out_dir}")
        logger.info(f"Combined updated → {combined_path.name}")