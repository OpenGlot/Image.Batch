import os
import logging
import boto3
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize S3 client
s3 = boto3.client('s3')

def get_s3_file_list(bucket_name, prefix):
    """ Get a list of all files under specified S3 bucket and prefix """
    s3_keys = []
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_keys.append(obj['Key'])
    except ClientError as e:
        logging.error(f"Error listing objects in bucket {bucket_name} with prefix {prefix}: {e}")
    return s3_keys

def upload_file(file_path, bucket_name, s3_key):
    """ Upload a single file to S3 """
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        logging.info(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
        return True
    except ClientError as e:
        logging.error(f"Error uploading {file_path} to S3: {e}")
        return False

def sync_to_s3(local_directory, bucket_name, s3_directory):
    """ Sync local directory to S3 bucket """
    # Get list of files already in S3
    s3_files = set(get_s3_file_list(bucket_name, s3_directory))
    
    # Get list of local files
    local_files = []
    for root, _, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_key = os.path.join(s3_directory, relative_path).replace("\\", "/")
            local_files.append((local_path, s3_key))
    
    # Filter out files that already exist in S3
    files_to_upload = [(local_path, s3_key) for local_path, s3_key in local_files if s3_key not in s3_files]
    
    # Upload files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_file = {executor.submit(upload_file, local_path, bucket_name, s3_key): (local_path, s3_key) 
                          for local_path, s3_key in files_to_upload}
        for future in as_completed(future_to_file):
            local_path, s3_key = future_to_file[future]
            try:
                success = future.result()
                if not success:
                    logging.warning(f"Failed to upload {local_path}")
            except Exception as e:
                logging.error(f"Exception occurred while uploading {local_path}: {e}")

if __name__ == "__main__":
    local_directory = "generated_images"
    bucket_name = os.getenv("S3_BUCKET_NAME")
    s3_directory = "batch_generated_images"
    
    if not bucket_name:
        logging.error("S3_BUCKET_NAME environment variable is not set")
    else:
        sync_to_s3(local_directory, bucket_name, s3_directory)
        logging.info("Sync to S3 completed")