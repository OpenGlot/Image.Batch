import csv
import os
import yaml
import openai
from dotenv import load_dotenv
from config import CONFIG, INPUT_CSV, ENHANCED_DESCRIPTIONS_CSV

# Load environment variables
load_dotenv()

# Initialize OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_gpt_prompts():
    """Load GPT prompts from YAML configuration file."""
    with open('./configs/describe.yml', 'r') as file:
        config = yaml.safe_load(file)
    return config['messages']

def improve_description(description, gpt_prompts):
    """Enhance the image description using GPT-4."""
    messages = gpt_prompts.copy()
    messages[-1]['content'] = messages[-1]['content'].format(description=description)
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    
    return response.choices[0].message['content'].strip()

def process_csv(input_file, output_file):
    """Process input CSV and create output CSV with enhanced descriptions."""
    gpt_prompts = load_gpt_prompts()
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['image_id', 'context', 'original_description', 'enhanced_description']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            image_id = row['image_id']
            context = row['context']
            original_description = row['description']
            
            enhanced_description = improve_description(original_description, gpt_prompts)
            print(f"Enhanced description for image {image_id}: {enhanced_description}")
            
            writer.writerow({
                'image_id': image_id,
                'context': context,
                'original_description': original_description,
                'enhanced_description': enhanced_description
            })

if __name__ == "__main__":
    input_file = INPUT_CSV
    output_file = ENHANCED_DESCRIPTIONS_CSV
    
    process_csv(input_file, output_file)
    print(f"Enhanced descriptions saved to {output_file}")