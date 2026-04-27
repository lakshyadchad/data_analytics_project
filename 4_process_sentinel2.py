# process_sentinel2.py

import rasterio
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend BEFORE importing pyplot
import matplotlib.pyplot as plt
from pathlib import Path
import os
import glob

def read_band(band_path):
    """
    Read a Sentinel-2 band (JP2 format)
    """
    with rasterio.open(band_path) as src:
        band_data = src.read(1)  # Read first band
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        
    return band_data, transform, crs, bounds

def normalize_band(band_data):
    """
    Normalize band data to 0-1 range
    """
    band_min = np.percentile(band_data, 2)  # 2nd percentile
    band_max = np.percentile(band_data, 98)  # 98th percentile
    
    normalized = (band_data - band_min) / (band_max - band_min)
    normalized = np.clip(normalized, 0, 1)
    
    return normalized

def calculate_ndvi(nir_path, red_path):
    """
    Calculate NDVI (Normalized Difference Vegetation Index)
    NDVI = (NIR - Red) / (NIR + Red)
    
    Returns values between -1 and 1:
    - High values (0.6-1.0): Dense vegetation
    - Medium (0.2-0.6): Sparse vegetation
    - Low (<0.2): Bare soil, water, urban
    """
    # Read bands
    nir, transform, crs, bounds = read_band(nir_path)
    red, _, _, _ = read_band(red_path)
    
    # Convert to float to avoid division issues
    nir = nir.astype(float)
    red = red.astype(float)
    
    # Calculate NDVI
    ndvi = (nir - red) / (nir + red + 1e-8)  # Add small value to avoid division by zero
    
    return ndvi, transform, crs, bounds

def calculate_ndbi(swir_path, nir_path):
    """
    Calculate NDBI (Normalized Difference Built-up Index)
    NDBI = (SWIR - NIR) / (SWIR + NIR)
    
    High values indicate built-up areas
    
    Note: SWIR is 20m resolution, NIR is 10m resolution
    We resample SWIR to 10m to match NIR
    """
    # Read NIR (10m resolution)
    nir, transform, crs, bounds = read_band(nir_path)
    nir = nir.astype(float)
    
    # Read SWIR (20m resolution) and resample to match NIR
    with rasterio.open(swir_path) as src:
        # Resample SWIR to match NIR dimensions
        swir = src.read(
            1,
            out_shape=(nir.shape[0], nir.shape[1]),
            resampling=rasterio.enums.Resampling.bilinear
        )
    
    swir = swir.astype(float)
    
    # Calculate NDBI
    ndbi = (swir - nir) / (swir + nir + 1e-8)
    
    return ndbi, transform, crs, bounds

def create_true_color_composite(red_path, green_path, blue_path, output_path):
    """
    Create RGB true color composite
    Downsamples to reasonable size for visualization to avoid memory issues
    """
    red, transform, crs, bounds = read_band(red_path)
    green, _, _, _ = read_band(green_path)
    blue, _, _, _ = read_band(blue_path)
    
    # Downsample for visualization if image is too large (saves memory)
    max_size = 5000  # Maximum dimension for visualization
    if red.shape[0] > max_size or red.shape[1] > max_size:
        scale_factor = max_size / max(red.shape)
        new_height = int(red.shape[0] * scale_factor)
        new_width = int(red.shape[1] * scale_factor)
        
        print(f"  Downsampling from {red.shape} to ({new_height}, {new_width}) for visualization...")
        
        # Use scikit-image for better quality downsampling if available
        try:
            from skimage.transform import resize
            red = resize(red, (new_height, new_width), preserve_range=True, anti_aliasing=True)
            green = resize(green, (new_height, new_width), preserve_range=True, anti_aliasing=True)
            blue = resize(blue, (new_height, new_width), preserve_range=True, anti_aliasing=True)
        except ImportError:
            # Fallback to simple array slicing
            step = int(1 / scale_factor)
            red = red[::step, ::step]
            green = green[::step, ::step]
            blue = blue[::step, ::step]
    
    # Normalize each band
    red_norm = normalize_band(red)
    green_norm = normalize_band(green)
    blue_norm = normalize_band(blue)
    
    # Stack bands
    rgb = np.dstack([red_norm, green_norm, blue_norm])
    
    # Save as PNG
    plt.figure(figsize=(12, 12))
    plt.imshow(rgb)
    plt.title("True Color Composite")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_path}")
    
    return rgb

