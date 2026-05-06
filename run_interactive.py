"""
run_interactive.py — Interactive PDF processor

Select PDF from list instead of typing filename
"""

import sys
from pathlib import Path
from config.settings import INPUTS_DIR

def select_pdf() -> Path | None:
    """Let user select a PDF from list."""
    pdfs = sorted(INPUTS_DIR.glob("*.pdf"))
    
    if not pdfs:
        print(f"No PDF files found in {INPUTS_DIR}")
        return None
    
    print("="*60)
    print("Available PDF files:")
    print("="*60)
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"{i:>2}. {pdf.name}")
    
    print()
    print("0. Cancel")
    print()
    
    while True:
        try:
            choice = input("Select PDF number: ").strip()
            
            if choice == "0":
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(pdfs):
                return pdfs[idx]
            else:
                print("Invalid number. Try again.")
        
        except (ValueError, KeyboardInterrupt):
            return None


def select_step() -> str | None:
    """Let user select processing step."""
    steps = {
        "1": ("step1", "Extract images from PDF"),
        "2": ("step2", "OCR images"),
        "3": ("step3", "Statistical analysis"),
        "4": ("all",   "Run all steps"),
    }
    
    print()
    print("="*60)
    print("Processing steps:")
    print("="*60)
    
    for key, (cmd, desc) in steps.items():
        print(f"{key}. {desc} ({cmd})")
    
    print()
    print("0. Cancel")
    print()
    
    while True:
        try:
            choice = input("Select step: ").strip()
            
            if choice == "0":
                return None
            
            if choice in steps:
                return steps[choice][0]
            else:
                print("Invalid choice. Try again.")
        
        except (ValueError, KeyboardInterrupt):
            return None


def main():
    print()
    print("╔" + "═"*58 + "╗")
    print("║" + " Interactive PDF Processor".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    print()
    
    # Select PDF
    pdf = select_pdf()
    if pdf is None:
        print("\nCancelled.")
        return
    
    print()
    print(f"Selected: {pdf.name}")
    
    # Select step
    step = select_step()
    if step is None:
        print("\nCancelled.")
        return
    
    print()
    print(f"Running: python main.py {step} --pdf \"{pdf}\"")
    print()
    print("="*60)
    print()
    
    # Run main.py
    import subprocess
    subprocess.run([
        sys.executable,
        "main.py",
        step,
        "--pdf",
        str(pdf)
    ])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")