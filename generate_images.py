import os
import yaml
import pandas as pd
import logging
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from dotenv import load_dotenv
from config import CONFIG, ENHANCED_DESCRIPTIONS_CSV, IMAGES_CSV, OUTPUT_DIR, OUTPUT_FORMAT

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
        response = stability_api.generate(
            prompt=prompt,
            steps=config['stability_ai']['steps'],
            cfg_scale=config['stability_ai']['cfg_scale'],
            width=config['stability_ai']['width'],
            height=config['stability_ai']['height'],
            samples=config['stability_ai']['samples'],
            sampler=getattr(generation, f"SAMPLER_{config['stability_ai']['sampler']}"),
            style_preset=config['stability_ai']['style_preset'],
            clip_guidance_preset=config['stability_ai']['clip_guidance_preset']
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

def process_descriptions(input_csv, output_csv, config):
    """Process the enhanced descriptions CSV and generate images."""
    output_dir = config['output']['directory']
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input CSV
    input_df = pd.read_csv(input_csv)
    
    # Check if output CSV exists and read it, otherwise create an empty DataFrame
    if os.path.exists(output_csv):
        output_df = pd.read_csv(output_csv)
    else:
        output_df = pd.DataFrame(columns=['image_id', 'context', 'original_description', 'enhanced_description', 'file_name'])
    
    # Process each row in the input DataFrame
    for _, row in input_df.iterrows():
        image_id = row['image_id']
        
        # Check if this image_id already exists in the output DataFrame
        existing_row = output_df[output_df['image_id'] == image_id]
        if not existing_row.empty and pd.notna(existing_row['file_name'].values[0]):
            file_path = os.path.join(output_dir, existing_row['file_name'].values[0])
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logging.info(f"Skipping image_id {image_id}: Already generated")
                continue
        
        context = row['context']
        original_description = row['original_description']
        enhanced_description = row['enhanced_description']
        
        output_file = f"{context}_{image_id}.{config['output']['format']}"
        file_path = os.path.join(output_dir, output_file)
        
        image_data = generate_image(enhanced_description, config)
        
        if image_data:
            with open(file_path, 'wb') as f:
                f.write(image_data)
            logging.info(f"Generated image saved to {file_path}")
            
            # Update or append the row in the output DataFrame
            new_row = {
                'image_id': image_id,
                'context': context,
                'original_description': original_description,
                'enhanced_description': enhanced_description,
                'file_name': output_file
            }
            if existing_row.empty:
                output_df = output_df.append(new_row, ignore_index=True)
            else:
                output_df.loc[output_df['image_id'] == image_id] = new_row
        else:
            logging.warning(f"Failed to generate image for {image_id}")
    
    # Save the updated DataFrame to CSV
    output_df.to_csv(output_csv, index=False)
    logging.info(f"Updated CSV saved to {output_csv}")

if __name__ == "__main__":
    input_csv = ENHANCED_DESCRIPTIONS_CSV
    output_csv = IMAGES_CSV
    
    if not os.path.exists(input_csv):
        logging.error(f"Input file {input_csv} not found.")
    else:
        process_descriptions(input_csv, output_csv, config)
        logging.info("Image generation process completed.")