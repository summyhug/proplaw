"""
propra/data/bulk_inventory.py
────────────────────────────────────────────────────────────────────────────
Bulk node inventory drafting for all LBO .txt files.

Runs draft_inventory.py on every .txt file that does not already have a
corresponding _node_inventory.md. Skips files already inventoried.

Usage:
    python propra/data/bulk_inventory.py
    python propra/data/bulk_inventory.py --dry_run   # parse only, no API calls
    python propra/data/bulk_inventory.py --force      # re-draft even if .md exists
    python propra/data/bulk_inventory.py --only BauO_BE  # single state
"""

import sys
import argparse
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RAW_DIR  = Path("propra/data/raw")
DATA_DIR = Path("propra/data")
DRAFTER  = Path("propra/data/draft_inventory.py")

# Metadata per LBO — must match exact .txt filename stem
LBO_METADATA = {
    "BauO_BE": {
        "bundesland":   "Berlin",
        "lbo_code":     "BauO_BE",
        "jurisdiction": "DE-BE",
        "version_date": "2021",
        "source_url":   "https://gesetze.berlin.de/bsbe/document/jlr-BauOBErahmen",
    },
    "BauO_HE": {
        "bundesland":   "Hessen",
        "lbo_code":     "BauO_HE",
        "jurisdiction": "DE-HE",
        "version_date": "2024",
        "source_url":   "https://www.rv.hessenrecht.hessen.de",
    },
    "BauO_LSA": {
        "bundesland":   "Sachsen-Anhalt",
        "lbo_code":     "BauO_LSA",
        "jurisdiction": "DE-ST",
        "version_date": "2024",
        "source_url":   "https://www.landesrecht.sachsen-anhalt.de",
    },
    "BauO_MV": {
        "bundesland":   "Mecklenburg-Vorpommern",
        "lbo_code":     "BauO_MV",
        "jurisdiction": "DE-MV",
        "version_date": "2024",
        "source_url":   "https://www.landesrecht-mv.de",
    },
    "BauO_NRW": {
        "bundesland":   "Nordrhein-Westfalen",
        "lbo_code":     "BauO_NRW",
        "jurisdiction": "DE-NW",
        "version_date": "2024",
        "source_url":   "https://recht.nrw.de",
    },
    "BayBO": {
        "bundesland":   "Bayern",
        "lbo_code":     "BayBO",
        "jurisdiction": "DE-BY",
        "version_date": "23. Dezember 2025",
        "source_url":   "https://www.gesetze-bayern.de/Content/Document/BayBO",
    },
    "BbgBO": {
        "bundesland":   "Brandenburg",
        "lbo_code":     "BbgBO",
        "jurisdiction": "DE-BB",
        "version_date": "2024",
        "source_url":   "https://bravors.brandenburg.de/gesetze/bbgbo",
    },
    "BW_LBO2026": {
        "bundesland":   "Baden-Wuerttemberg",
        "lbo_code":     "LBO_BW",
        "jurisdiction": "DE-BW",
        "version_date": "10. Februar 2026",
        "source_url":   "https://www.landesrecht-bw.de",
    },
    "LBO_HB": {
        "bundesland":   "Bremen",
        "lbo_code":     "BremLBO",
        "jurisdiction": "DE-HB",
        "version_date": "2024",
        "source_url":   "https://www.transparenz.bremen.de",
    },
    "HBauO": {
        "bundesland":   "Hamburg",
        "lbo_code":     "HBauO",
        "jurisdiction": "DE-HH",
        "version_date": "2024",
        "source_url":   "https://www.landesrecht-hamburg.de",
    },
    "LBauO_RLP": {
        "bundesland":   "Rheinland-Pfalz",
        "lbo_code":     "LBauO_RLP",
        "jurisdiction": "DE-RP",
        "version_date": "19. November 2025",
        "source_url":   "https://landesrecht.rlp.de/bsrp/document/jlr-BauORPrahmen",
    },
    "LBO_SH": {
        "bundesland":   "Schleswig-Holstein",
        "lbo_code":     "LBO_SH",
        "jurisdiction": "DE-SH",
        "version_date": "2024",
        "source_url":   "https://www.gesetze-rechtsprechung.sh.juris.de",
    },
    "LBO_SL": {
        "bundesland":   "Saarland",
        "lbo_code":     "LBO_SL",
        "jurisdiction": "DE-SL",
        "version_date": "2024",
        "source_url":   "https://recht.saarland.de",
    },
    "NBauO": {
        "bundesland":   "Niedersachsen",
        "lbo_code":     "NBauO",
        "jurisdiction": "DE-NI",
        "version_date": "2024",
        "source_url":   "https://www.nds-voris.de",
    },
    "SaechsBO": {
        "bundesland":   "Sachsen",
        "lbo_code":     "SaechsBO",
        "jurisdiction": "DE-SN",
        "version_date": "2024",
        "source_url":   "https://www.revosax.sachsen.de",
    },
    "ThuerBO": {
        "bundesland":   "Thueringen",
        "lbo_code":     "ThuerBO",
        "jurisdiction": "DE-TH",
        "version_date": "2024",
        "source_url":   "https://landesrecht.thueringen.de",
    },
    "MBO": {
        "bundesland":   "Bund",
        "lbo_code":     "MBO",
        "jurisdiction": "DE",
        "version_date": "2023",
        "source_url":   "https://www.bauministerkonferenz.de",
    },
}

