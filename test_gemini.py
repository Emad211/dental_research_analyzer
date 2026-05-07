"""
test_gemini.py — Find working Gemini models on gapgpt.app
"""

import time
from openai import OpenAI
from google.genai import types, Client as GeminiClient
from config.settings import API_KEY, BASE_URL

MODELS_TO_TEST = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]

# ── Test via OpenAI SDK ───────────────────────────────────────────────
def test_openai_sdk(models: list) -> list:
    client  = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    working = []

    print("\n" + "="*60)
    print("METHOD 1: OpenAI-compatible SDK")
    print("="*60)

    for model in models:
        print(f"  {model:<35} ... ", end="", flush=True)
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.1,
                max_tokens=20,
                timeout=20,
                messages=[{"role": "user", "content": "Say OK"}],
            )
            answer = response.choices[0].message.content.strip()[:30]
            print(f"✓  {answer}")
            working.append(("openai_sdk", model))
        except Exception as e:
            print(f"✗  {str(e)[:60]}")
        time.sleep(1)

    return working


# ── Test via Google Gemini SDK ────────────────────────────────────────
def test_gemini_sdk(models: list) -> list:
    working = []

    print("\n" + "="*60)
    print("METHOD 2: Google Gemini SDK")
    print("="*60)

    try:
        client = GeminiClient(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                base_url="https://api.gapgpt.app/"
            )
        )
    except Exception as e:
        print(f"  ✗ Could not create Gemini client: {e}")
        return working

    for model in models:
        print(f"  {model:<35} ... ", end="", flush=True)
        try:
            response = client.models.generate_content(
                model=model,
                contents="Say OK",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=20,
                )
            )
            answer = response.text.strip()[:30]
            print(f"✓  {answer}")
            working.append(("gemini_sdk", model))
        except Exception as e:
            print(f"✗  {str(e)[:60]}")
        time.sleep(1)

    return working


# ── Main ──────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("Gemini Model Finder — gapgpt.app")
    print("="*60)
    print(f"API Base URL : {BASE_URL}")
    print(f"Models to test: {len(MODELS_TO_TEST)}")

    working_openai = test_openai_sdk(MODELS_TO_TEST)
    working_gemini = test_gemini_sdk(MODELS_TO_TEST)

    all_working = working_openai + working_gemini

    print("\n" + "="*60)
    print("RESULTS — Working Models")
    print("="*60)

    if not all_working:
        print("  ✗ No working Gemini models found.")
        print("  → Check your API_KEY and internet connection.")
    else:
        for sdk, model in all_working:
            print(f"  ✓  [{sdk}]  {model}")

        print()
        print("─"*60)
        print("Recommended config/settings.py entry:")
        print("─"*60)
        best_sdk, best_model = all_working[0]
        print(f"""
    {{
        "key":      "{best_model.replace('.', '-')}",
        "name":     "{best_model}",
        "provider": "Google",
    }},
        """)

    print("="*60)


if __name__ == "__main__":
    main()