def visualize_ndvi(ndvi, output_path):
    """
    Visualize NDVI with color map
    Downsamples if needed to save memory
    """
    # Downsample for visualization if too large
    max_size = 5000
    ndvi_display = ndvi
    if ndvi.shape[0] > max_size or ndvi.shape[1] > max_size:
        scale_factor = max_size / max(ndvi.shape)
        new_height = int(ndvi.shape[0] * scale_factor)
        new_width = int(ndvi.shape[1] * scale_factor)
        
        try:
            from skimage.transform import resize
            ndvi_display = resize(ndvi, (new_height, new_width), preserve_range=True, anti_aliasing=True)
        except ImportError:
            step = int(1 / scale_factor)
            ndvi_display = ndvi[::step, ::step]
    
    plt.figure(figsize=(12, 10))
    
    im = plt.imshow(ndvi_display, cmap='RdYlGn', vmin=-0.5, vmax=1.0)
    plt.colorbar(im, label='NDVI', shrink=0.8)
    plt.title('NDVI (Vegetation Index)', fontsize=14)
    plt.axis('off')
    
    # Add legend
    legend_text = (
        'NDVI Values:\n'
        '0.6 - 1.0: Dense vegetation\n'
        '0.3 - 0.6: Moderate vegetation\n'
        '0.0 - 0.3: Sparse vegetation\n'
        '< 0.0: Water, urban, bare soil'
    )
    plt.text(0.02, 0.98, legend_text, 
             transform=plt.gca().transAxes,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
             verticalalignment='top',
             fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_path}")

