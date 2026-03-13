"""
propra/data/bulk_extract.py
────────────────────────────────────────────────────────────────────────────
Bulk PDF extraction for all LBO source files.

Runs extract_pdf_clean.py on every PDF in propra/data/raw/ that does not already
have a corresponding .txt file in propra/data/txt/. Skips files that are already extracted.

Usage:
    python propra/data/bulk_extract.py
    python propra/data/bulk_extract.py --force   # re-extract even if .txt exists
"""

import sys
import argparse
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RAW_DIR = Path("propra/data/raw")
TXT_DIR = Path("propra/data/txt")
EXTRACTOR = Path("propra/data/extract_pdf_clean.py")

PDFS = [
    "BauO_BE.pdf",
    "BauO_HE.pdf",
    "BauO_LSA.pdf",
    "BauO_MV.pdf",
    "BauO_NRW.pdf",
    "BayBO.pdf",
    "BbgBO.pdf",
    "LBO_HB.pdf",
    "HBauO.pdf",
    "LBauO_RLP.pdf",
    "LBO_SH.pdf",
    "LBO_SL.pdf",
    "NBauO.pdf",
    "SaechsBO.pdf",
    "ThuerBO.pdf",
]


def main():
    parser = argparse.ArgumentParser(description="Bulk extract all LBO PDFs to .txt")
    parser.add_argument("--force", action="store_true", help="Re-extract even if .txt exists")
    args = parser.parse_args()

    print("=" * 60)
    print("Bulk LBO PDF Extraction")
    print("=" * 60)

    skipped = []
    success = []
    failed = []

    for pdf_name in PDFS:
        pdf_path = RAW_DIR / pdf_name
        txt_path = TXT_DIR / Path(pdf_name).with_suffix(".txt").name

        if not pdf_path.exists():
            print(f"\nERR  {pdf_name} not found in {RAW_DIR} -- skipping")
            failed.append(pdf_name)
            continue

        if txt_path.exists() and not args.force:
            print(f"SKIP {pdf_name} -- {txt_path.name} already exists")
            skipped.append(pdf_name)
            continue

        TXT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nExtracting {pdf_name} ...")

        result = subprocess.run(
            [sys.executable, str(EXTRACTOR), str(pdf_path), str(txt_path)]
        )

        if result.returncode == 0:
            print(f"  OK   {pdf_name} done")
            success.append(pdf_name)
        else:
            print(f"  ERR  {pdf_name} failed with return code {result.returncode}")
            failed.append(pdf_name)

    print("\n" + "=" * 60)
    print(f"Done: {len(success)} extracted, {len(skipped)} skipped, {len(failed)} failed")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print("=" * 60)
    print("\nNext step: python propra/data/bulk_inventory.py --dry_run")


if __name__ == "__main__":
    main()