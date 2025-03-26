from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageChops
import io
import os
import base64
from skimage.metrics import structural_similarity as ssim
import numpy as np
from collections import OrderedDict
import glob
from priority_cache_manager import PriorityCacheManager
import cv2
import os
import glob
import numpy as np
from PIL import Image

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
}
ISLAND_CENTERS = [
    {"bgX": 1404.5, "bgY": 343.5}, {"bgX": 1140.5, "bgY": 607.5}, {"bgX": 1668.5, "bgY": 607.5},
    {"bgX": 876.5, "bgY": 871.5}, {"bgX": 1404.5, "bgY": 871.5}, {"bgX": 1932.5, "bgY": 871.5},
    {"bgX": 612.5, "bgY": 1135.5}, {"bgX": 1140.5, "bgY": 1135.5}, {"bgX": 1668.5, "bgY": 1135.5},
    {"bgX": 2196.5, "bgY": 1136.0}, {"bgX": 348.5, "bgY": 1399.5}, {"bgX": 876.5, "bgY": 1399.5},
    {"bgX": 1404.5, "bgY": 1399.5}, {"bgX": 1932.5, "bgY": 1399.0}, {"bgX": 2460.5, "bgY": 1400.0},
    {"bgX": 612.5, "bgY": 1663.5}, {"bgX": 1140.5, "bgY": 1663.0}, {"bgX": 1668.5, "bgY": 1663.5},
    {"bgX": 2196.5, "bgY": 1663.0}, {"bgX": 876.5, "bgY": 1927.5}, {"bgX": 1404.5, "bgY": 1927.5},
    {"bgX": 1932.5, "bgY": 1928.0}, {"bgX": 1140.5, "bgY": 2191.5}, {"bgX": 1668.5, "bgY": 2192.0},
    {"bgX": 1404.5, "bgY": 2455.5}
]
COMBAT_TYPE_POINTS = [
    {"bossX": 1406, "bossY": 170, "minionX": 1404, "minionY": 494},
    {"bossX": 1142, "bossY": 434, "minionX": 1140, "minionY": 758},
    {"bossX": 1670, "bossY": 434, "minionX": 1668, "minionY": 758},
    {"bossX": 878, "bossY": 698, "minionX": 876, "minionY": 1022},
    {"bossX": 1406, "bossY": 698, "minionX": 1404, "minionY": 1022},
    {"bossX": 1934, "bossY": 698, "minionX": 1932, "minionY": 1022},
    {"bossX": 614, "bossY": 962, "minionX": 612, "minionY": 1286},
    {"bossX": 1142, "bossY": 962, "minionX": 1140, "minionY": 1286},
    {"bossX": 1670, "bossY": 962, "minionX": 1668, "minionY": 1286},
    {"bossX": 2199, "bossY": 963, "minionX": 2196, "minionY": 1287},
    {"bossX": 350, "bossY": 1225, "minionX": 348, "minionY": 1550},
    {"bossX": 878, "bossY": 1225, "minionX": 876, "minionY": 1550},
    {"bossX": 1406, "bossY": 1226, "minionX": 1404, "minionY": 1550},
    {"bossX": 1934, "bossY": 1226, "minionX": 1932, "minionY": 1549},
    {"bossX": 2462, "bossY": 1226, "minionX": 2460, "minionY": 1550},
    {"bossX": 614, "bossY": 1489, "minionX": 612, "minionY": 1814},
    {"bossX": 1142, "bossY": 1489, "minionX": 1140, "minionY": 1813},
    {"bossX": 1670, "bossY": 1489, "minionX": 1668, "minionY": 1814},
    {"bossX": 2199, "bossY": 1489, "minionX": 2196, "minionY": 1813},
    {"bossX": 878, "bossY": 1753, "minionX": 876, "minionY": 2077},
    {"bossX": 1406, "bossY": 1753, "minionX": 1404, "minionY": 2077},
    {"bossX": 1934, "bossY": 1754, "minionX": 1932, "minionY": 2079},
    {"bossX": 1142, "bossY": 2017, "minionX": 1140, "minionY": 2340},
    {"bossX": 1670, "bossY": 2018, "minionX": 1668, "minionY": 2341},
    {"bossX": 1406, "bossY": 2281, "minionX": 1404, "minionY": 2603}
]

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def closest_color(pixel):
    closest_hex = None
    closest_dist = float("inf")
    for hex_code in COLOR_MAP.keys():
        color_rgb = hex_to_rgb(hex_code)
        dist = color_distance(pixel, color_rgb)
        if dist < closest_dist:
            closest_dist = dist
            closest_hex = hex_code
        if dist <= 5:
            return hex_code
    if closest_dist < 20:
        return closest_hex
    return "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2])

