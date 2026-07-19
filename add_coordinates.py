import pandas as pd
import argparse
from pathlib import Path

def add_coordinates_to_survey(survey_csv, coordinates_csv, output_csv=None):
    """
    Add latitude and longitude to housing survey data by looking up coordinates
    from the coordinates database using parcel IDs.
    
    Args:
        survey_csv (str): Path to housing survey CSV
        coordinates_csv (str): Path to coordinates CSV (from lookup_coordinates.py)
        output_csv (str, optional): Path for output CSV. If None, will add '_with_coords' 
                                  to original filename
    """
    # Read the CSVs
    print(f"Reading survey data from {survey_csv}")
    survey_df = pd.read_csv(survey_csv)
    
    print(f"Reading coordinates from {coordinates_csv}")
    coords_df = pd.read_csv(coordinates_csv)
    
    # Convert coordinates to numeric values
    coords_df['latitude'] = pd.to_numeric(coords_df['latitude'], errors='coerce')
    coords_df['longitude'] = pd.to_numeric(coords_df['longitude'], errors='coerce')
    
    # Ensure we have a parcel ID column
    if 'TAXPINNO' not in survey_df.columns:
        raise KeyError("Survey CSV must have a 'TAXPINNO' column")
    
    # Merge coordinates into survey data
    print("Joining coordinates with survey data...")
    merged_df = pd.merge(
        survey_df,
        coords_df[['TAXPINNO', 'latitude', 'longitude']],
        left_on='TAXPINNO',
        right_on='TAXPINNO',
        how='left'
    )
    
    # Check for unmatched records
    unmatched = merged_df[merged_df['latitude'].isna()]
    if not unmatched.empty:
        print(f"\nWarning: {len(unmatched)} records could not be matched:")
        print(unmatched['TAXPINNO'].tolist())
    
    # Determine output path
    if output_csv is None:
        output_csv = Path(survey_csv).stem + '_with_coords.csv'
    
    # Save the result with float format for coordinates
    merged_df.to_csv(output_csv, index=False, float_format='%.6f')
    print(f"\nSaved {len(merged_df)} records to {output_csv}")
    print(f"Successfully matched {len(merged_df) - len(unmatched)} records with coordinates")

def main():
    parser = argparse.ArgumentParser(description='Add coordinates to housing survey data')
    parser.add_argument('survey_csv', help='Path to housing survey CSV')
    parser.add_argument('--coords', default='output.csv', 
                       help='Path to coordinates CSV (default: output.csv)')
    parser.add_argument('--output', help='Output CSV path (optional)')
    
    args = parser.parse_args()
    
    add_coordinates_to_survey(args.survey_csv, args.coords, args.output)

if __name__ == "__main__":
    main() 