def process_single_image(image_dir, date_str):
    """
    Process one Sentinel-2 image
    """
    print(f"\n{'='*60}")
    print(f"Processing {date_str}...")
    print(f"{'='*60}")
    
    # Define band paths
    blue_path = os.path.join(image_dir, 'B02.jp2')
    green_path = os.path.join(image_dir, 'B03.jp2')
    red_path = os.path.join(image_dir, 'B04.jp2')
    nir_path = os.path.join(image_dir, 'B08.jp2')
    swir_path = os.path.join(image_dir, 'B11.jp2')
    
    # Check if files exist
    if not all(os.path.exists(p) for p in [red_path, green_path, blue_path, nir_path, swir_path]):
        print("❌ Not all required bands found!")
        missing = [p for p in [red_path, green_path, blue_path, nir_path, swir_path] if not os.path.exists(p)]
        print(f"   Missing: {missing}")
        return None
    
    # Create output directory
    output_dir = f"processed_22KFE/{date_str}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. True color composite
    print("Creating true color composite...")
    rgb = create_true_color_composite(
        red_path, green_path, blue_path,
        f"{output_dir}/true_color.png"
    )
    
    # 2. Calculate and visualize NDVI
    print("Calculating NDVI...")
    ndvi, transform, crs, bounds = calculate_ndvi(nir_path, red_path)
    visualize_ndvi(ndvi, f"{output_dir}/ndvi.png")
    
    # Save NDVI as GeoTIFF for later use
    with rasterio.open(red_path) as src:
        profile = src.profile.copy()  # Important: copy the profile
        profile.update(
            driver='GTiff',  # Force GTiff driver instead of JP2
            dtype=rasterio.float32, 
            count=1, 
            compress='lzw'
        )
    
    with rasterio.open(f"{output_dir}/ndvi.tif", 'w', **profile) as dst:
        dst.write(ndvi.astype(rasterio.float32), 1)
    
    print(f"Saved: {output_dir}/ndvi.tif")
    
    # 3. Calculate NDBI
    print("Calculating NDBI...")
    ndbi, _, _, _ = calculate_ndbi(swir_path, nir_path)
    
    # Visualize NDBI (with downsampling if needed)
    ndbi_display = ndbi
    max_size = 5000
    if ndbi.shape[0] > max_size or ndbi.shape[1] > max_size:
        scale_factor = max_size / max(ndbi.shape)
        new_height = int(ndbi.shape[0] * scale_factor)
        new_width = int(ndbi.shape[1] * scale_factor)
        
        try:
            from skimage.transform import resize
            ndbi_display = resize(ndbi, (new_height, new_width), preserve_range=True, anti_aliasing=True)
        except ImportError:
            step = int(1 / scale_factor)
            ndbi_display = ndbi[::step, ::step]
    
    plt.figure(figsize=(12, 10))
    im = plt.imshow(ndbi_display, cmap='RdYlBu_r', vmin=-0.5, vmax=0.5)
    plt.colorbar(im, label='NDBI', shrink=0.8)
    plt.title('NDBI (Built-up Index)', fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ndbi.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_dir}/ndbi.png")
    
    # Save NDBI as GeoTIFF
    with rasterio.open(f"{output_dir}/ndbi.tif", 'w', **profile) as dst:
        dst.write(ndbi.astype(rasterio.float32), 1)
    
    print(f"Saved: {output_dir}/ndbi.tif")
    
    # Statistics
    print(f"\n📊 Statistics:")
    print(f"  NDVI - Mean: {np.nanmean(ndvi):.3f}, Std: {np.nanstd(ndvi):.3f}")
    print(f"  NDVI - Min: {np.nanmin(ndvi):.3f}, Max: {np.nanmax(ndvi):.3f}")
    print(f"  NDBI - Mean: {np.nanmean(ndbi):.3f}, Std: {np.nanstd(ndbi):.3f}")
    
    return {
        'date': date_str,
        'ndvi': ndvi,
        'ndbi': ndbi,
        'transform': transform,
        'crs': crs,
        'bounds': bounds
    }

if __name__ == "__main__":
    print("=" * 60)
    print("SENTINEL-2 PREPROCESSING PIPELINE")
    print("Automatically processing ALL downloaded images")
    print("=" * 60)
    
    # Find all downloaded image directories
    sentinel_data_dir = "sentinel_22KFE_data"
    
    if not os.path.exists(sentinel_data_dir):
        print(f"❌ Error: Directory '{sentinel_data_dir}' not found!")
        print("   Make sure you've downloaded the data first using download_sentinel2_bands.py")
        exit(1)
    
    # Get all subdirectories (each represents a date)
    image_dirs = sorted([d for d in Path(sentinel_data_dir).iterdir() if d.is_dir()])
    
    if not image_dirs:
        print(f"❌ No image directories found in '{sentinel_data_dir}'!")
        print("   Make sure you've downloaded the data first.")
        exit(1)
    
    print(f"\nFound {len(image_dirs)} image directories to process")
    print("-" * 60)
    
    # Process each image
    processed_data = []
    
    for image_dir in image_dirs:
        date_str = image_dir.name  # e.g., "2024_06_13"
        result = process_single_image(str(image_dir), date_str)
        if result:
            processed_data.append(result)
    
    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print(f"Successfully processed: {len(processed_data)} images")
    print(f"Failed: {len(image_dirs) - len(processed_data)} images")
    print("=" * 60)
    
    if processed_data:
        print("\n✅ Processed images:")
        for data in processed_data:
            print(f"   - {data['date']}")
        
        print("\n💡 Next steps:")
        print("1. Check the 'processed/' directory for visualizations")
        print("2. Run: python detect_changes.py")