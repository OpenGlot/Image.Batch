import os
import yaml
import pandas as pd
import logging
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from dotenv import load_dotenv
from config import CONFIG, ENHANCED_DESCRIPTIONS_CSV, IMAGES_CSV, OUTPUT_DIR, OUTPUT_FORMAT
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Load configuration
with open('./configs/images.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Initialize Stability AI client
stability_api = client.StabilityInference(
    key=os.getenv('STABILITY_API_KEY'),
    verbose=True,
)

def generate_image(prompt, config):
    """Generate an image using StabilityAI based on the given prompt and configuration."""
    try:
        # Create the text prompt
        text_prompt = generation.Prompt(text=prompt)
        
        # If there's a negative prompt in the config, add it
        if 'negative_prompt' in config['stability_ai'] and config['stability_ai']['negative_prompt']:
            negative_prompt = generation.Prompt(text=config['stability_ai']['negative_prompt'], parameters=generation.PromptParameters(weight=-1))
            prompts = [text_prompt, negative_prompt]
        else:
            prompts = [text_prompt]

        response = stability_api.generate(
            prompt=prompts,
            steps=config['stability_ai']['steps'],
            cfg_scale=config['stability_ai']['cfg_scale'],
            width=config['stability_ai']['width'],
            height=config['stability_ai']['height'],
            samples=config['stability_ai']['samples'],
            sampler=getattr(generation, f"SAMPLER_{config['stability_ai']['sampler']}"),
            style_preset=config['stability_ai']['style_preset']
        )
        
        for resp in response:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    logging.warning(f"NSFW content detected for prompt: {prompt}")
                    return None
                if artifact.type == generation.ARTIFACT_IMAGE:
                    return artifact.binary
        
        logging.warning(f"No image generated for prompt: {prompt}")
        return None
    except Exception as e:
        logging.error(f"Error generating image for prompt: {prompt}. Error: {str(e)}")
        return None

def generate_deterministic_guid(image_id, context, original_description):
    """Generate a deterministic GUID based on input parameters."""
    combined = f"{image_id}:{context}:{original_description}"
    hash_object = hashlib.sha256(combined.encode())
    hash_digest = hash_object.hexdigest()
    guid = f"{hash_digest[:8]}-{hash_digest[8:12]}-{hash_digest[12:16]}-{hash_digest[16:20]}-{hash_digest[20:32]}"
    
    return guid

def process_descriptions(input_csv, output_csv, config):
    """Process the enhanced descriptions CSV and generate images."""
    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input CSV
    input_df = pd.read_csv(input_csv, encoding='utf-8')
    
    # Check if output CSV exists and read it, otherwise create an empty DataFrame
    if os.path.exists(output_csv):
        output_df = pd.read_csv(output_csv)
        output_df.set_index('image_id', inplace=True)
    else:
        output_df = pd.DataFrame(columns=['image_id', 'context', 'original_description', 'enhanced_description', 'file_name'])
        output_df.set_index('image_id', inplace=True)
    
    # Process each row in the input DataFrame
    for _, row in input_df.iterrows():
        image_id = row['image_id']
        
        # Check if this image_id already exists in the output DataFrame
        if image_id in output_df.index and pd.notna(output_df.loc[image_id, 'file_name']):
            file_path = os.path.join(output_dir, output_df.loc[image_id, 'file_name'])
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logging.info(f"Skipping image_id {image_id}: Already generated")
                continue
        
        context = row['context'].strip()
        original_description = row['original_description'].strip()
        enhanced_description = row['enhanced_description'].strip()
        
        output_file = f"{image_id}_{context}_{generate_deterministic_guid(image_id, context, original_description)}.{config['output']['format']}"
        file_path = os.path.join(output_dir, output_file)
        
        image_data = generate_image(enhanced_description, config)
        
        if image_data:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(image_data)
            logging.info(f"Generated image saved to {file_path}")
            
            # Update or append the row in the output DataFrame
            output_df.loc[image_id] = {
                'context': context,
                'original_description': original_description,
                'enhanced_description': enhanced_description,
                'file_name': output_file
            }
        else:
            logging.warning(f"Failed to generate image for {image_id}")
    
    # Save the updated DataFrame to CSV
    output_df.reset_index().to_csv(output_csv, index=False)
    logging.info(f"Updated CSV saved to {output_csv}")

if __name__ == "__main__":
    input_csv = ENHANCED_DESCRIPTIONS_CSV
    output_csv = IMAGES_CSV
    
    if not os.path.exists(input_csv):
        logging.error(f"Input file {input_csv} not found.")
    else:
        process_descriptions(input_csv, output_csv, config)
        logging.info("Image generation process completed.")