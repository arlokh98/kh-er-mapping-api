from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageDraw
import io
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from skimage.metrics import structural_similarity as ssim
import numpy as np
import os
import glob
from priority_cache_manager import PriorityCacheManager
import logging
from PIL import ImageEnhance


logging.basicConfig(
    level=logging.INFO,  # Set to WARNING or ERROR in production to reduce noise
    format='[%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

REFERENCE_IMAGE_SIZE = 2810
CONFIDENCE_THRESHOLD_CIRCLE = 0.85
CONFIDENCE_THRESHOLD_DIAMOND = 0.89

priority_cache = PriorityCacheManager(original_capacity=6, scaled_capacity=6)

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

RAW_COLOR_MAP = {
    "#F156FF": "decision",
    "#2DB38F": "easy",
    "#ECD982": "medium",
    "#F07E5F": "hard",
    "#9843C6": "portal",
    "#CA3B5F": "arrival",
    "#D7995B": "bronze door",
    "#EAE9E8": "silver door",
    "#FFDF33": "gold door",
    "#6D6DE5": "shop",
    "#697785": "time lock",
    "#E58F16": "boss"
}

COLOR_MAP = {k.upper(): v for k, v in RAW_COLOR_MAP.items()}
RGB_COLOR_MAP = {hex_to_rgb(k): v for k, v in COLOR_MAP.items()}

islandCenters = [
    { "bgX": 1404.5, "bgY": 343.5 },
    { "bgX": 1140.5, "bgY": 607.5 },
    { "bgX": 1668.5, "bgY": 607.5 },
    { "bgX": 876.5, "bgY": 871.5 },
    { "bgX": 1404.5, "bgY": 871.5 },
    { "bgX": 1932.5, "bgY": 871.5 },
    { "bgX": 612.5, "bgY": 1135.5 },
    { "bgX": 1140.5, "bgY": 1135.5 },
    { "bgX": 1668.5, "bgY": 1135.5 },
    { "bgX": 2196.5, "bgY": 1136.0 },
    { "bgX": 348.5, "bgY": 1399.5 },
    { "bgX": 876.5, "bgY": 1399.5 },
    { "bgX": 1404.5, "bgY": 1399.5 },
    { "bgX": 1932.5, "bgY": 1399.0 },
    { "bgX": 2460.5, "bgY": 1400.0 },
    { "bgX": 612.5, "bgY": 1663.5 },
    { "bgX": 1140.5, "bgY": 1663.0 },
    { "bgX": 1668.5, "bgY": 1663.5 },
    { "bgX": 2196.5, "bgY": 1663.0 },
    { "bgX": 876.5, "bgY": 1927.5 },
    { "bgX": 1404.5, "bgY": 1927.5 },
    { "bgX": 1932.5, "bgY": 1928.0 },
    { "bgX": 1140.5, "bgY": 2191.5 },
    { "bgX": 1668.5, "bgY": 2192.0 },
    { "bgX": 1404.5, "bgY": 2455.5 }
]
combatTypePoints = [
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
arrowPointsA = [
    'x',
    'x',
    [[1558, 497], [1515, 454]],
    'x',
    [[1294, 761], [1251, 718]],
    [[1822, 761], [1779, 718]],
    'x',
    [[1030, 1025], [987, 982]],
    [[1558, 1025], [1515, 982]],
    [[2086, 1025], [2043, 982]],
    'x',
    [[766, 1289], [723, 1246]],
    [[1294, 1289], [1251, 1246]],
    [[1822, 1289], [1779, 1246]],
    [[2350, 1289], [2307, 1246]],
    [[502, 1553], [459, 1510]],
    [[1030, 1553], [987, 1510]],
    [[1558, 1553], [1515, 1510]],
    [[2086, 1553], [2043, 1510]],
    [[766, 1817], [723, 1774]],
    [[1294, 1817], [1251, 1774]],
    [[1822, 1817], [1779, 1774]],
    [[1030, 2081], [987, 2038]],
    [[1558, 2081], [1515, 2038]],
    [[1294, 2345], [1251, 2302]]
]
arrowPointsD = [
    'x',
    [[1251, 497], [1294, 454]],
    'x',
    [[987, 761], [1030, 718]],
    [[1515, 761], [1558, 718]],
    'x',
    [[723, 1025], [766, 982]],
    [[1251, 1025], [1294, 982]],
    [[1779, 1025], [1822, 982]],
    'x',
    [[459, 1289], [502, 1246]],
    [[987, 1289], [1030, 1246]],
    [[1515, 1289], [1558, 1246]],
    [[2043, 1289], [2086, 1246]],
    'x',
    [[723, 1553], [766, 1510]],
    [[1251, 1553], [1294, 1510]],
    [[1779, 1553], [1822, 1510]],
    [[2307, 1553], [2350, 1510]],
    [[987, 1817], [1030, 1774]],
    [[1515, 1817], [1558, 1774]],
    [[2043, 1817], [2086, 1774]],
    [[1251, 2081], [1294, 2038]],
    [[1779, 2081], [1822, 2038]],
    [[1515, 2345], [1558, 2302]]
]
icon_points = [
            { "leftX": 1304, "leftY": 343, "rightX": 1504, "rightY": 343 },
            { "leftX": 1040, "leftY": 607, "rightX": 1240, "rightY": 607 },
            { "leftX": 1570, "leftY": 607, "rightX": 1770, "rightY": 607 },
            { "leftX": 776, "leftY": 871, "rightX": 976, "rightY": 871 },
            { "leftX": 1304, "leftY": 871, "rightX": 1504, "rightY": 871 },
            { "leftX": 1832, "leftY": 871, "rightX": 2032, "rightY": 871 },
            { "leftX": 512, "leftY": 1135, "rightX": 712, "rightY": 1135 },
            { "leftX": 1040, "leftY": 1135, "rightX": 1240, "rightY": 1135 },
            { "leftX": 1570, "leftY": 1135, "rightX": 1770, "rightY": 1135 },
            { "leftX": 2098, "leftY": 1135, "rightX": 2298, "rightY": 1135 },
            { "leftX": 248, "leftY": 1399, "rightX": 448, "rightY": 1399 },
            { "leftX": 776, "leftY": 1399, "rightX": 976, "rightY": 1399 },
            { "leftX": 1304, "leftY": 1399, "rightX": 1504, "rightY": 1399 },
            { "leftX": 1832, "leftY": 1399, "rightX": 2032, "rightY": 1399 },
            { "leftX": 2360, "leftY": 1399, "rightX": 2560, "rightY": 1399 },
            { "leftX": 512, "leftY": 1663, "rightX": 712, "rightY": 1663 },
            { "leftX": 1040, "leftY": 1663, "rightX": 1240, "rightY": 1663 },
            { "leftX": 1570, "leftY": 1663, "rightX": 1770, "rightY": 1663 },
            { "leftX": 2098, "leftY": 1663, "rightX": 2298, "rightY": 1663 },
            { "leftX": 776, "leftY": 1927, "rightX": 976, "rightY": 1927 },
            { "leftX": 1304, "leftY": 1927, "rightX": 1504, "rightY": 1927 },
            { "leftX": 1832, "leftY": 1927, "rightX": 2032, "rightY": 1927 },
            { "leftX": 1040, "leftY": 2191, "rightX": 1240, "rightY": 2191 },
            { "leftX": 1570, "leftY": 2191, "rightX": 1770, "rightY": 2191 },
            { "leftX": 1304, "leftY": 2455, "rightX": 1504, "rightY": 2455 }
        ]

door_categories = {"bronze door", "silver door", "door", "gold door", "time lock"}
symbol_categories = {"portal", "arrival", "shop"}
ssim_categories = {"decision"}
image_categories = {"battle", "boss"}

def preprocess_crop_and_gray(img, x, y, scale, radius=100, size=(118, 118)):
    """
    Crop a diamond shape, convert to grayscale, resize, and return the image and NumPy array.
    """
    scaled_x, scaled_y = int(x * scale), int(y * scale)
    crop_coords = [
        (scaled_x, scaled_y - radius), (scaled_x - radius, scaled_y),
        (scaled_x, scaled_y + radius), (scaled_x + radius, scaled_y)
    ]
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(crop_coords, fill=255)
    cropped = Image.composite(img, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask).crop(
        (scaled_x - radius, scaled_y - radius, scaled_x + radius, scaled_y + radius)
    )
    gray_resized = cropped.convert("L").resize(size)
    return cropped, gray_resized

def preprocess_crop(crop, size=(118, 118)):
    enhancer = ImageEnhance.Contrast(crop.convert("L"))
    boosted = enhancer.enhance(1.5)  # increase contrast
    return boosted.resize(size)

class ImageContext:
    def __init__(self, image_url):
        self.url = image_url
        self.img = download_image(image_url).convert("RGBA")
        self.image = self.img  # ✅ Add this line for legacy compatibility
        self.scale = get_image_scale(self.img)
        self.img_np = np.array(self.img)

    def scale_xy(self, x, y):
        return int(x * self.scale), int(y * self.scale)

    def get_pixel(self, x, y):
        sx, sy = self.scale_xy(x, y)
        return self.image.getpixel((sx, sy))

def enhance_contrast(img, factor=1.5):
    return ImageEnhance.Contrast(img).enhance(factor)

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def closest_color(pixel):
    closest_rgb = None
    closest_dist = float("inf")
    for color_rgb in RGB_COLOR_MAP:
        dist = color_distance(pixel, color_rgb)
        if dist < closest_dist:
            closest_dist = dist
            closest_rgb = color_rgb

    return closest_rgb if closest_dist < 20 else pixel

CANNOT_BE_MINION_COLORS = {
    "#2DB38F",  # Easy
    "#ECD982",  # Medium
    "#F07E5F"   # Hard
}

MONSTER_HEX = "#262B34"  # Dark fallback (Monster)
CANNOT_BE_MINION_RGB = {hex_to_rgb(c) for c in CANNOT_BE_MINION_COLORS}
MONSTER_RGB = hex_to_rgb(MONSTER_HEX)
def is_monster_color(pixel_rgb):
    return color_distance(pixel_rgb, MONSTER_RGB) <= MONSTER_THRESHOLD
def is_minion_color(pixel_rgb):
    if pixel_rgb in CANNOT_BE_MINION_RGB or is_monster_color(pixel_rgb):
        return False
    return True

MONSTER_THRESHOLD = 10  # Allow fuzzy match within distance 10

def download_image(image_url):
    cached_image = priority_cache.get_original(image_url)
    if cached_image:
        logging.info(f"Using cached original for {image_url}")
        return cached_image

    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Cloudinary returned error {response.status_code}.")

    img = Image.open(io.BytesIO(response.content)).convert("RGBA")
    priority_cache.store_original(image_url, img)
    return img
def preprocess_full_image(image):
    img_np = np.array(image.convert("RGB"))
    img_gray = np.array(image.convert("L"))
    return {
        "original": image,
        "rgb_array": img_np,
        "gray_array": img_gray,
        "scale": image.width / REFERENCE_IMAGE_SIZE
    }

def get_image_scale(image):
    return image.width / REFERENCE_IMAGE_SIZE

def preload_er_icon_templates(directories, er_scaled_size=118):
    templates = {}
    for directory in directories:
        for file in glob.glob(f"{directory}/*.png"):
            img_pil = Image.open(file).convert("L")
            img_np = np.array(img_pil)  # full-size 200px

            scaled_img = img_pil.resize((er_scaled_size, er_scaled_size))
            scaled_array = np.array(scaled_img)

            name = os.path.basename(file).split(".")[0]
            templates[name] = {
                "original": img_np,
                "er_scaled": scaled_array
            }
    
    logging.info(f"[TEMPLATE LOAD] Loaded template: {name} from {file}")
    return templates

icon_templates = preload_er_icon_templates(["iconsER"], er_scaled_size=118)

def image_similarity_ssim(gray1_np, gray2_np):
    return ssim(gray1_np, gray2_np, full=False)

def find_best_match_icon_np(gray_crop_np, threshold=0.85):
    best_score = -1
    best_name = "other"

    for name, template in icon_templates.items():
        template_np = template["er_scaled"]
        if gray_crop_np.shape != template_np.shape:
            continue
        score = ssim(gray_crop_np, template_np)
        if score > best_score:
            best_score = score
            best_name = name

    return {
        "label": best_name if best_score >= threshold else "other",
        "score": best_score
    }

def best_shifted_match(ctx: ImageContext, x, y, threshold=0.85):
    best_crop = None
    best_score = -1
    best_label = "other"

    # Try center and then shifted ±1 and ±2 pixels
    for shift in [0, 1, 2]:
        for dx in [-shift, 0, shift]:
            for dy in [-shift, 0, shift]:
                if shift != 0 and dx == 0 and dy == 0:
                    continue

                crop = ctx.crop_diamond(x + dx, y + dy)
                processed = preprocess_crop(crop)
                gray_np = np.array(processed)

                match = find_best_match_icon_np(gray_np, threshold)
                if match["score"] > best_score:
                    best_score = match["score"]
                    best_label = match["label"]
                    best_crop = crop

    return {
        "label": best_label,
        "score": best_score,
        "base64": image_to_base64(best_crop) if best_crop else ""
    }

def image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

@app.route('/extract_color', methods=['GET'])
def extract_color():
    image_url = request.args.get("image_url")
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        ctx = ImageContext(image_url)
        pixel = ctx.np_img[int(y * ctx.scale), int(x * ctx.scale)]
        pixel_rgb = tuple(pixel[:3])
        hex_result = closest_color(pixel_rgb)
        return jsonify({"hex": hex_result})
    except Exception as e:
        logger.exception("Error in extract_color")
        return jsonify({"error": str(e)})

@app.route('/check_minion', methods=['GET'])
def check_minion():
    image_url = request.args.get("image_url")
    x, y = int(request.args.get("x", 0)), int(request.args.get("y", 0))

    try:
        ctx = ImageContext(image_url)
        pixel = ctx.np_img[int(y * ctx.scale), int(x * ctx.scale)]
        pixel_rgb = tuple(pixel[:3])
        return jsonify({"minion": is_minion_color(pixel_rgb)})
    except Exception as e:
        logger.exception("Error in check_minion")
        return jsonify({"error": str(e)})

@app.route("/extract_all_categories", methods=["POST"])
def extract_all_categories():
    data = request.get_json()
    image_url = data.get("image_url")
    logger.info(f"📥 [extract_all_categories] Image URL received: {image_url}")

    try:
        ctx = ImageContext(image_url)
        img_np = ctx.img_np  # Preprocessed full image as NumPy array
        scale = ctx.scale
        results = []

        def process_island(i, center):
            try:
                x_scaled = int(center["bgX"] * scale)
                y_scaled = int(center["bgY"] * scale)

                pixel = tuple(img_np[y_scaled, x_scaled][:3])
                matched_hex = closest_color(pixel)

                # ✅ Safely handle the case where closest_color returns a tuple instead of hex
                if isinstance(matched_hex, str):
                    hex_key = matched_hex.upper()
                else:
                    hex_key = "#{:02X}{:02X}{:02X}".format(*pixel)

                island_type = COLOR_MAP.get(hex_key, "Void")

                # === Combat/Boss/Minion logic ===
                combat_type_helper = None
                if center.get("bossX") and center.get("bossY"):
                    boss_x = int(center["bossX"] * scale)
                    boss_y = int(center["bossY"] * scale)
                    boss_pixel = tuple(img_np[boss_y, boss_x][:3])
                    if boss_pixel == hex_to_rgb("#E58F16"):
                        combat_type_helper = "boss"

                if center.get("minionX") and center.get("minionY"):
                    minion_x = int(center["minionX"] * scale)
                    minion_y = int(center["minionY"] * scale)
                    minion_pixel = tuple(img_np[minion_y, minion_x][:3])
                    if is_minion_color(minion_pixel):
                        combat_type_helper = "minion"

                lower_type = island_type.lower()
                if lower_type in ["easy", "medium", "hard"]:
                    category = combat_type_helper if combat_type_helper else "Battle"
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
                    "index": i,
                    "island_type": island_type,
                    "category": category
                })

            except Exception as e:
                logger.warning(f"⚠️ Error processing island {i}: {e}")

        # Run processing in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_island, i + 1, center) for i, center in enumerate(islandCenters)]
            [f.result() for f in futures]

        return jsonify({"island_data": sorted(results, key=lambda x: x["index"])})

    except Exception as e:
        logger.exception("❌ Unexpected error in extract_all_categories")
        return jsonify({"error": str(e)}), 500

