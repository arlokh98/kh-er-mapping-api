from utils.color_tools import color_distance

# RGB values that indicate combat backgrounds (should not be treated as minion)
CANNOT_BE_MINION_RGB = {
    (45, 179, 143),   # easy
    (236, 217, 130),  # medium
    (240, 126, 95)    # hard
}

MONSTER_RGB = (38, 43, 52)
MONSTER_THRESHOLD = 10  # Allow fuzzy match for dark monster base

def is_monster_color(pixel_rgb):
    return color_distance(pixel_rgb, MONSTER_RGB) <= MONSTER_THRESHOLD

def is_minion_color(pixel_rgb):
    if pixel_rgb in CANNOT_BE_MINION_RGB or is_monster_color(pixel_rgb):
        return False
    return True
