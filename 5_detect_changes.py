# detect_changes.py (FIXED VERSION)

import rasterio
import numpy as    
import matplotlib.pyplot as plt
from pathlib import Path
import os
from collections import defaultdict

MAX_VIS_SIZE = 5000  # Max dimension for visualization to avoid memory issues

def downsample(array, max_size=MAX_VIS_SIZE):
    """Downsample a 2D array for visualization if it's too large"""
    if array.shape[0] <= max_size and array.shape[1] <= max_size:
        return array
    step = max(array.shape[0], array.shape[1]) // max_size
    return array[::step, ::step]

def discover_processed_images():
    """
    Scan the processed/ directory and group all available
    NDVI/NDBI GeoTIFFs by year.
    
    Returns a dict like:
    {
        2021: ['processed/2021_06_04', 'processed/2021_06_09', ...],
        2022: ['processed/2022_06_04', ...],
        ...
    }
    """
    processed_dir = Path("processed_22KFE")
    
    if not processed_dir.exists():
        print("❌ 'processed/' directory not found!")
        print("   Run process_sentinel2.py first.")
        exit(1)
    
    year_groups = defaultdict(list)
    
    for folder in sorted(processed_dir.iterdir()):
        if not folder.is_dir():
            continue
        # Skip change output folders (e.g., changes_2021_2024)
        if folder.name.startswith("changes_"):
            continue
        # Check that ndvi.tif and ndbi.tif exist
        if (folder / "ndvi.tif").exists() and (folder / "ndbi.tif").exists():
            # Extract year from folder name (e.g., "2021_06_04" → 2021)
            year = int(folder.name.split("_")[0])
            year_groups[year].append(str(folder))
    
    return dict(year_groups)

def load_tif(path):
    """Load a single-band GeoTIFF"""
    with rasterio.open(path) as src:
        data = src.read(1)
        profile = src.profile
    return data, profile

def average_band_for_year(year_folders, band_name):
    """
    Load and average a band (ndvi or ndbi) across all images
    for a given year. This gives a more representative value
    than a single image.
    
    Also ensures all arrays are resized to match if needed.
    """
    arrays = []
    profile = None
    target_shape = None
    
    for folder in year_folders:
        path = os.path.join(folder, f"{band_name}.tif")
        data, prof = load_tif(path)
        
        if target_shape is None:
            target_shape = data.shape
            profile = prof
        
        # Resize if this image has a different shape
        if data.shape != target_shape:
            # Use simple slicing to match shapes
            min_h = min(data.shape[0], target_shape[0])
            min_w = min(data.shape[1], target_shape[1])
            
            resized = np.zeros(target_shape, dtype=data.dtype)
            resized[:min_h, :min_w] = data[:min_h, :min_w]
            data = resized
        
        arrays.append(data.astype(np.float32))
    
    # Average across all images for the year
    averaged = np.mean(arrays, axis=0)
    return averaged, profile

def detect_vegetation_loss(ndvi_before, ndvi_after, threshold=-0.2):
    """
    Detect areas where vegetation decreased significantly
    
    threshold: NDVI difference threshold (default -0.2)
    Negative values = vegetation loss
    """
    ndvi_diff = ndvi_after - ndvi_before
    vegetation_loss = ndvi_diff < threshold
    
    total_pixels = vegetation_loss.size
    changed_pixels = np.sum(vegetation_loss)
    change_percentage = (changed_pixels / total_pixels) * 100
    
    return vegetation_loss, ndvi_diff, change_percentage

def detect_urban_expansion(ndbi_before, ndbi_after, threshold=0.1):
    """
    Detect areas where built-up index increased
    """
    ndbi_diff = ndbi_after - ndbi_before
    urban_expansion = ndbi_diff > threshold
    
    changed_pixels = np.sum(urban_expansion)
    change_percentage = (changed_pixels / urban_expansion.size) * 100
    
    return urban_expansion, ndbi_diff, change_percentage