@app.route('/crop_circle', methods=['POST'])
def crop_circle():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        ctx = ImageContext(image_url)
        x_scaled, y_scaled = int(x * ctx.scale), int(y * ctx.scale)
        radius = int(24 * ctx.scale)

        mask = Image.new("L", ctx.img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius), fill=255)

        cropped_img = Image.composite(ctx.img, Image.new("RGBA", ctx.img.size, (0, 0, 0, 0)), mask).crop(
            (x_scaled - radius, y_scaled - radius, x_scaled + radius, y_scaled + radius))

        label = find_best_match_icon_np(preprocess_crop(cropped_img), CONFIDENCE_THRESHOLD_CIRCLE)
        base64_result = image_to_base64(cropped_img)

        return jsonify({"label": label, "base64": base64_result})

    except Exception as e:
        logger.exception("Error in crop_circle")
        return jsonify({"error": str(e)})

@app.route('/crop_diamond', methods=['POST'])
def crop_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        ctx = ImageContext(image_url)
        crop = ctx.crop_diamond(x, y)
        label = find_best_match_icon_np(preprocess_crop(crop), CONFIDENCE_THRESHOLD_DIAMOND)
        base64_result = image_to_base64(crop)

        return jsonify({"label": label, "base64": base64_result})

    except Exception as e:
        logger.exception("Error in crop_diamond")
        return jsonify({"error": str(e)})
