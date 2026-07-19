"""Build a compact, indexed SQLite lookup database from the geocoded parcel CSV.

The source CSV (output.csv) is ~226MB with ~120 columns. The web service only
needs a handful of fields to answer geocoding queries, so this script streams the
CSV in chunks and writes a small `parcels` table with indexes on parcel ID and a
normalized address, turning multi-second scans into sub-millisecond queries.
"""

import argparse
import sqlite3
import pandas as pd

# Columns pulled from the source CSV. Everything else is dropped.
SOURCE_COLUMNS = [
    "TAXPINNO",
    "LOC_NBR",
    "LOC_DIR",
    "LOC_STREET",
    "LOC_SUFFIX",
    "LOC_ZIP",
    "latitude",
    "longitude",
]

CHUNK_SIZE = 50_000


def build_full_address(row):
    """Combine address components into a single normalized (upper-case) string."""
    components = []
    if pd.notna(row.get("LOC_NBR")):
        # Convert to int to drop the trailing ".0" pandas adds to numeric columns.
        components.append(str(int(row["LOC_NBR"])))
    if pd.notna(row.get("LOC_DIR")):
        components.append(str(row["LOC_DIR"]))
    if pd.notna(row.get("LOC_STREET")):
        components.append(str(row["LOC_STREET"]))
    if pd.notna(row.get("LOC_SUFFIX")):
        components.append(str(row["LOC_SUFFIX"]))
    return " ".join(components).upper()


def build_index(input_csv, db_file):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS parcels")
    cur.execute(
        """
        CREATE TABLE parcels (
            parcel_id    TEXT,
            full_address TEXT,
            zip          TEXT,
            latitude     REAL,
            longitude    REAL
        )
        """
    )
    conn.commit()

    total = 0
    reader = pd.read_csv(
        input_csv,
        usecols=SOURCE_COLUMNS,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )
    for chunk in reader:
        chunk = chunk.dropna(subset=["latitude", "longitude"])
        chunk["full_address"] = chunk.apply(build_full_address, axis=1)
        chunk["zip"] = chunk["LOC_ZIP"].apply(
            lambda z: str(int(z)) if pd.notna(z) else None
        )
        rows = list(
            zip(
                chunk["TAXPINNO"].astype(str),
                chunk["full_address"],
                chunk["zip"],
                chunk["latitude"].astype(float),
                chunk["longitude"].astype(float),
            )
        )
        cur.executemany(
            "INSERT INTO parcels (parcel_id, full_address, zip, latitude, longitude) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        total += len(rows)
        print(f"  inserted {total:,} rows...")

    conn.commit()

    print("Creating indexes...")
    cur.execute("CREATE INDEX idx_parcel_id ON parcels(parcel_id)")
    cur.execute("CREATE INDEX idx_full_address ON parcels(full_address)")
    conn.commit()

    cur.execute("VACUUM")
    conn.commit()
    conn.close()
    print(f"Done. Wrote {total:,} rows to {db_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Build a compact SQLite lookup index from the geocoded parcel CSV"
    )
    parser.add_argument("--csv", default="output.csv", help="Input CSV (default: output.csv)")
    parser.add_argument("--db", default="geocoder.db", help="Output SQLite DB (default: geocoder.db)")
    args = parser.parse_args()
    build_index(args.csv, args.db)


if __name__ == "__main__":
    main()
