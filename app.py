from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw
import io
import os

app = Flask(__name__)

def download_image(image_url):
    response = requests.get(image_url)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGBA")
    return image

def crop_diamond(image, points, corner_round=20):
    # Create a mask with a diamond shape
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)

    # Draw polygon with slightly rounded corners by offsetting
    def rounded_point(p1, p2, radius):
        return (p1[0] + (p2[0] - p1[0]) * radius, p1[1] + (p2[1] - p1[1]) * radius)

    # Smooth polygon approximation (optional: simple polygon also works)
    draw.polygon(points, fill=255)

    # Crop to bounding box of the polygon
    bbox = mask.getbbox()
    cropped_img = Image.composite(image, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask)
    cropped_img = cropped_img.crop(bbox)
    return cropped_img

@app.route('/extract_color', methods=['GET'])
def extract_color():
    image_url = request.args.get("image_url")
    x = int(request.args.get("x", 0))
    y = int(request.args.get("y", 0))

    try:
        image = download_image(image_url)
        pixel = image.getpixel((x, y))
        hex_color = "#{:02X}{:02X}{:02X}".format(pixel[0], pixel[1], pixel[2])
        return jsonify({"hex": hex_color})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/crop_icon', methods=['GET', 'POST'])
def crop_icon():
    if request.method == 'POST':
        data = request.get_json()
        image_url = data.get("image_url")
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        side = data.get("side", "left")
    else:
        image_url = request.args.get("image_url")
        x = int(request.args.get("x", 0))
        y = int(request.args.get("y", 0))
        side = request.args.get("side", "left")

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # cropping logic continues here
        # and finally:
        byte_io = io.BytesIO()
        cropped_img.save(byte_io, 'PNG')
        byte_io.seek(0)
        return send_file(byte_io, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