def crop_diamond_to_file(image_url, x, y, output_path="diamond_crop.png"):
    try:
        ctx = ImageContext(image_url)
        crop = ctx.crop_diamond(x, y)
        crop.save(output_path)
        return f"Saved diamond crop to {output_path}"
    except Exception as e:
        logger.exception("Error in crop_diamond_to_file")
        return f"Error: {str(e)}"

@app.route('/crop_small_diamond', methods=['POST'])
def crop_small_diamond():
    data = request.get_json()
    image_url = data.get("image_url")
    x, y = int(data.get("x")), int(data.get("y"))

    try:
        ctx = ImageContext(image_url)
        x_scaled, y_scaled = int(x * ctx.scale), int(y * ctx.scale)
        offset = int(32 * ctx.scale)

        crop_coords = [
            (x_scaled, y_scaled - offset), (x_scaled - offset, y_scaled),
            (x_scaled, y_scaled + offset), (x_scaled + offset, y_scaled)
        ]

        mask = Image.new("L", ctx.img.size, 0)
        ImageDraw.Draw(mask).polygon(crop_coords, fill=255)

        cropped_img = Image.composite(ctx.img, Image.new("RGBA", ctx.img.size, (0, 0, 0, 0)), mask).crop(
            (x_scaled - offset, y_scaled - offset, x_scaled + offset, y_scaled + offset))

        base64_result = image_to_base64(cropped_img)
        return jsonify({"image_base64": base64_result})

    except Exception as e:
        logger.exception("Error in crop_small_diamond")
        return jsonify({"error": str(e)})

