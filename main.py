import os
import logging
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

def main():
    # Validate artifacts
    if validate_artifacts(IMAGES_CSV, CONFIG):
        logging.info("Artifacts are valid. Skipping download and generation.")
    else:
        # Download the CSV file
        if not os.path.exists(INPUT_CSV):
            bucket_name = os.getenv('S3_BUCKET_NAME')
            if not bucket_name:
                logging.error("S3_BUCKET_NAME environment variable is not set")
                return
            if not download_csv_from_s3(bucket_name, S3_INPUT_KEY, INPUT_CSV):
                logging.error("Failed to download input CSV")
                return
        
        # Generate enhanced descriptions
        if not os.path.exists(ENHANCED_DESCRIPTIONS_CSV):
            if not generate_descriptions(INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV):
                logging.error("Failed to generate enhanced descriptions")
                return
        
        # Generate images
        if not os.path.exists(IMAGES_CSV):
            generate_images(ENHANCED_DESCRIPTIONS_CSV, IMAGES_CSV, CONFIG)
    
    # Sync to S3
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not bucket_name:
        logging.error("S3_BUCKET_NAME environment variable is not set")
        return
    
    if sync_to_s3(OUTPUT_DIR, bucket_name, 'batch_generated_images'):
        logging.info("Sync to S3 completed successfully")
    else:
        logging.error("Sync to S3 failed")

if __name__ == "__main__":
    main()