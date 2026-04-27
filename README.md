# Phase 2 Dataset: Sentinel-2 Image Processing Pipeline

This repository contains a pipeline of Python scripts for processing Sentinel-2 satellite imagery. The pipeline covers the entire workflow from discovering and downloading images to processing them and detecting changes.

## Pipeline Scripts

The workflow is broken down into five sequential scripts:

1. **`1_list_sentinel2_images.py`**
   - Queries and lists available Sentinel-2 images for a specific area of interest and time period.

2. **`2_download_sentinel2_bands.py`**
   - Downloads the necessary spectral bands for the Sentinel-2 images identified in the previous step.

3. **`3_upload_to_s3.py`**
   - Uploads the downloaded raw or processed image data to an Amazon S3 bucket for storage or cloud-based processing.

4. **`4_process_sentinel2.py`**
   - Processes the raw Sentinel-2 bands (e.g., atmospheric correction, calculating indices like NDVI, image stacking).

5. **`5_detect_changes.py`**
   - Analyzes processed images from different time periods to detect environmental or structural changes in the area of interest.

## Usage

Run the scripts in sequential order (1 to 5) to execute the full pipeline. Ensure you have the necessary dependencies installed and correct credentials (such as AWS and Sentinel Hub/Copernicus Data Space credentials) configured in your environment before running the scripts.
