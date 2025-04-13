import requests
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
from utils.cropping import crop_diamond_np_array
from utils.constants import REFERENCE_IMAGE_SIZE
from priority_cache_manager import get_priority_cache
priority_cache = get_priority_cache()
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
        cached = priority_cache.get_original(self.image_url)
        if cached:
            logger.debug(f"[Cache] Using cached original image")
            return cached

        response = requests.get(self.image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to load image: {self.image_url}")

        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        priority_cache.store_original(self.image_url, img)
        return img

    def get_pixel(self, x, y):
        sx, sy = int(x * self.scale), int(y * self.scale)
        return self.image.getpixel((sx, sy))

    def crop_diamond(self, x, y, radius=None):
        return crop_diamond_np_array(np.array(self.image), x, y, self.scale, radius)[0]