priority_cache = PriorityCacheManager(original_capacity=6, scaled_capacity=12)

CANNOT_BE_MINION_COLORS = {
    "#2DB38F",  # Easy
    "#ECD982",  # Medium
    "#F07E5F"   # Hard
}

MONSTER_HEX = "#262B34"  # Dark fallback (Monster)
MONSTER_THRESHOLD = 10  # Allow fuzzy match within distance 10
def is_monster_color(pixel_hex):
    pixel_rgb = hex_to_rgb(pixel_hex)
    monster_rgb = hex_to_rgb(MONSTER_HEX)
    return color_distance(pixel_rgb, monster_rgb) <= MONSTER_THRESHOLD

def is_minion_color(pixel_hex):
    if pixel_hex.upper() in CANNOT_BE_MINION_COLORS or is_monster_color(pixel_hex):
        return False
    return True

def download_image(image_url):
    cached_image = priority_cache.get_original(image_url)
    if cached_image:
        print(f"Using cached original for {image_url}")
        return cached_image

    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Cloudinary returned error {response.status_code}.")

    img = Image.open(io.BytesIO(response.content)).convert("RGBA")
    priority_cache.store_original(image_url, img)  # Auto-tracks batch/type if present
    return img

def get_image_scale(image):
    return image.width / REFERENCE_IMAGE_SIZE

def preload_er_icon_templates(directories, er_scaled_size=118):
    templates = []
    for directory in directories:
        for file in glob.glob(f"{directory}/*.png"):
            img_pil = Image.open(file).convert("L")
            img_np = np.array(img_pil)  # full-size 200px

            scaled_img = img_pil.resize((er_scaled_size, er_scaled_size))
            scaled_array = np.array(scaled_img)

            templates.append({
                "name": os.path.basename(file).split(".")[0],
                "original": img_np,
                "er_scaled": scaled_array
            })
    return templates

icon_templates = preload_er_icon_templates(["iconsER"], er_scaled_size=118)

def image_similarity_ssim(img1, img2):
    img1_gray = np.array(img1.convert("L"))
    img2_gray = np.array(img2.convert("L").resize(img1.size))
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def find_best_match_icon(img, confidence_threshold):
    best_match, best_score = None, -1
    img_array = np.array(img.convert("L"))  # Convert target crop to grayscale numpy array

    for template in icon_templates:
        template_array = template['er_scaled']  # Use ER-scaled version for matching

        if template_array.shape == img_array.shape:
            score, _ = ssim(img_array, template_array, full=True)

            if score > best_score:
                best_score, best_match = score, template['name']

    return best_match if best_score > confidence_threshold else "other"


@app.route('/extract_color', methods=['GET'])
def extract_color():
    image_url = request.args.get("image_url")
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        pixel = image.getpixel((int(x * scale_factor), int(y * scale_factor)))

        color_result = closest_color(pixel)
        return jsonify({"hex": color_result})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/check_minion', methods=['GET'])
def check_minion():
    image_url = request.args.get("image_url")
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        pixel = image.getpixel((int(x * scale_factor), int(y * scale_factor)))
        pixel_hex = "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2])

        return jsonify({"minion": is_minion_color(pixel_hex)})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/extract_all_categories', methods=['POST'])
