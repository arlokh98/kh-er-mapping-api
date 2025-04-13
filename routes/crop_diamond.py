from flask import Blueprint, request, jsonify
import os
import logging

from utils.image_context import ImageContext
from utils.constants import FULL_ISLAND_DATA

logger = logging.getLogger(__name__)
crop_diamond_bp = Blueprint("crop_diamond", __name__)

@crop_diamond_bp.route('/crop_diamond_to_file', methods=['POST'])
def crop_diamond_to_file():
    data = request.get_json()
    image_url = data.get("image_url")
    island_index = data.get("island_index")
    side = data.get("side")
    filename = data.get("filename", "cropped_icon.png")

    if not all([image_url, island_index, side, filename]):
        return jsonify({"error": "Missing one or more required fields: image_url, island_index, side, filename"}), 400

    try:
        i = island_index - 1
        if not (0 <= i < len(FULL_ISLAND_DATA)):
            return jsonify({"error": f"island_index must be between 1 and {len(FULL_ISLAND_DATA)}"}), 400

        island = FULL_ISLAND_DATA[i]
        if side == "left":
            x, y = island["icon_left"], island["icon_leftY"]
        elif side == "right":
            x, y = island["icon_right"], island["icon_rightY"]
        else:
            return jsonify({"error": "Side must be 'left' or 'right'"}), 400

        ctx = ImageContext(image_url)
        cropped_img = ctx.crop_diamond(x, y)

        os.makedirs("debug_icons", exist_ok=True)
        path = os.path.join("debug_icons", filename)
        cropped_img.save(path)

        return jsonify({"status": "success", "path": path})

    except Exception as e:
        logger.exception("❌ Error in crop_diamond_to_file")
        return jsonify({"error": str(e)}), 500
