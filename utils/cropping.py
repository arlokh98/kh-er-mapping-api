import numpy as np
from PIL import Image, ImageDraw

def crop_diamond_np_array(img_np, x, y, scale, radius=None, size=(118, 118)):
    base_radius = 100 if radius is None else radius
    scaled_radius = int(base_radius * scale)

    sx, sy = int(x * scale), int(y * scale)

    # Diamond coordinates
    coords = [
        (sx, sy - scaled_radius),
        (sx - scaled_radius, sy),
        (sx, sy + scaled_radius),
        (sx + scaled_radius, sy)
    ]

    # Create mask
    mask = Image.new("L", (img_np.shape[1], img_np.shape[0]), 0)
    ImageDraw.Draw(mask).polygon(coords, fill=255)

    # Convert to RGBA PIL image
    if img_np.shape[2] == 3:
        full_img = Image.fromarray(img_np, mode="RGB").convert("RGBA")
    else:
        full_img = Image.fromarray(img_np, mode="RGBA")

    # Apply mask + crop
    masked_img = Image.composite(full_img, Image.new("RGBA", full_img.size), mask)
    cropped = masked_img.crop((sx - scaled_radius, sy - scaled_radius, sx + scaled_radius, sy + scaled_radius))

    # Grayscale + resize
    gray_resized = cropped.convert("L").resize(size)
    gray_np = np.array(gray_resized)

    return cropped, gray_np

def get_median_pixel(img_np, x, y):
    h, w, _ = img_np.shape
    pixels = []

    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                pixels.append(tuple(img_np[ny, nx]))

    if not pixels:
        return (0, 0, 0)

    # Sort by total intensity and return median
    pixels.sort(key=lambda p: sum(p))
    return pixels[len(pixels) // 2]
