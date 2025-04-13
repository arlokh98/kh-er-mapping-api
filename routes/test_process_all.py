from flask import Blueprint, request, jsonify
import base64, csv, io, os
from PIL import Image
import logging

test_process_all_bp = Blueprint("test_process_all", __name__)
logger = logging.getLogger(__name__)

@test_process_all_bp.route("/test_process_all", methods=["POST"])
def test_process_all():
    os.makedirs("debug_icons", exist_ok=True)

    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    try:
        from app import app  # Flask app instance
        with app.test_client() as client:
            resp = client.post("/process_all", json={"image_url": image_url})
            if resp.status_code != 200:
                return jsonify({"error": "process_all failed", "detail": resp.get_json()}), 500

            json_data = resp.get_json()
            islands = json_data.get("islands", [])
            arrows = json_data.get("arrows", {})

        saved_icons = []
        for island in islands:
            for side in ["icon1", "icon2"]:
                icon_data = island.get(side)
                if isinstance(icon_data, str) and len(icon_data) > 100:
                    try:
                        img_bytes = base64.b64decode(icon_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        path = f"debug_icons/island_{island['row']}_{island['col']}_{side}.png"
                        img.save(path)
                        saved_icons.append(path)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to save icon for {island['row']}, {island['col']}: {e}")

        # Write results to CSV
        csv_path = "debug_icons/island_results_detailed.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(islands[0].keys()))
            writer.writeheader()
            writer.writerows(islands)

        return jsonify({
            "status": "success",
            "icon_paths": saved_icons,
            "csv": csv_path,
            "result_count": len(islands),
            "arrow_summary": arrows
        })

    except Exception as e:
        logger.exception("💥 Error in test_process_all")
        return jsonify({"error": str(e)}), 500
