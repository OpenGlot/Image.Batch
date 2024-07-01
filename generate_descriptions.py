import csv
import os
import yaml
from openai import OpenAI
from dotenv import load_dotenv
from config import CONFIG, INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV
import logging
import pandas as pd
import copy 

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
    messages =  copy.deepcopy(gpt_prompts)
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
    """Process input CSV and create or update output CSV with enhanced descriptions."""
    gpt_prompts = load_gpt_prompts()
    
    if not os.path.exists(input_file):
        logging.error(f"Input file {input_file} not found.")
        return False
    
    # Read existing output file if it exists
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        existing_df.set_index('image_id', inplace=True)
    else:
        existing_df = pd.DataFrame()
    
    updated_rows = []
    
    with open(input_file, 'r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            image_id = row['image_id'].strip()
            context = row['context'].strip().replace(' ', '_')
            original_description = row['description'].strip().strip('"')
            
            # Check if this image_id already has an enhanced description
            if image_id in existing_df.index and pd.notna(existing_df.loc[image_id, 'enhanced_description']):
                enhanced_description = existing_df.loc[image_id, 'enhanced_description']
                logging.info(f"Using existing enhanced description for image {image_id}")
            else:
                enhanced_description = improve_description(original_description, gpt_prompts)
                logging.info(f"Generated new enhanced description for image {image_id}")
            
            updated_rows.append({
                'image_id': image_id,
                'context': context,
                'original_description': original_description,
                'enhanced_description': enhanced_description
            })
    
    # Create a new DataFrame with updated rows
    updated_df = pd.DataFrame(updated_rows)
    updated_df.set_index('image_id', inplace=True)
    
    # Combine existing and new data, giving priority to new data
    final_df = existing_df.combine_first(updated_df)
    
    # Save the updated DataFrame to CSV
    final_df.reset_index().to_csv(output_file, index=False)
    logging.info(f"Updated CSV saved to {output_file}")
    
    return True

if __name__ == "__main__":
    input_file = INPUT_CSV
    output_file = ENHANCED_DESCRIPTIONS_CSV
    
    if not os.path.exists(input_file):
        logging.error(f"Input file {input_file} not found.")
    else:
        if process_csv(input_file, output_file):
            logging.info(f"Enhanced descriptions saved to {output_file}")
        else:
            logging.error("Failed to process CSV file")