import os
import uuid
from flask import Flask, request, jsonify, redirect
from openai import OpenAI
import redis

# Initialize Flask app
app = Flask(__name__)

# --- Vercel KV (Redis) Connection ---
# The connection details are automatically provided by Vercel as environment variables.
try:
    kv = redis.from_url(os.environ.get("KV_URL"))
except Exception as e:
    print(f"Error connecting to Vercel KV: {e}")
    kv = None

# --- OpenAI Client Initialization ---
try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.route('/generate', methods=['POST'])
def generate_image_dalle():
    """
    Generates an image, stores its temporary URL in Vercel KV, 
    and returns a clean, permanent-looking link from our own domain.
    """
    if not client or not kv:
        error_msg = "Server is not configured correctly. Check API key and KV connection."
        return jsonify({"error": error_msg}), 500

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
        # Step 1: Get the long, temporary URL from OpenAI
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=image_size,
            quality="standard",
            response_format="url"
        )
        long_image_url = response.data[0].url

        # Step 2: Create a unique ID for our short link
        image_id = str(uuid.uuid4().hex[:8]) # A short but unique 8-character ID

        # Step 3: Store the long URL in Vercel KV with a 1-hour expiration
        # The DALL-E URL expires in 1 hour, so we'll match that.
        kv.setex(image_id, 3600, long_image_url)

        # Step 4: Construct the clean, short URL using our own domain
        short_url = f"{request.host_url}image/{image_id}"

        # Step 5: Return the clean URL to the user
        return jsonify({"imageUrl": short_url})

    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/image/<image_id>')
def get_image(image_id):
    """
    This endpoint looks up an image_id in Vercel KV and redirects 
    the user to the actual DALL-E image URL.
    """
    if not kv:
        return "KV store not connected", 500

    try:
        # Look for the image_id in the database
        image_url = kv.get(image_id)

        if image_url:
            # If found, redirect the user's browser to the image
            # We decode from bytes to a string for the redirect function
            return redirect(image_url.decode('utf-8'))
        else:
            # If not found (e.g., expired or invalid ID), return an error
            return "Image not found or link has expired.", 404
            
    except Exception as e:
        print(f"Error retrieving from KV: {e}")
        return "Server error", 500

@app.route('/')
def index():
    return "DALL-E Image Generation API with clean, ad-free URLs is running!"

