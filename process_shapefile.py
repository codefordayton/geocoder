import geopandas as gpd
import pandas as pd

def process_shapefile(input_shp, output_csv):
    # Read the shapefile
    gdf = gpd.read_file(input_shp)
    
    # Get the original CRS
    original_crs = gdf.crs
    
    # Clean invalid geometries and calculate centroids
    original_count = len(gdf)
    gdf['centroid'] = gdf.geometry.apply(lambda geom: 
        geom.centroid if geom and geom.is_valid 
        else None)
    
    # Remove rows where centroid calculation failed
    gdf = gdf.dropna(subset=['centroid'])
    print(f"Dropped {original_count - len(gdf)} invalid geometries")
    
    # Create a new GeoDataFrame with just the centroids
    centroid_gdf = gpd.GeoDataFrame(
        gdf.drop(columns=['geometry']),
        geometry='centroid',
        crs=original_crs
    )
    
    # Reproject to WGS84 (EPSG:4326)
    centroid_gdf = centroid_gdf.to_crs('EPSG:4326')
    
    # Extract latitude and longitude from centroids
    centroid_gdf['longitude'] = centroid_gdf.geometry.x
    centroid_gdf['latitude'] = centroid_gdf.geometry.y
    
    # Drop the geometry column and save to CSV
    # centroid_df = centroid_gdf.drop(columns=['geometry'])
    centroid_gdf.to_csv(output_csv, index=False)
    
    print(f"Processed centroids saved to {output_csv}")

if __name__ == "__main__":
    # Example usage
    input_shapefile = "out.shp"
    output_csv = "output.csv"
    
    process_shapefile(input_shapefile, output_csv) 