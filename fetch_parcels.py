#!/usr/bin/env python3
"""Build geocoder.db from the Montgomery County Auditor's live parcel layer.

Pages through the County's ArcGIS parcel polygon service asking for WGS84
centroids, and writes the same compact `parcels` table that build_index.py
produces from the shapefile — so the web service doesn't care which route
built it. No GIS libraries needed; stdlib only.

    python fetch_parcels.py            # -> geocoder.db (~273k parcels, a few minutes)
    python fetch_parcels.py --out x.db

Source: https://gis.mcohio.org/server/rest/services/TestData/mc_parcel_polygon/FeatureServer/0
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

LAYER = "https://gis.mcohio.org/server/rest/services/TestData/mc_parcel_polygon/FeatureServer/0"
PAGE = 2000
USER_AGENT = "codefordayton-geocoder build (https://github.com/codefordayton/geocoder)"
FIELDS = ["TAXPINNO", "LOC_NBR", "LOC_DIR", "LOC_STREET", "LOC_SUFFIX", "LOC_ZIP"]


def get_json(url: str, params: dict, retries: int = 4) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def full_address(a: dict) -> str:
    parts = []
    if a.get("LOC_NBR") not in (None, 0):
        parts.append(str(int(a["LOC_NBR"])))
    for k in ("LOC_DIR", "LOC_STREET", "LOC_SUFFIX"):
        v = (a.get(k) or "").strip()
        if v:
            parts.append(v)
    return " ".join(parts).upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="geocoder.db")
    args = ap.parse_args()

    total = get_json(LAYER + "/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
    print(f"{total:,} parcels on the County layer", file=sys.stderr)

    con = sqlite3.connect(args.out + ".tmp")
    con.execute("DROP TABLE IF EXISTS parcels")
    con.execute(
        """CREATE TABLE parcels (
             parcel_id TEXT, full_address TEXT, zip TEXT, latitude REAL, longitude REAL)"""
    )

    # Keyset paging on OBJECTID: stays fast at depth and doesn't skip or
    # duplicate rows if the County edits parcels mid-run (offset paging can).
    last_oid, written, skipped = 0, 0, 0
    while True:
        data = get_json(
            LAYER + "/query",
            {
                "where": f"OBJECTID > {last_oid}",
                "outFields": "OBJECTID," + ",".join(FIELDS),
                "returnGeometry": "false",
                "returnCentroid": "true",
                "outSR": 4326,
                "orderByFields": "OBJECTID",
                "resultRecordCount": PAGE,
                "f": "json",
            },
        )
        feats = data.get("features", [])
        if not feats:
            break
        last_oid = max(f["attributes"]["OBJECTID"] for f in feats)
        rows = []
        for f in feats:
            a, c = f.get("attributes", {}), f.get("centroid") or {}
            pid = (a.get("TAXPINNO") or "").strip()
            if not pid or "x" not in c:
                skipped += 1
                continue
            rows.append((pid, full_address(a), (a.get("LOC_ZIP") or "").strip() or None, c["y"], c["x"]))
        con.executemany("INSERT INTO parcels VALUES (?, ?, ?, ?, ?)", rows)
        con.commit()
        written += len(rows)
        print(f"  {written:,} / {total:,}", file=sys.stderr, flush=True)
        if len(feats) < PAGE:
            break

    con.execute("CREATE INDEX idx_parcel_id ON parcels(parcel_id)")
    con.execute("CREATE INDEX idx_full_address ON parcels(full_address)")
    con.execute("CREATE TABLE IF NOT EXISTS _meta (built_at TEXT, source TEXT, parcels INTEGER)")
    con.execute("INSERT INTO _meta VALUES (?, ?, ?)", (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), LAYER, written))
    con.commit()
    con.close()
    import os
    os.replace(args.out + ".tmp", args.out)
    print(f"\nwrote {args.out}: {written:,} parcels ({skipped:,} skipped without id/centroid)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
