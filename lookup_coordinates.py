import pandas as pd
import argparse
import sys
import sqlite3
import geopandas as gpd

def create_full_address(row):
    """Combine address components into a single string."""
    components = []
    
    # Add number if present
    if pd.notna(row.get('LOC_NBR')):
        components.append(str(int(row['LOC_NBR'])))  # Convert to int to remove decimals
    
    # Add direction if present
    if pd.notna(row.get('LOC_DIR')):
        components.append(str(row['LOC_DIR']))
        
    # Add street name if present
    if pd.notna(row.get('LOC_STREET')):
        components.append(str(row['LOC_STREET']))
        
    # Add suffix if present
    if pd.notna(row.get('LOC_SUFFIX')):
        components.append(str(row['LOC_SUFFIX']))
        
    return ' '.join(components)

def process_and_join_data(input_csv, db_file, output_csv, parcel_id_field='TAXPINNO'):
    """
    Join CSV data with parcel database.
    
    Args:
        input_csv (str): Path to input CSV file (with coordinates)
        db_file (str): Path to SQLite database file
        output_csv (str): Path for output CSV file
        parcel_id_field (str): Field name for parcel ID in both datasets
    """
    # Read the CSV file
    print("Reading CSV file...")
    df = pd.read_csv(input_csv)
    
    # Read parcel database
    print("Reading parcel database...")
    conn = sqlite3.connect(db_file)
    parcel_df = pd.read_sql_query("SELECT * FROM rental_registry", conn)
    conn.close()
    
    # Prepare for merge
    input_df = df[['TAXPINNO', 'latitude', 'longitude']]
    
    # Merge with parcel database
    print("Merging datasets...")
    merged_df = pd.merge(
        input_df,
        parcel_df,
        left_on=parcel_id_field,
        right_on='parcel',
        how='inner'
    )
    
    # Save to CSV
    merged_df.to_csv(output_csv, index=False)
    print(f"Merged data saved to {output_csv}")
    print(f"Total records after merge: {len(merged_df)}")
    return merged_df

def lookup_coordinates_db(db_file, search_term, search_field='address'):
    """
    Look up coordinates for a given address or parcel ID.
    
    Args:
        db_file (str): Path to the SQLite database file
        search_term (str): Address or parcel ID to search for
        search_field (str): Column name to search in ('address' or 'parcel_id')
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    if search_field == 'address':
        cursor.execute("SELECT * FROM rental_registry WHERE address = ?", (search_term,))
    else:
        cursor.execute("SELECT * FROM rental_registry WHERE parcel = ?", (search_term,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result


def lookup_coordinates(csv_file, search_term, search_field='address'):
    """
    Look up coordinates for a given address or parcel ID.
    
    Args:
        csv_file (str): Path to the CSV file containing coordinates
        search_term (str): Address or parcel ID to search for
        search_field (str): Column name to search in ('address' or 'parcel_id')
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        if search_field == 'address':
            # Create combined address field
            df['full_address'] = df.apply(create_full_address, axis=1)
            search_field = 'full_address'
        else:  # parcel_id
            search_field = 'TAXPINNO'  # Adjust if your parcel ID column name is different
            
        # Case-insensitive partial match
        mask = df[search_field].str.lower().str.contains(search_term.lower(), na=False)
        matches = df[mask]
        
        if len(matches) == 0:
            print(f"No matches found for {search_term}")
            return
            
        if len(matches) > 1:
            print(f"Found {len(matches)} matches:")
        
        # Display results
        for _, row in matches.iterrows():
            print(f"\nMatch found:")
            print(f"Full Address: {row.get('full_address', 'N/A')}")
            print(f"Parcel ID: {row.get('TAXPINNO', 'N/A')}")
            print(f"Coordinates: {row['latitude']}, {row['longitude']}")
            
    except FileNotFoundError:
        print(f"Error: Could not find file {csv_file}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Required column {e} not found in CSV file")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Process parcels and look up coordinates')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Look up coordinates')
    lookup_parser.add_argument('search_term', help='Address or parcel ID to search for')
    lookup_parser.add_argument('--csv', default='output.csv', help='Path to the CSV file (default: output.csv)')
    lookup_parser.add_argument('--db', default='parcels.db', help='Path to the SQLite database file (default: parcels.db)')
    lookup_parser.add_argument('--field', choices=['address', 'parcel_id'], default='address',
                              help='Field to search in (default: address)')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Join CSV data with database')
    process_parser.add_argument('--csv', required=True, help='Input CSV path')
    process_parser.add_argument('--db', default='parcels.db', help='SQLite database path (default: parcels.db)')
    process_parser.add_argument('--output', default='result.csv', help='Output CSV path (default: result.csv)')
    process_parser.add_argument('--id-field', default='TAXPINNO', help='Parcel ID field name (default: TAXPINNO)')
    
    args = parser.parse_args()
    
    if args.command == 'lookup':
        lookup_coordinates(args.csv, args.search_term, args.field)
    elif args.command == 'process':
        process_and_join_data(args.csv, args.db, args.output, args.id_field)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 