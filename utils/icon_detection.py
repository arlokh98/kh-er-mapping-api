import io
import base64
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from utils.color_tools import color_distance
from utils.constants import MONSTER_ICON_COLORS
import glob
import os
from PIL import ImageDraw

# Used in template loader
icon_templates = {}

def preload_er_icon_templates(directories, er_scaled_size=118):
    global icon_templates
    for directory in directories:
        for file in glob.glob(f"{directory}/*.png"):
            img_pil = Image.open(file).convert("L")
            img_np = np.array(img_pil)
            scaled = img_pil.resize((er_scaled_size, er_scaled_size))
            scaled_np = np.array(scaled)
            name = os.path.basename(file).split(".")[0]
            icon_templates[name] = {
                "original": img_np,
                "er_scaled": scaled_np
            }

preload_er_icon_templates(["iconsER"])

# Bear background detection
BEAR_OVERLAY_COLORS = {
    (255, 182, 255),
    (255, 255, 255),
    (51, 68, 85)
}
RED_GRADIENT = [(128, 7, 8), (132, 31, 37)]

def is_red_pixel(pixel, tolerance=10):
    for red in RED_GRADIENT:
        diffs = [abs(p - r) for p, r in zip(pixel, red)]
        if all(d <= tolerance for d in diffs):
            return True
    return False

def is_bear_background(crop_img, red_threshold_ratio=0.15):
    rgb = np.array(crop_img.convert("RGB"))
    flat = rgb.reshape(-1, 3)
    total = 0
    red_count = 0

    for pixel in flat:
        px = tuple(pixel)
        if px in BEAR_OVERLAY_COLORS:
            continue
        total += 1
        if is_red_pixel(px):
            red_count += 1

    return (red_count / total) >= red_threshold_ratio if total else False

# Monster color extraction
def is_near_any_icon_color(pixel, max_distance=60):
    return any(color_distance(pixel, ref_rgb) <= max_distance for ref_rgb in MONSTER_ICON_COLORS)

def get_icon_core_color(crop_img, match_distance_threshold=60):
    rgba_np = np.array(crop_img.convert("RGBA"))
    total = 0
    sum_r = sum_g = sum_b = 0

    for px in rgba_np.reshape(-1, 4):
        r, g, b, a = map(int, px)
        if a == 0:
            continue
        if not is_near_any_icon_color((r, g, b), match_distance_threshold):
            continue
        sum_r += r
        sum_g += g
        sum_b += b
        total += 1

    if total == 0:
        return None
    return (sum_r // total, sum_g // total, sum_b // total)

def match_monster_label(rgb, return_distance=False):
    if not rgb:
        return ("other", None) if return_distance else "other"
    distances = []
    for label_rgb, label_name in MONSTER_ICON_COLORS.items():
        dist = color_distance(rgb, label_rgb)
        distances.append((label_name, dist))
    distances.sort(key=lambda x: x[1])
    best_label, best_dist = distances[0]
    return (best_label, best_dist) if return_distance else best_label

# SSIM-based decision icon matching
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

def best_shifted_match(img_np, scale, x, y, threshold=0.85, crop_fn=None):
    best_score = -1
    best_label = "other"
    best_crop = None
    shifts = [(0, 0)] + [(dx, dy) for shift in [1, 2] for dx in [-shift, 0, shift] for dy in [-shift, 0, shift] if not (dx == 0 and dy == 0)]

    from utils.cropping import crop_diamond_np_array
    for dx, dy in shifts:
        try:
            crop, gray_np = crop_diamond_np_array(img_np, x + dx, y + dy, scale)
            for name, template in icon_templates.items():
                score = ssim(gray_np, template["er_scaled"])
                if score > best_score:
                    best_score = score
                    best_label = name
                    best_crop = crop
        except Exception:
            continue

    return {
        "label": best_label if best_score >= threshold else "other",
        "score": best_score,
        "base64": image_to_base64(best_crop) if best_crop else None
    }

# For saving final icons
def image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