@app.route('/arrow_check_bulk', methods=['POST'])
def arrow_check_bulk():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400

        ctx = ImageContext(image_url)

        def check_color(x, y):
            pixel = ctx.get_pixel(x, y)
            hex_color = "#{:02X}{:02X}{:02X}".format(*pixel[:3])
            accepted_colors = {
                "#F156FF", "#FFFFFF", "#2DB38F", "#ECD982", "#E5E4E2",
                "#FFD700", "#CD7F32", "#445566", "#F07E5F", "#EAE9E8"
            }
            return "arrow" if hex_color.upper() in accepted_colors else "no"

        def process_arrow_pair(entry):
            if entry == "x":
                return ["skip", "skip"]
            else:
                (x1, y1), (x2, y2) = entry
                return [check_color(x1, y1), check_color(x2, y2)]

        results = {
            "A": [process_arrow_pair(entry) for entry in arrowPointsA],
            "D": [process_arrow_pair(entry) for entry in arrowPointsD]
        }

        return jsonify(results)

    except Exception as e:
        logger.exception("Error in arrow_check_bulk")
        return jsonify({"error": str(e)}), 500

@app.route('/crop_all_decision_icons', methods=['POST'])
def crop_all_decision_icons():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        categories = data.get("categories", [])
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400
        if not categories or len(categories) != 25:
            return jsonify({"error": "categories must be a 25-item list"}), 400

        ctx = ImageContext(image_url)

        def process_icon(idx):
            point = icon_points[idx]
            category = categories[idx].strip().lower()
            left_result = {"id": f"L{idx+1}", "label": "", "base64": ""}
            right_result = {"id": f"R{idx+1}", "label": "", "base64": ""}

            try:
                if category == "decision":
                    left = best_shifted_match(ctx, point["leftX"], point["leftY"])
                    right = best_shifted_match(ctx, point["rightX"], point["rightY"])
                    left_result.update({"label": left["label"], "base64": left["base64"]})
                    right_result.update({"label": right["label"], "base64": right["base64"]})

                elif category in ["battle", "boss"]:
                    left_result["label"] = right_result["label"] = category

                elif "door" in category:
                    left_result["label"] = right_result["label"] = "𓉞"

                elif category in ["portal", "arrival", "shop"]:
                    left_result["label"] = "⋆₊˚⊹"
                    right_result["label"] = "࿔⋆"

            except Exception as e:
                logger.warning(f"[Icon {idx+1}] Failed: {str(e)}")

            return {"left": left_result, "right": right_result}

        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_icon, i) for i in range(25)]
            for f in as_completed(futures):
                results.append(f.result())

        results.sort(key=lambda r: int(r["left"]["id"][1:]))
        return jsonify({"icons": results})

    except Exception as e:
        logger.exception("Error in crop_all_decision_icons")
        return jsonify({"error": str(e)}), 500

@app.route('/crop_diamond_to_file', methods=['POST'])
def crop_diamond_to_file(image_url, x, y, output_path="diamond_crop.png"):
    try:
        ctx = ImageContext(image_url)
        crop = ctx.crop_diamond(x, y)
        crop.save(output_path)
        return f"Saved diamond crop to {output_path}"
    except Exception as e:
        logger.exception("Error in crop_diamond_to_file")
        return f"Error: {str(e)}"

@app.route('/status', methods=['GET'])
def status():
    return jsonify(priority_cache.get_cache_status())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), threaded=True)
