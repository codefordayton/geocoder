import pandas as pd
import json
from pathlib import Path

def csv_to_json(input_csv, output_json=None):
    """
    Convert CSV file to JSON array.
    
    Args:
        input_csv (str): Path to input CSV file
        output_json (str, optional): Path for output JSON file. 
                                   If None, will use same name as CSV but with .json extension
    """
    # Read CSV file
    print(f"Reading CSV file: {input_csv}")
    df = pd.read_csv(input_csv, keep_default_na=False)
    print(df.head())
    # Convert to JSON array
    json_array = df.to_dict(orient='records')
    
    # Determine output path if not provided
    if output_json is None:
        output_json = Path(input_csv).with_suffix('.json')
    
    # Write to JSON file
    print(f"Writing JSON file: {output_json}")
    with open(output_json, 'w', encoding='utf-8') as f:
        try:

            json.dump(json_array, f, allow_nan=True, indent=2)
        except TypeError as e:
            print(f"Error: {e}")
            print(f"JSON array: {json_array}")
            raise
    
    print(f"Converted {len(json_array)} records to JSON")
    return json_array

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert CSV to JSON array')
    parser.add_argument('input_csv', help='Input CSV file path')
    parser.add_argument('--output', help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    csv_to_json(args.input_csv, args.output) 