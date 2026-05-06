"""
rename_pdfs.py — Clean PDF filenames

Removes spaces, special characters, and ' - Copy' from filenames
"""

import re
from pathlib import Path

def clean_filename(name: str) -> str:
    """Clean a filename by removing problematic characters."""
    # Remove ' - Copy' or '-Copy'
    name = re.sub(r'\s*-?\s*Copy\s*', '', name, flags=re.IGNORECASE)
    
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name


def rename_pdfs(directory: Path) -> None:
    """Rename all PDFs in directory to clean names."""
    pdfs = list(directory.glob("*.pdf"))
    
    if not pdfs:
        print(f"No PDF files found in {directory}")
        return
    
    print(f"Found {len(pdfs)} PDF files\n")
    
    for pdf in pdfs:
        # Get clean name
        clean_name = clean_filename(pdf.stem) + pdf.suffix
        new_path = pdf.parent / clean_name
        
        # Skip if already clean
        if pdf.name == clean_name:
            print(f"✓ Already clean: {pdf.name}")
            continue
        
        # Check if target exists
        if new_path.exists():
            print(f"✗ Conflict: {pdf.name}")
            print(f"  Target already exists: {clean_name}")
            continue
        
        # Rename
        try:
            pdf.rename(new_path)
            print(f"✓ Renamed:")
            print(f"  From: {pdf.name}")
            print(f"  To:   {clean_name}")
        except Exception as e:
            print(f"✗ Error renaming {pdf.name}: {e}")
        
        print()


if __name__ == "__main__":
    from config.settings import INPUTS_DIR
    
    print("="*60)
    print("PDF Filename Cleaner")
    print("="*60)
    print()
    
    rename_pdfs(INPUTS_DIR)
    
    print("="*60)
    print("Done!")
    print("="*60)