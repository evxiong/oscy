"""
Script for exporting data to `data/oscars.csv`.

Usage:
    python -m src.oscy.export
"""

from . import db

if __name__ == "__main__":
    db.export_nominations_to_csv()