def visualize_change_detection(year_before, year_after, year_groups):
    """
    Create comprehensive change detection visualization
    """
    print(f"\n{'='*60}")
    print(f"Detecting changes: {year_before} → {year_after}")
    print(f"  Images used for {year_before}: {len(year_groups[year_before])}")
    print(f"  Images used for {year_after}: {len(year_groups[year_after])}")
    print(f"{'='*60}")
    
    # Load and average NDVI across all images per year
    print("  Loading and averaging NDVI...")
    ndvi_before, profile = average_band_for_year(year_groups[year_before], "ndvi")
    ndvi_after, _        = average_band_for_year(year_groups[year_after],  "ndvi")
    
    # Load and average NDBI
    print("  Loading and averaging NDBI...")
    ndbi_before, _ = average_band_for_year(year_groups[year_before], "ndbi")
    ndbi_after, _  = average_band_for_year(year_groups[year_after],  "ndbi")
    
    # Detect changes
    veg_loss, ndvi_diff, veg_loss_pct = detect_vegetation_loss(ndvi_before, ndvi_after)
    urban_exp, ndbi_diff, urban_exp_pct = detect_urban_expansion(ndbi_before, ndbi_after)
    
    # Downsample everything for visualization
    ndvi_before_vis  = downsample(ndvi_before)
    ndvi_after_vis   = downsample(ndvi_after)
    ndbi_before_vis  = downsample(ndbi_before)
    ndbi_after_vis   = downsample(ndbi_after)
    veg_loss_vis     = downsample(veg_loss)
    urban_exp_vis    = downsample(urban_exp)
    
    # Create visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Land Use Change Detection: {year_before} → {year_after}', 
                 fontsize=16, fontweight='bold')
    
    # Row 1: NDVI
    im1 = axes[0, 0].imshow(ndvi_before_vis, cmap='RdYlGn', vmin=0, vmax=1)
    axes[0, 0].set_title(f'NDVI {year_before}')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], shrink=0.8)
    
    im2 = axes[0, 1].imshow(ndvi_after_vis, cmap='RdYlGn', vmin=0, vmax=1)
    axes[0, 1].set_title(f'NDVI {year_after}')
    axes[0, 1].axis('off')
    plt.colorbar(im2, ax=axes[0, 1], shrink=0.8)
    
    im3 = axes[0, 2].imshow(veg_loss_vis, cmap='Reds')
    axes[0, 2].set_title(f'Vegetation Loss\n({veg_loss_pct:.2f}% of area)')
    axes[0, 2].axis('off')
    
    # Row 2: NDBI and combined
    im4 = axes[1, 0].imshow(ndbi_before_vis, cmap='RdYlBu_r', vmin=-0.5, vmax=0.5)
    axes[1, 0].set_title(f'NDBI {year_before}')
    axes[1, 0].axis('off')
    plt.colorbar(im4, ax=axes[1, 0], shrink=0.8)
    
    im5 = axes[1, 1].imshow(ndbi_after_vis, cmap='RdYlBu_r', vmin=-0.5, vmax=0.5)
    axes[1, 1].set_title(f'NDBI {year_after}')
    axes[1, 1].axis('off')
    plt.colorbar(im5, ax=axes[1, 1], shrink=0.8)
    
    # Combined change map
    change_map = np.zeros((*veg_loss_vis.shape, 3))
    change_map[veg_loss_vis] = [1, 0, 0]      # Red: Vegetation loss
    change_map[urban_exp_vis] = [0, 0, 1]     # Blue: Urban expansion
    change_map[veg_loss_vis & urban_exp_vis] = [1, 0, 1]  # Magenta: Both
    
    axes[1, 2].imshow(change_map)
    axes[1, 2].set_title('Combined Changes\nRed: Deforestation | Blue: Urban')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    
    # Save
    output_dir = f"processed_22KFE/changes_{year_before}_{year_after}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{output_dir}/change_detection.png", dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved visualization: {output_dir}/change_detection.png")
    
    # Save change masks as GeoTIFF (full resolution)
    profile = profile.copy()
    profile.update(driver='GTiff', dtype='uint8', count=1)
    
    with rasterio.open(f"{output_dir}/vegetation_loss.tif", 'w', **profile) as dst:
        dst.write(veg_loss.astype('uint8'), 1)
    
    with rasterio.open(f"{output_dir}/urban_expansion.tif", 'w', **profile) as dst:
        dst.write(urban_exp.astype('uint8'), 1)
    
    print(f"✓ Saved GeoTIFFs: {output_dir}/")
    
    # Print statistics
    print(f"\n📊 Change Statistics:")
    print(f"  Vegetation Loss: {veg_loss_pct:.2f}% of area")
    print(f"  Urban Expansion: {urban_exp_pct:.2f}% of area")
    print(f"  Total Pixels Changed: {np.sum(veg_loss | urban_exp):,}")
    
    return veg_loss, urban_exp

if __name__ == "__main__":
    print("=" * 60)
    print("CHANGE DETECTION ANALYSIS")
    print("=" * 60)
    
    # Auto-discover all processed images grouped by year
    year_groups = discover_processed_images()
    
    if not year_groups:
        print("❌ No processed images found!")
        print("   Run process_sentinel2.py first.")
        exit(1)
    
    # Show what was found
    print("\n📂 Discovered processed images:")
    for year in sorted(year_groups.keys()):
        print(f"  {year}: {len(year_groups[year])} images")
        for folder in year_groups[year]:
            print(f"       - {folder}")
    
    # Build year pairs from whatever years are available
    available_years = sorted(year_groups.keys())
    
    year_pairs = []
    # Consecutive year pairs
    for i in range(len(available_years) - 1):
        year_pairs.append((available_years[i], available_years[i + 1]))
    # Total change (first to last year)
    if len(available_years) > 2:
        year_pairs.append((available_years[0], available_years[-1]))
    
    print(f"\n📅 Year pairs to compare: {year_pairs}")
    
    # Run change detection
    for year_before, year_after in year_pairs:
        try:
            visualize_change_detection(year_before, year_after, year_groups)
        except Exception as e:
            print(f"❌ Error processing {year_before}-{year_after}: {e}")
    
    print("\n" + "=" * 60)
    print("CHANGE DETECTION COMPLETE")
    print("=" * 60)
    print("\n💡 Output saved in: processed/changes_YYYY_YYYY/")