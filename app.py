"""FastAPI geocoding service for Montgomery County, Ohio parcels.

Serves lat/lon lookups by parcel ID or address from the compact SQLite index
built by build_index.py. Read-only: the database is opened per request in
read-only mode, so the process is stateless and safe to run with many workers.
"""

import os
import sqlite3
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query

DB_FILE = os.environ.get("GEOCODER_DB", "geocoder.db")
MAX_RESULTS = 50

app = FastAPI(
    title="Montgomery County Parcel Geocoder",
    description="Look up parcel coordinates by parcel ID or address.",
    version="1.0.0",
)


@contextmanager
def get_db():
    # Open read-only so the shipped index can never be mutated by a request.
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _row_to_dict(row):
    return {
        "parcel_id": row["parcel_id"],
        "address": row["full_address"],
        "zip": row["zip"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
    }


@app.get("/health")
def health():
    """Liveness/readiness check that also confirms the index is reachable."""
    try:
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM parcels").fetchone()[0]
        return {"status": "ok", "parcels": count}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}")


@app.get("/geocode")
def geocode(
    parcel_id: str | None = Query(
        None, description="Exact parcel ID, e.g. 'R72 12307 0032'"
    ),
    address: str | None = Query(
        None, description="Full or partial address, e.g. '4060 DELPHOS AVE' or 'DELPHOS'"
    ),
    limit: int = Query(MAX_RESULTS, ge=1, le=MAX_RESULTS),
):
    """Look up parcels by exact parcel ID or by (partial) address.

    Provide exactly one of `parcel_id` or `address`. Address matching is
    case-insensitive and matches substrings, so partial names return multiple hits.
    """
    if bool(parcel_id) == bool(address):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of 'parcel_id' or 'address'.",
        )

    with get_db() as conn:
        if parcel_id:
            rows = conn.execute(
                "SELECT * FROM parcels WHERE parcel_id = ? LIMIT ?",
                (parcel_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM parcels WHERE full_address LIKE ? LIMIT ?",
                (f"%{address.upper()}%", limit),
            ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No matching parcels found.")

    return {"count": len(rows), "results": [_row_to_dict(r) for r in rows]}
