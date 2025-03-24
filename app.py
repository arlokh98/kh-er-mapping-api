from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageChops
import io
import os
import base64
from skimage.metrics import structural_similarity as ssim
import numpy as np
from collections import OrderedDict

app = Flask(__name__)

REFERENCE_IMAGE_SIZE = 2810
CONFIDENCE_THRESHOLD_CIRCLE = 0.85
CONFIDENCE_THRESHOLD_DIAMOND = 0.90

COLOR_MAP = {
    "#F156FF": "Decision",
    "#2DB38F": "Easy",
    "#ECD982": "Medium",
    "#F07E5F": "Hard",
    "#9843C6": "Portal",
    "#CA3B5F": "Arrival",
    "#D7995B": "Bronze door",
    "#EAE9E8": "Silver door",
    "#FFDF33": "Gold door",
    "#6D6DE5": "Shop",
    "#697785": "Time lock",
    "#E58F16": "Boss",
    "#5A5B78": "Minion"
}

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def closest_color(pixel):
    def hex_to_rgb(hex_color):
        return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    
    closest_hex = None
    closest_dist = float("inf")
    
    for hex_code in COLOR_MAP.keys():
        color_rgb = hex_to_rgb(hex_code)
        dist = color_distance(pixel, color_rgb)
        if dist < closest_dist:
            closest_dist = dist
            closest_hex = hex_code
    
    if closest_dist < 30:
        return closest_hex
    else:
        return "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2])  # fallback to exact color


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

def get_image_scale(image):
    width = image.width
    return width / REFERENCE_IMAGE_SIZE

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
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        pixel = image.getpixel((int(x * scale_factor), int(y * scale_factor)))

        best_hex = closest_color(pixel)
        return jsonify({"hex": best_hex})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_circle', methods=['POST'])
def crop_circle():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)

        x_scaled = int(x * scale_factor)
        y_scaled = int(y * scale_factor)
        radius = int(24 * scale_factor)

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius), fill=255)

        cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius)
        )

        label = find_best_match_icon(cropped_img, "iconsNR", CONFIDENCE_THRESHOLD_CIRCLE)
        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"label": label, "base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_diamond', methods=['POST'])
def crop_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        scaled_x, scaled_y = int(x * scale_factor), int(y * scale_factor)
        radius = int(100 * scale_factor)

        crop_coords = [
            (scaled_x, scaled_y - radius), (scaled_x - radius, scaled_y),
            (scaled_x, scaled_y + radius), (scaled_x + radius, scaled_y)
        ]

        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask).crop(
            (scaled_x - radius, scaled_y - radius, scaled_x + radius, scaled_y + radius)
        )

        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/crop_small_diamond', methods=['POST'])
def crop_small_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)

        x_scaled = int(x * scale_factor)
        y_scaled = int(y * scale_factor)
        offset = int(32 * scale_factor)

        crop_coords = [
            (x_scaled, y_scaled - offset),
            (x_scaled - offset, y_scaled),
            (x_scaled, y_scaled + offset),
            (x_scaled + offset, y_scaled)
        ]
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x_scaled - offset, y_scaled - offset, x_scaled + offset, y_scaled + offset)
        )

        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"image_base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
