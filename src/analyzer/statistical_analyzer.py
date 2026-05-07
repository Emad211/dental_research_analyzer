import time
from pathlib import Path
from typing import Dict

from openai import OpenAI
from google.genai import types, Client as GeminiClient

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


class StatisticalAnalyzer:
    """
    Statistical analysis using multiple AI models.
    - Gemini models  → Google Gemini SDK (direct)
    - All other models → OpenAI-compatible SDK
    """

    def __init__(self):
        # OpenAI-compatible client (for non-Gemini models)
        self.openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

        # Google Gemini client (for Gemini models)
        self.gemini_client = GeminiClient(
            api_key=API_KEY,
            http_options=types.HttpOptions(base_url="https://api.gapgpt.app/")
        )

        logger.info(
            f"StatisticalAnalyzer ready — {len(ANALYSIS_MODELS)} models configured"
        )

    # ------------------------------------------------------------------
    def _is_gemini(self, model_name: str) -> bool:
        """Check if a model should use the Gemini SDK."""
        return model_name.lower().startswith("gemini")

    # ------------------------------------------------------------------
    def _call_gemini(self, model_name: str, prompt: str) -> str:
        """Send request using Google Gemini SDK."""
        response = self.gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=8192,
            )
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    def _call_openai(self, model_name: str, prompt: str) -> str:
        """Send request using OpenAI-compatible SDK."""
        response = self.openai_client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            max_tokens=8192,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    def _call_model(self, model_name: str, prompt: str) -> str:
        """Route request to the correct SDK based on model name."""
        if self._is_gemini(model_name):
            logger.info(f"    → Using Google Gemini SDK")
            return self._call_gemini(model_name, prompt)
        else:
            logger.info(f"    → Using OpenAI-compatible SDK")
            return self._call_openai(model_name, prompt)

    # ------------------------------------------------------------------
    def run(
        self,
        ocr_text: str,
        pdf_name: str,
        delay: float = 3.0,
    ) -> Dict:
        """
        Run statistical analysis with all configured models.

        Args:
            ocr_text: OCR-extracted text
            pdf_name: Original PDF filename
            delay:    Delay between API calls (seconds)

        Returns:
            Dictionary with results from each model
        """
        prompt  = STATISTICAL_PROMPT.format(ocr_text=ocr_text)
        results: Dict[str, Dict] = {}

        logger.info(f"Starting statistical analysis — {len(ANALYSIS_MODELS)} models")
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
                logger.info(f"  ✓ Received: {len(answer):,} characters")

            except Exception as exc:
                answer = f"[Error: {exc}]"
                status = "error"
                logger.error(f"  ✗ Error: {exc}")

            results[key] = {
                "provider": provider,
                "model":    name,
                "status":   status,
                "text":     answer,
            }

            if idx < len(ANALYSIS_MODELS) - 1:
                time.sleep(delay)

        self._save(results, pdf_name)

        logger.info("─" * 60)
        logger.info("All analyses completed.")
        return results

    # ------------------------------------------------------------------
    def _save(self, results: Dict, pdf_name: str) -> None:
        """Save each model's result + combined report."""
        ts      = timestamp()
        stem    = Path(pdf_name).stem
        out_dir = ANALYSIS_RESULTS_DIR / stem
        out_dir.mkdir(parents=True, exist_ok=True)

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

        save_text(out_dir / f"combined_{ts}.txt",
                  self._build_combined(results, pdf_name, ts))

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

        logger.info(f"Results saved → {out_dir}")

    # ------------------------------------------------------------------
    @staticmethod
    def _build_combined(results: Dict, pdf_name: str, ts: str) -> str:
        """Build a single combined report from all models."""
        sep   = "═" * 70
        parts = [
            sep,
            "COMBINED STATISTICAL ANALYSIS REPORT",
            f"PDF  : {pdf_name}",
            f"Time : {ts}",
            f"Models: {len(results)}",
            sep,
        ]
        for i, (key, data) in enumerate(results.items(), start=1):
            sdk = "Gemini SDK" if data["model"].lower().startswith("gemini") else "OpenAI SDK"
            parts += [
                f"\n{'─'*70}",
                f"MODEL {i}: {data['provider']} — {data['model']}  [{sdk}]",
                f"{'─'*70}\n",
                data["text"],
            ]
        return "\n".join(parts)