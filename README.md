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

Look up coordinates by address or parcel ID:

```bash
# Search by address (default)
python lookup_coordinates.py "123 MAIN ST"

# Search by partial address
python lookup_coordinates.py "MAIN"

# Search by parcel ID
python lookup_coordinates.py "R72 12307 0032" --field parcel_id

# Use a different csv file
python lookup_coordinates.py "MAIN" --csv path/to/coordinates.csv
```


#### Options:
- `search_term`: Address or parcel ID to search for
- `--csv`: Path to the CSV file (default: output.csv)
- `--field`: Field to search in ('address' or 'parcel_id', default: address)

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