import csv
import os
import yaml
from openai import OpenAI
from dotenv import load_dotenv
from config import CONFIG, INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize OpenAI API client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def load_gpt_prompts():
    """Load GPT prompts from YAML configuration file."""
    with open('./configs/describe.yml', 'r') as file:
        config = yaml.safe_load(file)
    return config['messages']

def improve_description(description, gpt_prompts):
    """Enhance the image description using GPT-4."""
    messages = gpt_prompts.copy()
    messages[-1]['content'] = messages[-1]['content'].format(description=description)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content.encode("utf-8").decode().strip().strip('"')
    except Exception as e:
        logging.error(f"Error in GPT-4 API call: {str(e)}")
        return None

def process_csv(input_file, output_file):
    """Process input CSV and create output CSV with enhanced descriptions."""
    gpt_prompts = load_gpt_prompts()
    
    if not os.path.exists(input_file):
        logging.error(f"Input file {input_file} not found.")
        return False
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['image_id', 'context', 'original_description', 'enhanced_description']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            image_id = row['image_id'].strip()
            context = row['context'].strip()
            original_description = row['description'].strip().strip('"')
            
            enhanced_description = improve_description(original_description, gpt_prompts)
            logging.info(f"Enhanced description for image {image_id}: {enhanced_description}")
            
            writer.writerow({
                'image_id': image_id,
                'context': context,
                'original_description': original_description,
                'enhanced_description': enhanced_description
            })
    
    return True

if __name__ == "__main__":
    input_file = INPUT_CSV
    output_file = ENHANCED_DESCRIPTIONS_CSV
    
    if process_csv(input_file, output_file):
        logging.info(f"Enhanced descriptions saved to {output_file}")
    else:
        logging.error("Failed to process CSV file")