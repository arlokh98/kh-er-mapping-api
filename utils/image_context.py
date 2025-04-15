import requests
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
from utils.cropping import crop_diamond_np_array
from utils.constants import REFERENCE_IMAGE_SIZE
import logging

logger = logging.getLogger(__name__)

class ImageContext:
    def __init__(self, image_url):
        self.image_url = image_url
        self.image = self._load_image()
        self.scale = self.image.width / REFERENCE_IMAGE_SIZE

        self.gray_image = self.image.convert("L")
        self.contrast_image = ImageEnhance.Contrast(self.gray_image).enhance(1.5)
        self.img_np = np.array(self.image.convert("RGB"))

    def _load_image(self):
        response = requests.get(self.image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to load image: {self.image_url}")
        return Image.open(io.BytesIO(response.content)).convert("RGBA")

    def get_pixel(self, x, y):
        sx, sy = int(x * self.scale), int(y * self.scale)
        return self.image.getpixel((sx, sy))

    def crop_diamond(self, x, y, radius=None):
        return crop_diamond_np_array(np.array(self.image), x, y, self.scale, radius)[0]
