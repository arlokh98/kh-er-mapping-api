import os
import requests
from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO

app = Flask(__name__)

def fetch_image(image_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        session = requests.Session()
        response = session.get(image_url, headers=headers, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        return str(e)

@app.route("/extract_color", methods=["GET"])
def extract_color():
    image_url = request.args.get("image_url")
    x = int(request.args.get("x", 0))
    y = int(request.args.get("y", 0))

    if not image_url:
        return jsonify({"error": "Missing image URL"}), 400

    image = fetch_image(image_url)
    if isinstance(image, str):  # If fetching failed
        return jsonify({"error": image}), 500

    pixel = image.getpixel((x, y))
    hex_color = "#{:02x}{:02x}{:02x}".format(pixel[0], pixel[1], pixel[2]).upper()
    return jsonify({"hex": hex_color})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
