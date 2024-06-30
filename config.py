import os
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config():
    with open('./configs/config.yml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Replace environment variables in the config
    config['s3']['bucket_name'] = os.getenv(config['s3']['bucket_name'].strip('${}'))
    
    return config

# Load configuration
CONFIG = load_config()

# Convenience variables
INPUT_CSV = CONFIG['csv_files']['input']
ENHANCED_DESCRIPTIONS_CSV = CONFIG['csv_files']['enhanced_descriptions']
IMAGES_CSV = CONFIG['csv_files']['images']
S3_BUCKET_NAME = CONFIG['s3']['bucket_name']
S3_INPUT_KEY = CONFIG['s3']['input_key']
OUTPUT_DIR = CONFIG['output']['directory']
OUTPUT_FORMAT = CONFIG['output']['format']