def extract_all_categories():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400

        img = download_image(image_url)
        scale = get_image_scale(img)

        results = []

        for i, center in enumerate(islandCenters):
            x_scaled = int(center["bgX"] * scale)
            y_scaled = int(center["bgY"] * scale)
            pixel = img.getpixel((x_scaled, y_scaled))
            hex_color = "#{:02X}{:02X}{:02X}".format(*pixel[:3])
            island_type = COLOR_MAP.get(hex_color.upper(), "Void")

            boss_x = int(combatTypePoints[i]["bossX"] * scale)
            boss_y = int(combatTypePoints[i]["bossY"] * scale)
            boss_pixel = img.getpixel((boss_x, boss_y))
            boss_hex = "#{:02X}{:02X}{:02X}".format(*boss_pixel[:3])

            minion_x = int(combatTypePoints[i]["minionX"] * scale)
            minion_y = int(combatTypePoints[i]["minionY"] * scale)
            minion_pixel = img.getpixel((minion_x, minion_y))
            minion_hex = "#{:02X}{:02X}{:02X}".format(*minion_pixel[:3])

            combat_type_helper = "None"
            if boss_hex.upper() == "#E58F16":
                combat_type_helper = "Boss"
            elif is_minion_color(minion_hex):
                combat_type_helper = "minion"

            # Determine final category label
            lower_type = island_type.lower()
            if lower_type in ["easy", "medium", "hard"]:
                category = combat_type_helper if combat_type_helper != "None" else "Battle"
            elif lower_type == "decision":
                category = "Decision"
            elif lower_type == "shop":
                category = "Shop"
            elif lower_type in ["portal", "arrival"]:
                category = "Portal"
            elif lower_type in ["bronze door", "silver door", "gold door", "time lock"]:
                category = "Door"
            else:
                category = "Void"

            results.append({
                "index": i + 1,
                "island_type": island_type,
                "category": category
            })

        return jsonify({"island_data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/crop_circle', methods=['POST'])
def crop_circle():
    data = request.get_json()
    image_url, x, y = data.get("image_url"), int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        x_scaled, y_scaled = int(x * scale_factor), int(y * scale_factor)
        radius = int(24 * scale_factor)

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius), fill=255)

        cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius))

        label = find_best_match_icon(cropped_img, CONFIDENCE_THRESHOLD_CIRCLE)
        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")
        priority_cache.store_scaled(image_url, 48, cropped_img)  # assuming 48px target scale for small crops

        return jsonify({"label": label, "base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_diamond', methods=['POST'])
def crop_diamond():
    data = request.get_json()
    image_url, x, y = data.get("image_url"), int(data.get("x")), int(data.get("y"))

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

        # Get label from icon matching
        label = find_best_match_icon(cropped_img, CONFIDENCE_THRESHOLD_DIAMOND)

        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        scale = image.width / 2810
        priority_cache.store_scaled(image_url, scale, cropped_img)

        return jsonify({
            "base64": image_base64,
            "label": label
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_small_diamond', methods=['POST'])
def crop_small_diamond():
    data = request.get_json()
    image_url, x, y = data.get("image_url"), int(data.get("x")), int(data.get("y"))

    try:
        image = download_image(image_url)
        scale_factor = get_image_scale(image)
        x_scaled, y_scaled = int(x * scale_factor), int(y * scale_factor)
        offset = int(32 * scale_factor)

        crop_coords = [
            (x_scaled, y_scaled - offset), (x_scaled - offset, y_scaled),
            (x_scaled, y_scaled + offset), (x_scaled + offset, y_scaled)
        ]

        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0,0,0,0)), mask).crop(
            (x_scaled - offset, y_scaled - offset, x_scaled + offset, y_scaled + offset))

        output = io.BytesIO()
        cropped_img.save(output, format="PNG")
        image_base64 = base64.b64encode(output.getvalue()).decode("utf-8")

        return jsonify({"image_base64": image_base64})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/status', methods=['GET'])
def status():
    return jsonify(priority_cache.get_cache_status())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), threaded=True)



