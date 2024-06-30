import os
import pandas as pd
import logging
from PIL import Image
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Load configuration from YAML file."""
    with open('./configs/images.yml', 'r') as config_file:
        return yaml.safe_load(config_file)

def is_valid_image(file_path):
    """Check if the file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        logging.warning(f"Invalid image file: {file_path}. Error: {str(e)}")
        return False

def validate_artifacts(csv_file, config):
    """Validate the artifacts listed in the CSV file."""
    if not os.path.exists(csv_file):
        logging.error(f"CSV file not found: {csv_file}")
        return False

    df = pd.read_csv(csv_file)
    output_dir = config['output']['directory']
    valid_count = 0
    invalid_count = 0

    for _, row in df.iterrows():
        file_name = row['file_name']
        if pd.isna(file_name):
            logging.warning(f"Missing file_name for image_id: {row['image_id']}")
            invalid_count += 1
            continue

        file_path = os.path.join(output_dir, file_name)
        
        if not os.path.exists(file_path):
            logging.warning(f"File not found: {file_path}")
            invalid_count += 1
        elif not is_valid_image(file_path):
            logging.warning(f"Invalid image file: {file_path}")
            invalid_count += 1
        else:
            valid_count += 1

    total_count = valid_count + invalid_count
    logging.info(f"Validation complete. Total: {total_count}, Valid: {valid_count}, Invalid: {invalid_count}")
    
    return invalid_count == 0

if __name__ == "__main__":
    config = load_config()
    csv_file = "images.csv"
    
    if validate_artifacts(csv_file, config):
        logging.info("All artifacts are valid.")
    else:
        logging.warning("Some artifacts are invalid or missing. Please check the logs for details.")