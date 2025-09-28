import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
# The client will automatically look for the OPENAI_API_KEY environment variable.
try:
    client = OpenAI()
except Exception as e:
    # This will help debug if the API key is missing during startup.
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.route('/generate', methods=['POST'])
def generate_image_dalle():
    """
    Endpoint to generate an image using OpenAI's DALL-E 3 model.
    Accepts 'prompt' and an optional 'size' in the request body.
    """
    if not client:
        return jsonify({"error": "OpenAI client is not initialized. Check API key."}), 500

    # 1. Validate the incoming request
    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Request must be JSON with a 'prompt' key."}), 400

    prompt = request.json['prompt']
    if not prompt:
        return jsonify({"error": "The 'prompt' cannot be empty."}), 400

    # 2. Get and validate the 'size' parameter, with a default
    # DALL-E 3 supports "1024x1024", "1792x1024", or "1024x1792"
    allowed_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    # Get the user-provided size, default to "1024x1024" if not present
    image_size = request.json.get("size", "1024x1024") 
    
    # If the user provided a size but it's not valid, fall back to the default
    if image_size not in allowed_sizes:
        image_size = "1024x1024"

    # 3. Make the API call to DALL-E
    try:
        response = client.images.generate(
            model="dall-e-3", # The latest and most powerful model
            prompt=prompt,
            n=1, # Number of images to generate
            size=image_size, # Use the validated or default size
            quality="standard", # or "hd" for higher quality
            response_format="url" # We want a direct link to the image
        )

        # 4. Extract the image URL from the response
        # The API returns a URL that is valid for one hour.
        image_url = response.data[0].url

        # 5. Return the programmatic response
        return jsonify({"imageUrl": image_url})

    except Exception as e:
        # Catch potential errors from the OpenAI API (e.g., invalid key, billing issues)
        print(f"An error occurred with the OpenAI API: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def index():
    return "DALL-E Image Generation API Gateway is running on Vercel!"

