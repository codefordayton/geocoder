import pandas as pd
import argparse
import sys

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
    parser = argparse.ArgumentParser(description='Look up coordinates by address or parcel ID')
    parser.add_argument('search_term', help='Address or parcel ID to search for')
    parser.add_argument('--csv', default='output.csv', help='Path to the CSV file (default: output.csv)')
    parser.add_argument('--field', choices=['address', 'parcel_id'], default='address',
                        help='Field to search in (default: address)')
    
    args = parser.parse_args()
    lookup_coordinates(args.csv, args.search_term, args.field)

if __name__ == "__main__":
    main() 