# BW is already manually inventoried — skip by default
SKIP_BY_DEFAULT = {"BW_LBO2026"}


def main():
    parser = argparse.ArgumentParser(description="Bulk draft node inventories for all LBOs.")
    parser.add_argument("--dry_run", action="store_true", help="Parse only, no API calls")
    parser.add_argument("--force",   action="store_true", help="Re-draft even if .md exists")
    parser.add_argument("--only",    type=str, default="",  help="Process only this stem (e.g. BauO_BE)")
    args = parser.parse_args()

    print("=" * 60)
    print("Bulk LBO Node Inventory Drafting")
    if args.dry_run:
        print("[DRY RUN MODE]")
    print("=" * 60)

    txt_files = sorted(RAW_DIR.glob("*.txt"))

    if args.only:
        txt_files = [f for f in txt_files if f.stem == args.only]
        if not txt_files:
            print(f"ERR  No .txt found for stem '{args.only}'")
            sys.exit(1)

    skipped = []
    success = []
    failed  = []

    for txt_path in txt_files:
        stem = txt_path.stem  # e.g. "BauO_BE"

        if stem in SKIP_BY_DEFAULT and not args.force:
            print(f"SKIP {stem} — manually inventoried (use --force to override)")
            skipped.append(stem)
            continue

        if stem not in LBO_METADATA:
            print(f"WARN {stem} — no metadata defined in LBO_METADATA, skipping")
            skipped.append(stem)
            continue

        meta = LBO_METADATA[stem]
        out_path = DATA_DIR / f"{meta['lbo_code']}_node_inventory.md"

        if out_path.exists() and not args.force and not args.dry_run:
            print(f"SKIP {stem} — {out_path.name} already exists")
            skipped.append(stem)
            continue

        print(f"\nDrafting {stem} ({meta['bundesland']}) ...")

        cmd = [
            sys.executable, str(DRAFTER),
            "--txt",          str(txt_path),
            "--bundesland",   meta["bundesland"],
            "--lbo_code",     meta["lbo_code"],
            "--jurisdiction", meta["jurisdiction"],
            "--version_date", meta["version_date"],
            "--source_url",   meta["source_url"],
            "--output",       str(out_path),
        ]
        if args.dry_run:
            cmd.append("--dry_run")

        result = subprocess.run(
            cmd,
            capture_output=False,  # stream output live
            text=True,
            encoding="utf-8",
        )

        if result.returncode == 0:
            success.append(stem)
        else:
            print(f"  ERR  {stem} failed")
            failed.append(stem)

    print("\n" + "=" * 60)
    print(f"Done: {len(success)} drafted, {len(skipped)} skipped, {len(failed)} failed")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()