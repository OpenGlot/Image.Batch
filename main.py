import os
import logging
import csv
from dotenv import load_dotenv
from config import CONFIG, INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV, IMAGES_CSV, OUTPUT_DIR, S3_BUCKET_NAME, S3_INPUT_KEY
from download_csv import download_csv_from_s3
from generate_descriptions import process_csv as generate_descriptions
from generate_images import process_descriptions as generate_images
from sync_to_s3 import sync_to_s3
from validate_artifacts import validate_artifacts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()


def count_csv_rows(file_path):
    """Count the number of valid rows in a CSV file."""
    if not os.path.exists(file_path):
        return 0
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        return sum(1 for row in reader if row)

def file_size_equal(file1, file2):
    """Check if two CSV files have the same number of valid rows."""
    return count_csv_rows(file1) == count_csv_rows(file2)

def main():
    # Validate artifacts
    artifacts_valid = validate_artifacts(IMAGES_CSV, CONFIG)
    if artifacts_valid:
        logging.info("Artifacts are valid. Skipping download and generation.")
    else:
        # Download the CSV file
        csv_exists = os.path.exists(INPUT_CSV)
        if not csv_exists:
            bucket_name = os.getenv('S3_BUCKET_NAME')
            if not bucket_name:
                logging.error("S3_BUCKET_NAME environment variable is not set")
                return
            csv_downloaded = download_csv_from_s3(bucket_name, S3_INPUT_KEY, INPUT_CSV)
            if not csv_downloaded:
                logging.error("Failed to download input CSV")
                return
        
        # Generate enhanced descriptions
        descriptions_exist = os.path.exists(ENHANCED_DESCRIPTIONS_CSV)  and file_size_equal(INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV)
        if not descriptions_exist:
            descriptions_generated = generate_descriptions(INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV)
            if not descriptions_generated:
                logging.error("Failed to generate enhanced descriptions")
                return
        
        # Generate images
        images_exist = os.path.exists(IMAGES_CSV)
        if not images_exist:
            generate_images(ENHANCED_DESCRIPTIONS_CSV, IMAGES_CSV, CONFIG)
    
    # Sync to S3
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        logging.error("S3_BUCKET_NAME environment variable is not set")
        return
    
    sync_successful = sync_to_s3(OUTPUT_DIR, bucket_name, 'batch_generated_images')
    if sync_successful:
        logging.info("Sync to S3 completed successfully")
    else:
        logging.error("Sync to S3 failed")

if __name__ == "__main__":
    main()
