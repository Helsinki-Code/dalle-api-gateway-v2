import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# Define the TinyURL API endpoint
TINYURL_API_URL = "https://tinyurl.com/api-create.php"

def shorten_url(long_url):
    """
    Calls the TinyURL API to shorten a given URL.
    Returns the original long URL if the shortening service fails.
    """
    try:
        # The TinyURL API is a simple GET request with the URL as a parameter
        response = requests.get(TINYURL_API_URL, params={'url': long_url}, timeout=5)
        if response.status_code == 200:
            # The short URL is in the response text
            return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error shortening URL: {e}")
    
    # If anything goes wrong, return the original URL as a fallback
    return long_url

@app.route('/generate', methods=['POST'])
def generate_image_dalle():
    """
    Generates an image with DALL-E and returns a shortened URL.
    """
    if not client:
        return jsonify({"error": "OpenAI client is not initialized. Check API key."}), 500

    if not request.json or 'prompt' not in request.json:
        return jsonify({"error": "Request must be JSON with a 'prompt' key."}), 400

    prompt = request.json['prompt']
    if not prompt:
        return jsonify({"error": "The 'prompt' cannot be empty."}), 400

    allowed_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    image_size = request.json.get("size", "1024x1024")
    if image_size not in allowed_sizes:
        image_size = "1024x1024"

    try:
        # Step 1: Get the long URL from OpenAI
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=image_size,
            quality="standard",
            response_format="url"
        )
        long_image_url = response.data[0].url

        # Step 2: Shorten the URL using our new function
        short_image_url = shorten_url(long_image_url)

        # Step 3: Return the shortened URL
        return jsonify({"imageUrl": short_image_url})

    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def index():
    return "DALL-E Image Generation API Gateway with URL Shortening is running!"
