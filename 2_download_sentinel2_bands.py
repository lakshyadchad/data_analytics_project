# download_sentinel2_bands.py (FIXED VERSION)

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import os
from pathlib import Path

def download_sentinel2_bands(s3_path, bands, output_dir):
    """
    Download specific bands from Sentinel-2 image
    
    Args:
        s3_path: S3 path to image (e.g., 'tiles/20/L/NR/2024/6/13/0/')
        bands: List of bands to download (e.g., ['B02', 'B03', 'B04', 'B08'])
        output_dir: Local directory to save files
    """
    # Setup S3 client
    s3 = boto3.client('s3', 
                      region_name='eu-central-1',
                      config=Config(signature_version=UNSIGNED))
    
    bucket = 'sentinel-s2-l2a'
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading from: s3://{bucket}/{s3_path}")
    print(f"Bands: {bands}")
    print(f"Output: {output_dir}")
    print("-" * 60)
    
    downloaded_files = []
    
    # Band to resolution mapping
    band_resolution = {
        'B02': 'R10m',  # Blue
        'B03': 'R10m',  # Green
        'B04': 'R10m',  # Red
        'B08': 'R10m',  # NIR
        'B11': 'R20m',  # SWIR1
        'B12': 'R20m',  # SWIR2
        'TCI': 'R10m',  # True Color Image
    }
    
    for band in bands:
        # Get resolution folder
        resolution = band_resolution.get(band, 'R10m')
        
        # Construct file path with resolution subdirectory
        if band == 'TCI':
            remote_file = f'{s3_path}{resolution}/TCI.jp2'
            local_file = os.path.join(output_dir, 'TCI.jp2')
        else:
            remote_file = f'{s3_path}{resolution}/{band}.jp2'
            local_file = os.path.join(output_dir, f'{band}.jp2')
        
        try:
            print(f"Downloading {band}...", end=' ')
            
            # Download file
            s3.download_file(bucket, remote_file, local_file)
            
            # Check file size
            file_size = os.path.getsize(local_file) / (1024 * 1024)  # MB
            print(f"✓ ({file_size:.2f} MB)")
            
            downloaded_files.append(local_file)
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("-" * 60)
    print(f"Downloaded {len(downloaded_files)} files successfully")
    
    return downloaded_files

def download_year_images(tile, year, month, day, sequence, output_base_dir):
    """
    Download images for a specific date
    """
    # Parse tile
    utm_zone = tile[:2]
    lat_band = tile[2]
    grid_square = tile[3:5]
    
    # Construct S3 path
    s3_path = f'tiles/{utm_zone}/{lat_band}/{grid_square}/{year}/{month}/{day}/{sequence}/'
    
    # Create output directory
    output_dir = os.path.join(output_base_dir, f'{year}_{month:02d}_{day:02d}')
    
    # Bands to download
    bands = ['B02', 'B03', 'B04', 'B08', 'B11', 'TCI']
    # B02 = Blue, B03 = Green, B04 = Red, B08 = NIR, B11 = SWIR, TCI = True Color
    
    print(f"\n📥 Downloading {year}-{month:02d}-{day:02d}")
    downloaded = download_sentinel2_bands(s3_path, bands, output_dir)
    
    return downloaded

if __name__ == "__main__":
    # Configuration
    tile = "22KFE"  # Rondônia, Brazil
    base_output_dir = "sentinel2_22KFE_data"
    
    print("=" * 60)
    print("SENTINEL-2 BAND DOWNLOADER - FULL DATA")
    print("Downloading ALL June images (2021-2024)")
    print("=" * 60)
    
    # Download ALL available images from June for each year
    # Based on list_sentinel2_images.py output
    images_to_download = [
        # 2024 - All June dates
        {'year': 2024, 'month': 6, 'day': 10, 'sequence': 0},
        {'year': 2024, 'month': 6, 'day': 15, 'sequence': 0},
        {'year': 2024, 'month': 6, 'day': 20, 'sequence': 0},
        {'year': 2024, 'month': 6, 'day': 25, 'sequence': 0},
        {'year': 2024, 'month': 6, 'day': 30, 'sequence': 0},
        {'year': 2024, 'month': 6, 'day': 5, 'sequence': 0},
        
        # 2023 - All June dates
        {'year': 2023, 'month': 6, 'day': 1, 'sequence': 0},
        {'year': 2023, 'month': 6, 'day': 11, 'sequence': 0},
        {'year': 2023, 'month': 6, 'day': 16, 'sequence': 0},
        {'year': 2023, 'month': 6, 'day': 21, 'sequence': 0},
        {'year': 2023, 'month': 6, 'day': 26, 'sequence': 0},
        {'year': 2023, 'month': 6, 'day': 6, 'sequence': 0},
        
        # 2022 - All June dates
        {'year': 2022, 'month': 6, 'day': 1, 'sequence': 0},
        {'year': 2022, 'month': 6, 'day': 11, 'sequence': 0},
        {'year': 2022, 'month': 6, 'day': 16, 'sequence': 0},
        {'year': 2022, 'month': 6, 'day': 21, 'sequence': 0},
        {'year': 2022, 'month': 6, 'day': 26, 'sequence': 0},
        {'year': 2022, 'month': 6, 'day': 6, 'sequence': 0},
        
        # 2021 - All June dates (both sequences where available)
        {'year': 2021, 'month': 6, 'day': 1, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 1, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 11, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 11, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 16, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 16, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 21, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 21, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 26, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 26, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 6, 'sequence': 0},
        {'year': 2021, 'month': 6, 'day': 6, 'sequence': 1},
        {'year': 2021, 'month': 6, 'day': 6, 'sequence': 2},
        {'year': 2021, 'month': 6, 'day': 6, 'sequence': 3},
    ]
    
    all_downloads = []
    
    for img in images_to_download:
        try:
            files = download_year_images(
                tile, 
                img['year'], 
                img['month'], 
                img['day'], 
                img['sequence'],
                base_output_dir
            )
            all_downloads.extend(files)
        except Exception as e:
            print(f"⚠️  Failed to download {img['year']}-{img['month']:02d}-{img['day']:02d}: {e}")
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print(f"Total files downloaded: {len(all_downloads)}")
    print(f"Location: {base_output_dir}/")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("1. Run: python process_sentinel2.py")
    print("2. Run: python detect_changes.py")