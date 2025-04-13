from utils.constants import RGB_COLOR_MAP

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def closest_color(pixel):
    best_match = None
    best_distance = float("inf")

    for ref_rgb, label in RGB_COLOR_MAP.items():
        dist = color_distance(pixel, ref_rgb)
        if dist < best_distance:
            best_distance = dist
            best_match = (ref_rgb, label)

    if best_match:
        ref_rgb, label = best_match

        # Variable thresholds based on label
        if label == "arrival":
            threshold = 4.0
        elif label == "portal":
            threshold = 1.5
        else:
            threshold = 1.1

        result = ref_rgb if best_distance < threshold else "other"
        return {
            "label": label,
            "matched_rgb": ref_rgb,
            "distance": best_distance,
            "result": result
        }

    return {
        "label": "none",
        "matched_rgb": None,
        "distance": None,
        "result": "other"
    }
