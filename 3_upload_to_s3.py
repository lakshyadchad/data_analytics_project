# upload_to_s3.py

import boto3
import os
from pathlib import Path

def upload_directory_to_s3(local_dir, bucket_name, s3_prefix):
    """
    Upload entire directory to S3
    """
    s3 = boto3.client('s3')
    
    print(f"Uploading {local_dir} to s3://{bucket_name}/{s3_prefix}")
    print("-" * 60)
    
    uploaded_count = 0
    
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = os.path.join(s3_prefix, relative_path).replace("\\", "/")
            
            try:
                print(f"Uploading {relative_path}...", end=' ')
                s3.upload_file(local_path, bucket_name, s3_path)
                print("✓")
                uploaded_count += 1
            except Exception as e:
                print(f"✗ Error: {e}")
    
    print("-" * 60)
    print(f"Uploaded {uploaded_count} files")

if __name__ == "__main__":
    bucket = "landuse-rondonia-data"
    local_directory = "processed_20LNR"
    s3_directory = "processed/"
    
    upload_directory_to_s3(local_directory, bucket, s3_directory)