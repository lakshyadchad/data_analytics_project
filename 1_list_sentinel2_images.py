# list_sentinel2_images.py

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from datetime import datetime

def list_sentinel2_images(tile_id, year, month):
    """
    List all Sentinel-2 images for a specific tile, year, and month
    
    Args:
        tile_id: Sentinel-2 tile ID (e.g., '20LNR')
        year: Year (e.g., 2024)
        month: Month (e.g., 6)
    """
    # Configure boto3 for anonymous access
    s3 = boto3.client('s3', 
                      region_name='eu-central-1',
                      config=Config(signature_version=UNSIGNED))
    
    bucket = 'sentinel-s2-l2a'
    
    # Parse tile ID
    utm_zone = tile_id[:2]
    lat_band = tile_id[2]
    grid_square = tile_id[3:5]
    
    # Construct prefix
    prefix = f'tiles/{utm_zone}/{lat_band}/{grid_square}/{year}/{month}/'
    
    print(f"Searching: s3://{bucket}/{prefix}")
    print("-" * 60)
    
    try:
        # List objects
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
        
        if 'CommonPrefixes' not in response:
            print("No images found for this date")
            return []
        
        images = []
        for prefix_obj in response['CommonPrefixes']:
            day_prefix = prefix_obj['Prefix']
            day = day_prefix.split('/')[-2]
            
            # List sequences for this day
            seq_response = s3.list_objects_v2(Bucket=bucket, 
                                             Prefix=day_prefix, 
                                             Delimiter='/')
            
            if 'CommonPrefixes' in seq_response:
                for seq_prefix_obj in seq_response['CommonPrefixes']:
                    seq_prefix = seq_prefix_obj['Prefix']
                    sequence = seq_prefix.split('/')[-2]
                    
                    # Get metadata to check cloud cover
                    metadata_key = f'{seq_prefix}metadata.xml'
                    
                    image_info = {
                        'date': f'{year}-{month:02d}-{int(day):02d}',
                        'path': seq_prefix,
                        's3_uri': f's3://{bucket}/{seq_prefix}',
                        'tile': tile_id,
                        'sequence': sequence
                    }
                    images.append(image_info)
                    
                    print(f"Found: {image_info['date']} - Sequence {sequence}")
                    print(f"  Path: {image_info['s3_uri']}")
        
        print("-" * 60)
        print(f"Total images found: {len(images)}")
        return images
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    # Search for images in Rondônia tile
    tile = "22KFE"
    
    print("=" * 60)
    print("SENTINEL-2 IMAGE SEARCH - RONDÔNIA, BRAZIL")
    print("=" * 60)
    
    # Search for 2024 June
    print("\n📅 Searching June 2024...")
    images_2024 = list_sentinel2_images(tile, 2024, 6)
    
    # Search for 2023 June
    print("\n📅 Searching June 2023...")
    images_2023 = list_sentinel2_images(tile, 2023, 6)
    
    # Search for 2022 June
    print("\n📅 Searching June 2022...")
    images_2022 = list_sentinel2_images(tile, 2022, 6)
    
    # Search for 2021 June
    print("\n📅 Searching June 2021...")
    images_2021 = list_sentinel2_images(tile, 2021, 6)
    
    print("\n" + "=" * 60)
    print("SEARCH COMPLETE")
    print("=" * 60)