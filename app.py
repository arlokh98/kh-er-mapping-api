from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageChops
import io
import os
import base64
import pytesseract
from difflib import get_close_matches
from skimage.metrics import structural_similarity as ssim
import numpy as np
from collections import OrderedDict

app = Flask(__name__)

# Adjustable thresholds
CONFIDENCE_THRESHOLD_CIRCLE = 0.85
CONFIDENCE_THRESHOLD_DIAMOND = 0.90

# In-memory LRU image cache with size limit
class LRUImageCache:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

image_cache = LRUImageCache(capacity=10)  # Store up to 10 images

# Predefined known OCR words
known_words = [
    "Apostate of the Rift", "Bloodwing", "Butcher of the Rift", "Gorbash Thunderfist", 
    "Heretic of the Rift", "Infernalis", "Kren Rockjaw", "Lord of the Rift", 
    "Necros the Cursed", "Omphalotus Rex", "Penthetor the Scion", "Ravanger of the Rift",
    "Breaker of the Rift", "Deceiver of the Rift", "Renegade of the Rift",
    "Despoiler of the Rift", "Thaumaturge of the Rift", "Timelost of the Rift",
    "Blunted", "Clumsy", "Weightless", "Rogue's Curse", "Hunter's Curse",
    "Siren Song", "Barrier", "Catalyst", "Combust", "Klaxon", "Lights Out",
    "Shackles", "Spores", "Thorns", "Time Warp"
]

def download_image(image_url):
    cached_image = image_cache.get(image_url)
    if cached_image:
        print(f"Using cached image for {image_url}")
        return cached_image
    else:
        try:
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"Cloudinary returned error {response.status_code}.")

            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            image_cache.put(image_url, img)
            return img
        except Exception as e:
            print(f"Failed to download image from {image_url}: {str(e)}")
            raise e

def notify_google_sheets(message, webhook_url):
    if webhook_url:
        try:
            requests.post(webhook_url, json={"message": message})
            print(f"Sent webhook message: {message}")
        except Exception as e:
            print(f"Error sending webhook notification: {e}")

def image_similarity_ssim(img1, img2):
    img1_gray = np.array(img1.convert("L"))
    img2_gray = np.array(img2.convert("L").resize(img1.size))
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def find_best_match_icon(img, directory, confidence_threshold):
    best_match = None
    best_score = -1

    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            try:
                ref_img = Image.open(os.path.join(directory, filename)).convert("L").resize(img.size)
                score = image_similarity_ssim(img, ref_img)
                if score > best_score:
                    best_score = score
                    best_match = filename.split(".")[0]
            except Exception as e:
                print(f"Error comparing {filename}: {e}")

    return best_match if best_score > confidence_threshold else "other"

@app.route('/extract_color', methods=['GET'])
def extract_color():
    image_url = request.args.get("image_url")
    webhook_url = request.args.get("webhook_url")
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        image = download_image(image_url)
        pixel = image.getpixel((x, y))
        hex_color = "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2])
        return jsonify({"hex": hex_color})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_circle', methods=['POST'])
def crop_circle():
    data = request.get_json()
    image_url = data.get("image_url")
    webhook_url = data.get("webhook_url")
    x, y, radius = int(data.get("x")), int(data.get("y")), 24

    try:
        image = download_image(image_url)
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)

        cropped_img = Image.composite(img, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x - radius, y - radius, x + radius, y + radius)
        )

        label = find_best_match_icon(cropped_img, "iconsNR", CONFIDENCE_THRESHOLD_CIRCLE)
        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"label": label, "image_base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_diamond', methods=['POST'])
def crop_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    webhook_url = data.get("webhook_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        crop_coords = [(x, y - 100), (x - 100, y), (x, y + 100), (x + 100, y)]
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(img, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x - 100, y - 100, x + 100, y + 100)
        )

        label = find_best_match_icon(cropped_img, "iconsER", CONFIDENCE_THRESHOLD_DIAMOND)
        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"label": label, "image_base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_small_diamond', methods=['POST'])
def crop_small_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    webhook_url = data.get("webhook_url")
    x, y = int(data.get("x", 0)), int(data.get("y", 0))

    try:
        image = download_image(image_url)
        crop_coords = [(x, y - 32), (x - 32, y), (x, y + 32), (x + 32, y)]
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(img, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask).crop(
            (x - 32, y - 32, x + 32, y + 32)
        )

        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"image_base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.get_json()
    image_url = data.get("image_url")
    webhook_url = data.get("webhook_url")
    x1, y1, x2, y2 = data.get("x1"), data.get("y1"), data.get("x2"), data.get("y2")

    try:
        img = download_image(image_url)
        cropped_img = img.crop((x1, y1, x2, y2))
        raw_text = pytesseract.image_to_string(cropped_img, config="--psm 6").strip()
        match = get_close_matches(raw_text, known_words, n=1, cutoff=0.6)
        best_guess = match[0] if match else "other"

        print(f"Extracted raw text: {raw_text}")
        print(f"Best guess match: {best_guess}")

        return jsonify({
            "raw_text": raw_text,
            "best_match": best_guess
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
