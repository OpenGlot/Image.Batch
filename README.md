# Image.Batch

Image.Batch is a Python batch job application that leverages an AI API to generate images based on provided descriptions. The application processes a CSV input file containing image details and outputs the generated images in organized directories. The final images are then uploaded to an S3 bucket for storage.

## Features

- Batch image generation using AI API.
- Input CSV parsing for image details.
- Multiple processing stages for image generation.
- Output image storage in organized directories.
- Automatic upload of generated images to S3.
- Preference for .png format over .jpeg.

## Prerequisites

- Python 3.8 or higher
- AWS CLI configured with appropriate permissions
- Docker (for containerized deployment)

## Setup

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/Image.Batch.git
    cd Image.Batch
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Configure AWS CLI:**
    Ensure that your AWS CLI is configured with the necessary permissions to upload files to S3.

4. **Set up environment variables:**
    Create a `.env` file in the root directory with the following variables:
    ```env
    AI_API_KEY=your_ai_api_key
    S3_BUCKET_NAME=your_s3_bucket_name
    ```

## Usage

1. **Prepare the input CSV file:**
    The input CSV should have the following format:
    ```csv
    image_id, context, description
    1, nature, "A beautiful sunrise over the mountains."
    2, city, "A bustling city street at night."
    ```

2. **Run the main script:**
    ```sh
    python main.py input.csv
    ```

## Docker Commands

1. **Build the Docker image:**
    ```sh
    docker build -t image-batch .
    ```

2. **Run the Docker container:**
    ```sh
    docker run --env-file .env -v $(pwd):/app image-batch input.csv
    ```

3. **Push Docker image to Docker Hub:**
    ```sh
    docker tag image-batch yourusername/image-batch
    docker push yourusername/image-batch
    ```

## Script Explanations

- `main.py`: Orchestrates the entire batch job process by calling different stages.
- `generate_descriptions.py`: Parses the input CSV file to generate a csv of descriptions
- `generate_images.py`: Uses the AI API to generate images based on descriptions.
- `sync_to_s3.py`: Uploads the generated images to the specified S3 bucket.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements

- Thanks to the developers of the AI API for their powerful image generation capabilities.
- Special thanks to the contributors and the open-source community for their valuable work and support.