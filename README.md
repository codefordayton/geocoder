# Geocoding Tools

Tools for processing shapefiles and looking up coordinates by address or parcel ID.

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv env

source env/bin/activate # On Windows, use: env\Scripts\activate
```

2. Install required packages:

```bash
pip install pandas geopandas shapely
```

3. Download the [Montgomery County GIS parcel shapefile](https://go.mcohio.org/embed/auditor/downloads/Shape_files/SHAPEFILE_PARCELLINES_ROW_OLDLOT.zip) from the Montgomery County GIS [website](https://www.mcohio.org/631/GIS-Downloads) and unzip it.

## Usage

### Process Shapefile

Convert a shapefile to CSV with centroid coordinates:

```bash
python process_shapefile.py
```

By default, this looks for `out.shp` and creates `output.csv`. You can modify the input/output paths in the script.

### Look Up Coordinates

The lookup_coordinates script now supports two commands: `lookup` and `process`.

#### Looking up coordinates:
```bash
# Search by address (default)
python lookup_coordinates.py lookup "123 MAIN ST"

# Search by partial address
python lookup_coordinates.py lookup "MAIN"

# Search by parcel ID
python lookup_coordinates.py lookup "R72 12307 0032" --field parcel_id

# Use a different csv file
python lookup_coordinates.py lookup "MAIN" --csv path/to/coordinates.csv
```

#### Processing and joining data:
```bash
python lookup_coordinates.py process --csv output.csv --db parcels.db --output result.csv
```

#### Lookup Options:
- `search_term`: Address or parcel ID to search for
- `--csv`: Path to the CSV file (default: output.csv)
- `--field`: Field to search in ('address' or 'parcel_id', default: address)

#### Process Options:
- `--csv`: Input CSV file path
- `--db`: SQLite database path (default: parcels.db)
- `--output`: Output CSV path (default: result.csv)
- `--id-field`: Parcel ID field name (default: TAXPINNO)

### Convert CSV to JSON

Convert the result CSV file to a JSON array:

```bash
python csv_to_json.py result.csv
# or specify custom output path
python csv_to_json.py result.csv --output data.json
```

The script will create a JSON file with the same name as the input CSV (but with .json extension) if no output path is specified.

## Web Service

The geocoder can run as a REST API (FastAPI) that returns parcel coordinates by
parcel ID or address.

### 1. Build the lookup index

The API reads from a compact, indexed SQLite database. The simplest way to build
it needs no shapefile and no GIS libraries — it pages through the County's live
parcel layer and asks for centroids:

```bash
python fetch_parcels.py          # County ArcGIS layer -> geocoder.db (~273k parcels, ~10 minutes)
```

The older route still works if you have the shapefile-derived CSV:

```bash
python build_index.py            # output.csv -> geocoder.db (~29MB)
```

### 2. Run locally

```bash
pip install -r requirements-web.txt
uvicorn app:app --reload
```

Interactive docs are served at `http://localhost:8000/docs`.

### Endpoints

| Endpoint | Description |
| --- | --- |
| `GET /health` | Liveness check; returns parcel count |
| `GET /geocode?parcel_id=R72 12307 0032` | Exact parcel ID lookup |
| `GET /geocode?address=4060 DELPHOS` | Partial, case-insensitive address lookup |

Example:

```bash
curl "http://localhost:8000/geocode?address=4060%20DELPHOS"
# {"count":1,"results":[{"parcel_id":"R72 12307 0032","address":"4060 DELPHOS AVE",
#   "zip":"45402","latitude":39.763...,"longitude":-84.251...}]}
```

Provide exactly one of `parcel_id` or `address`. Address matches are substrings,
so partial terms may return multiple results (capped at 50).

### Deploy to Railway

The production service runs on Railway from this repo's `Dockerfile`, which downloads
`geocoder.db` from the `geocoder-data` GitHub release. A monthly workflow
(`.github/workflows/geocoder-data.yml`) rebuilds the index from the County layer,
re-uploads it, and bumps `LAST_BUILD` so Railway redeploys. To refresh by hand:

```bash
python fetch_parcels.py
gh release upload geocoder-data geocoder.db --clobber
```

It is also the backend for the `geocode` tool in
[OpenDayton](https://github.com/codefordayton/opendayton).

### Deploy to Google Cloud Run

The `geocoder.db` index is baked into the container image (read-only), so the
service is stateless and scales to zero when idle.

```bash
# Prereqs: gcloud CLI authenticated, a project selected, geocoder.db built.
./deploy.sh
```

To run the container locally:

```bash
docker build -t parcel-geocoder .
docker run -p 8080:8080 parcel-geocoder
curl "http://localhost:8080/health"
```

## CSV File Structure

The script expects the following columns in the CSV file:
- `LOC_NBR`: Street number
- `LOC_DIR`: Street direction
- `LOC_STREET`: Street name
- `LOC_SUFFIX`: Street suffix
- `TAXPINNO`: Parcel ID
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate

## Notes

- Address searches are case-insensitive and support partial matches
- Multiple matches will be displayed if found
- Invalid geometries in the shapefile will be skipped during processing
- The process command in lookup_coordinates.py joins the CSV data with a SQLite database
- The csv_to_json.py script handles NaN values and provides proper JSON formatting