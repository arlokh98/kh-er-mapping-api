from flask import Blueprint, request, jsonify
from utils.image_context import ImageContext
from utils.constants import arrowPointsA, arrowPointsD, ARROW_A_MAPPING, ARROW_D_MAPPING
import logging

logger = logging.getLogger(__name__)
arrow_check_bp = Blueprint("arrow_check", __name__)

@arrow_check_bp.route('/arrow_check_bulk', methods=['POST'])
def arrow_check_bulk():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        if not image_url:
            return jsonify({"error": "Missing image_url"}), 400

        ctx = ImageContext(image_url)

        def check_color(x, y):
            pixel_rgb = tuple(ctx.get_pixel(x, y)[:3])
            accepted_rgb = {
                (241, 86, 255),   # decision
                (255, 255, 255),  # white
                (45, 179, 143),   # easy
                (236, 217, 130),  # medium
                (229, 228, 226),  # silver
                (255, 215, 0),    # gold
                (205, 127, 50),   # bronze
                (68, 85, 102),    # time
                (240, 126, 95),   # hard
                (234, 233, 232)   # shop gray
            }
            return "arrow" if pixel_rgb in accepted_rgb else "no"

        def classify_arrow_direction(c1, c2, direction_type):
            if c1 == "arrow" and c2 == "no":
                return "left" if direction_type == "A" else "up"
            elif c1 == "no" and c2 == "arrow":
                return "right" if direction_type == "A" else "down"
            else:
                return "voidArrow"

        def process_arrow_set(arrow_points, mapping, direction_type):
            output = []
            for i, entry in enumerate(arrow_points):
                mapped = mapping[i]

                # Handle skipped entries
                if entry == "x" or mapped is None:
                    direction = "voidArrow"
                    row, col = None, None
                else:
                    (x1, y1), (x2, y2) = entry
                    c1 = check_color(x1, y1)
                    c2 = check_color(x2, y2)
                    direction = classify_arrow_direction(c1, c2, direction_type)
                    row, col = mapped["row"], mapped["col"]

                output.append({
                    "row": row,
                    "col": col,
                    "direction": direction
                })

            return output

        # Final results for arrow sets
        results = {
            "A": process_arrow_set(arrowPointsA, ARROW_A_MAPPING, "A"),
            "D": process_arrow_set(arrowPointsD, ARROW_D_MAPPING, "D")
        }

        return jsonify(results)


    except Exception as e:
        logger.exception("Error in /arrow_check_bulk")
        return jsonify({"error": str(e)}), 500
