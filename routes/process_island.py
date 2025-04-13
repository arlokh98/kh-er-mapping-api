from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import logging

from utils.image_context import ImageContext
from utils.cropping import crop_diamond_np_array, get_median_pixel
from utils.icon_detection import (
    is_bear_background,
    match_monster_label,
    image_to_base64,
    best_shifted_match,
    get_icon_core_color
)
from utils.color_tools import closest_color
from utils.island_checks import is_minion_color
from utils.constants import FULL_ISLAND_DATA, RGB_COLOR_MAP

logger = logging.getLogger(__name__)
process_island_bp = Blueprint("process_island", __name__)

@process_island_bp.route("/process_island", methods=["POST"])
def process_island():
    data = request.get_json()
    image_url = data.get("image_url")
    logger.info(f" [process_island] Image URL received: {image_url}")

    try:
        ctx = ImageContext(image_url)
        img_np = ctx.img_np
        scale = ctx.scale
        results = [None] * len(FULL_ISLAND_DATA)

        def process_monster_icon(island, side):
            x = island["icon_left"] if side == "left" else island["icon_right"]
            y = island["icon_leftY"] if side == "left" else island["icon_rightY"]
            full_crop_img, _ = crop_diamond_np_array(img_np, x, y, scale)

            if is_bear_background(full_crop_img):
                return image_to_base64(full_crop_img)

            small_crop_img, _ = crop_diamond_np_array(img_np, x, y, scale, radius=70)
            avg_rgb = get_icon_core_color(small_crop_img)

            if not avg_rgb:
                return "other"

            return match_monster_label(avg_rgb)

        def process_decision_icon(x, y):
            match = best_shifted_match(img_np, scale, x, y)
            return match["base64"] if match["label"] == "other" else match["label"]

        def process_single_island(island):
            try:
                index = island["index"]
                x_scaled = int(island["bgX"] * scale)
                y_scaled = int(island["bgY"] * scale)

                pixel = get_median_pixel(img_np, x_scaled, y_scaled)
                pixel_rgb = tuple(map(int, pixel)) if pixel else None
                color_info = closest_color(pixel_rgb)

                matched_rgb = tuple(map(int, color_info["matched_rgb"])) if color_info["matched_rgb"] else None
                color_label = color_info["label"]
                distance = color_info["distance"]
                island_type = RGB_COLOR_MAP.get(matched_rgb, "Void") if color_info["result"] != "other" else "Void"
                lower_type = island_type.lower()

                # Boss/minion marker
                combat_type_helper = None
                bx, by = int(island["bossX"] * scale), int(island["bossY"] * scale)
                if tuple(img_np[by, bx][:3]) == (229, 143, 22):
                    combat_type_helper = "boss"
                mx, my = int(island["minionX"] * scale), int(island["minionY"] * scale)
                if is_minion_color(tuple(img_np[my, mx][:3])):
                    combat_type_helper = "minion"

                if lower_type in ["easy", "medium", "hard"]:
                    category = combat_type_helper or "battle"
                elif lower_type == "decision":
                    category = "decision"
                elif lower_type == "shop":
                    category = "shop"
                elif lower_type in ["portal", "arrival"]:
                    category = "portal"
                elif lower_type in ["bronze", "silver", "gold", "time"]:
                    category = "door"
                else:
                    category = "void"

                subtype = (
                    "gold" if "gold" in lower_type else
                    "silver" if "silver" in lower_type else
                    "bronze" if "bronze" in lower_type else
                    "time" if "time" in lower_type else
                    lower_type
                )

                frontend_category = "Battle" if category in ["boss", "minion", "battle"] else category.capitalize()
                type_ = category

                icon1 = icon2 = None
                if frontend_category == "Battle":
                    icon1 = process_monster_icon(island, "left")
                    icon2 = process_monster_icon(island, "right")
                elif frontend_category == "Decision":
                    icon1 = process_decision_icon(island["icon_left"], island["icon_leftY"])
                    icon2 = process_decision_icon(island["icon_right"], island["icon_rightY"])

                results[index] = {
                    "row": island["row"],
                    "col": island["col"],
                    "type": type_,
                    "category": frontend_category,
                    "subtype": subtype,
                    "icon1": icon1,
                    "icon2": icon2,
                    "centerX": x_scaled,
                    "centerY": y_scaled,
                    "pixel_rgb": pixel_rgb,
                    "matched_rgb": matched_rgb,
                    "color_label": color_label,
                    "distance": round(float(distance), 2) if distance is not None else None
                }

            except Exception as e:
                logger.warning(f" Error processing island {island.get('index')}: {e}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(process_single_island, FULL_ISLAND_DATA)

        return jsonify({"islands": results})

    except Exception as e:
        logger.exception(" Unexpected error in /process_island")
        return jsonify({"error": str(e)}), 500
