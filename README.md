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