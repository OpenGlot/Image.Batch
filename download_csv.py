import os
import boto3
from botocore.exceptions import ClientError
import logging
from dotenv import load_dotenv
from config import CONFIG, INPUT_CSV, S3_BUCKET_NAME, S3_INPUT_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize S3 client
s3 = boto3.client('s3')

def download_csv_from_s3(bucket_name, s3_key, local_file_path):
    """
    Download a CSV file from S3 if it doesn't exist locally.
    
    :param bucket_name: Name of the S3 bucket
    :param s3_key: S3 object key of the CSV file
    :param local_file_path: Local path to save the downloaded file
    :return: True if file was downloaded or already exists, False otherwise
    """
    if os.path.exists(local_file_path):
        logging.info(f"File already exists locally: {local_file_path}")
        return True
    
    try:
        s3.download_file(bucket_name, s3_key, local_file_path)
        logging.info(f"Successfully downloaded {s3_key} from {bucket_name} to {local_file_path}")
        return True
    except ClientError as e:
        logging.error(f"Error downloading file from S3: {e}")
        return False

if __name__ == "__main__":
    bucket_name = os.getenv('S3_BUCKET_NAME')
    s3_key = S3_INPUT_KEY  # Adjust this if your S3 path is different
    local_file_path = INPUT_CSV
    
    if not bucket_name:
        logging.error("S3_BUCKET_NAME environment variable is not set")
    else:
        if download_csv_from_s3(bucket_name, s3_key, local_file_path):
            logging.info("input.csv is ready for use")
        else:
            logging.error("Failed to ensure input.csv is available")