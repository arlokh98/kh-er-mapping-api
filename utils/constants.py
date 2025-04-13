# utils/constants.py

REFERENCE_IMAGE_SIZE = 2810

RGB_COLOR_MAP = {
    (241, 86, 255): "decision",
    (45, 179, 143): "easy",
    (236, 217, 130): "medium",
    (240, 126, 95): "hard",
    (152, 67, 198): "portal",
    (204, 59, 91): "arrival",
    (215, 153, 91): "bronze",
    (234, 233, 232): "silver",
    (255, 223, 51): "gold",
    (109, 109, 229): "shop",
    (105, 119, 133): "time",
    (229, 143, 22): "boss"
}

MONSTER_ICON_COLORS = {
    (255, 182, 255): "beast",
    (112, 156, 255): "troll",
    (37, 196, 155): "cult",
    (255, 141, 120): "demon",
    (41, 207, 249): "undead",
    (255, 245, 184): "outlaw",
    (255, 255, 0): "militia",
    (255, 156, 0): "golem",
    (179, 226, 50): "goblin"
}

# FULL_ISLAND_DATA — full 25-island layout
FULL_ISLAND_DATA = [
    {"index": 0, "row": 1, "col": 1, "bgX": 1404.5, "bgY": 343.5, "bossX": 1406, "bossY": 170, "minionX": 1404, "minionY": 494, "icon_left": 1304, "icon_leftY": 343, "icon_right": 1504, "icon_rightY": 343},
    {"index": 1, "row": 3, "col": 1, "bgX": 1140.5, "bgY": 607.5, "bossX": 1142, "bossY": 434, "minionX": 1140, "minionY": 758, "icon_left": 1040, "icon_leftY": 607, "icon_right": 1240, "icon_rightY": 607},
    {"index": 2, "row": 1, "col": 3, "bgX": 1668.5, "bgY": 607.5, "bossX": 1670, "bossY": 434, "minionX": 1668, "minionY": 758, "icon_left": 1570, "icon_leftY": 607, "icon_right": 1770, "icon_rightY": 607},
    {"index": 3, "row": 5, "col": 1, "bgX": 876.5, "bgY": 871.5, "bossX": 878, "bossY": 698, "minionX": 876, "minionY": 1022, "icon_left": 776, "icon_leftY": 871, "icon_right": 976, "icon_rightY": 871},
    {"index": 4, "row": 3, "col": 3, "bgX": 1404.5, "bgY": 871.5, "bossX": 1406, "bossY": 698, "minionX": 1404, "minionY": 1022, "icon_left": 1304, "icon_leftY": 871, "icon_right": 1504, "icon_rightY": 871},
    {"index": 5, "row": 1, "col": 5, "bgX": 1932.5, "bgY": 871.5, "bossX": 1934, "bossY": 698, "minionX": 1932, "minionY": 1022, "icon_left": 1832, "icon_leftY": 871, "icon_right": 2032, "icon_rightY": 871},
    {"index": 6, "row": 7, "col": 1, "bgX": 612.5, "bgY": 1135.5, "bossX": 614, "bossY": 962, "minionX": 612, "minionY": 1286, "icon_left": 512, "icon_leftY": 1135, "icon_right": 712, "icon_rightY": 1135},
    {"index": 7, "row": 5, "col": 3, "bgX": 1140.5, "bgY": 1135.5, "bossX": 1142, "bossY": 962, "minionX": 1140, "minionY": 1286, "icon_left": 1040, "icon_leftY": 1135, "icon_right": 1240, "icon_rightY": 1135},
    {"index": 8, "row": 3, "col": 5, "bgX": 1668.5, "bgY": 1135.5, "bossX": 1670, "bossY": 962, "minionX": 1668, "minionY": 1286, "icon_left": 1570, "icon_leftY": 1135, "icon_right": 1770, "icon_rightY": 1135},
    {"index": 9, "row": 1, "col": 7, "bgX": 2196.5, "bgY": 1136.0, "bossX": 2199, "bossY": 963, "minionX": 2196, "minionY": 1287, "icon_left": 2098, "icon_leftY": 1135, "icon_right": 2298, "icon_rightY": 1135},
    {"index": 10, "row": 9, "col": 1, "bgX": 348.5, "bgY": 1399.5, "bossX": 350, "bossY": 1225, "minionX": 348, "minionY": 1550, "icon_left": 248, "icon_leftY": 1399, "icon_right": 448, "icon_rightY": 1399},
    {"index": 11, "row": 7, "col": 3, "bgX": 876.5, "bgY": 1399.5, "bossX": 878, "bossY": 1225, "minionX": 876, "minionY": 1550, "icon_left": 776, "icon_leftY": 1399, "icon_right": 976, "icon_rightY": 1399},
    {"index": 12, "row": 5, "col": 5, "bgX": 1404.5, "bgY": 1399.5, "bossX": 1406, "bossY": 1226, "minionX": 1404, "minionY": 1550, "icon_left": 1304, "icon_leftY": 1399, "icon_right": 1504, "icon_rightY": 1399},
    {"index": 13, "row": 3, "col": 7, "bgX": 1932.5, "bgY": 1399.0, "bossX": 1934, "bossY": 1226, "minionX": 1932, "minionY": 1549, "icon_left": 1832, "icon_leftY": 1399, "icon_right": 2032, "icon_rightY": 1399},
    {"index": 14, "row": 1, "col": 9, "bgX": 2460.5, "bgY": 1400.0, "bossX": 2462, "bossY": 1226, "minionX": 2460, "minionY": 1550, "icon_left": 2360, "icon_leftY": 1399, "icon_right": 2560, "icon_rightY": 1399},
    {"index": 15, "row": 9, "col": 3, "bgX": 612.5, "bgY": 1663.5, "bossX": 614, "bossY": 1489, "minionX": 612, "minionY": 1814, "icon_left": 512, "icon_leftY": 1663, "icon_right": 712, "icon_rightY": 1663},
    {"index": 16, "row": 7, "col": 5, "bgX": 1140.5, "bgY": 1663.0, "bossX": 1142, "bossY": 1489, "minionX": 1140, "minionY": 1813, "icon_left": 1040, "icon_leftY": 1663, "icon_right": 1240, "icon_rightY": 1663},
    {"index": 17, "row": 5, "col": 7, "bgX": 1668.5, "bgY": 1663.5, "bossX": 1670, "bossY": 1489, "minionX": 1668, "minionY": 1814, "icon_left": 1570, "icon_leftY": 1663, "icon_right": 1770, "icon_rightY": 1663},
    {"index": 18, "row": 3, "col": 9, "bgX": 2196.5, "bgY": 1663.0, "bossX": 2199, "bossY": 1489, "minionX": 2196, "minionY": 1813, "icon_left": 2098, "icon_leftY": 1663, "icon_right": 2298, "icon_rightY": 1663},
    {"index": 19, "row": 9, "col": 5, "bgX": 876.5, "bgY": 1927.5, "bossX": 878, "bossY": 1753, "minionX": 876, "minionY": 2077, "icon_left": 776, "icon_leftY": 1927, "icon_right": 976, "icon_rightY": 1927},
    {"index": 20, "row": 7, "col": 7, "bgX": 1404.5, "bgY": 1927.5, "bossX": 1406, "bossY": 1753, "minionX": 1404, "minionY": 2077, "icon_left": 1304, "icon_leftY": 1927, "icon_right": 1504, "icon_rightY": 1927},
    {"index": 21, "row": 5, "col": 9, "bgX": 1932.5, "bgY": 1928.0, "bossX": 1934, "bossY": 1754, "minionX": 1932, "minionY": 2079, "icon_left": 1832, "icon_leftY": 1927, "icon_right": 2032, "icon_rightY": 1927},
    {"index": 22, "row": 9, "col": 7, "bgX": 1140.5, "bgY": 2191.5, "bossX": 1142, "bossY": 2017, "minionX": 1140, "minionY": 2340, "icon_left": 1040, "icon_leftY": 2191, "icon_right": 1240, "icon_rightY": 2191},
    {"index": 23, "row": 7, "col": 9, "bgX": 1668.5, "bgY": 2192.0, "bossX": 1670, "bossY": 2018, "minionX": 1668, "minionY": 2341, "icon_left": 1570, "icon_leftY": 2191, "icon_right": 1770, "icon_rightY": 2191},
    {"index": 24, "row": 9, "col": 9, "bgX": 1404.5, "bgY": 2455.5, "bossX": 1406, "bossY": 2281, "minionX": 1404, "minionY": 2603, "icon_left": 1304, "icon_leftY": 2455, "icon_right": 1504, "icon_rightY": 2455}
]

# Arrow points used in arrow_check_bulk (actual mapping rows/cols live in arrow_mapping.py)
arrowPointsA = [
    'x', 'x', [[1558, 497], [1515, 454]], 'x', [[1294, 761], [1251, 718]], [[1822, 761], [1779, 718]],
    'x', [[1030, 1025], [987, 982]], [[1558, 1025], [1515, 982]], [[2086, 1025], [2043, 982]], 'x',
    [[766, 1289], [723, 1246]], [[1294, 1289], [1251, 1246]], [[1822, 1289], [1779, 1246]], [[2350, 1289], [2307, 1246]],
    [[502, 1553], [459, 1510]], [[1030, 1553], [987, 1510]], [[1558, 1553], [1515, 1510]], [[2086, 1553], [2043, 1510]],
    [[766, 1817], [723, 1774]], [[1294, 1817], [1251, 1774]], [[1822, 1817], [1779, 1774]], [[1030, 2081], [987, 2038]],
    [[1558, 2081], [1515, 2038]], [[1294, 2345], [1251, 2302]]
]

arrowPointsD = [
    [[1251, 497], [1294, 454]], 'x', [[987, 761], [1030, 718]], [[1515, 761], [1558, 718]], 'x',
    [[723, 1025], [766, 982]], [[1251, 1025], [1294, 982]], [[1779, 1025], [1822, 982]], 'x',
    [[459, 1289], [502, 1246]], [[987, 1289], [1030, 1246]], [[1515, 1289], [1558, 1246]], [[2043, 1289], [2086, 1246]],
    'x', [[723, 1553], [766, 1510]], [[1251, 1553], [1294, 1510]], [[1779, 1553], [1822, 1510]], [[2307, 1553], [2350, 1510]],
    [[987, 1817], [1030, 1774]], [[1515, 1817], [1558, 1774]], [[2043, 1817], [2086, 1774]], [[1251, 2081], [1294, 2038]],
    [[1779, 2081], [1822, 2038]], [[1515, 2345], [1558, 2302]]
]


# Arrow A index → frontend (row, col) mapping (left/right logic)
ARROW_A_MAPPING = [
    None, None,
    {"row": 1, "col": 0},
    None,
    {"row": 3, "col": 0},
    {"row": 1, "col": 2},
    None,
    {"row": 5, "col": 0},
    {"row": 3, "col": 2},
    {"row": 1, "col": 4},
    None,
    {"row": 7, "col": 0},
    {"row": 5, "col": 2},
    {"row": 3, "col": 4},
    {"row": 1, "col": 6},
    {"row": 9, "col": 0},
    {"row": 7, "col": 2},
    {"row": 5, "col": 4},
    {"row": 3, "col": 6},
    {"row": 9, "col": 2},
    {"row": 7, "col": 4},
    {"row": 5, "col": 6},
    {"row": 9, "col": 4},
    {"row": 7, "col": 6},
    {"row": 9, "col": 6}
]

# Arrow D index → frontend (row, col) mapping (up/down logic)
ARROW_D_MAPPING = [
    {"row": 0, "col": 1},
    None,
    {"row": 2, "col": 1},
    {"row": 0, "col": 3},
    {"row": 4, "col": 1},
    {"row": 2, "col": 3},
    {"row": 0, "col": 5},
    {"row": 6, "col": 1},
    {"row": 4, "col": 3},
    {"row": 2, "col": 5},
    {"row": 0, "col": 7},
    {"row": 8, "col": 1},
    {"row": 6, "col": 3},
    {"row": 4, "col": 5},
    {"row": 2, "col": 7},
    {"row": 0, "col": 9},
    {"row": 8, "col": 3},
    {"row": 6, "col": 5},
    {"row": 4, "col": 7},
    {"row": 2, "col": 9},
    {"row": 8, "col": 5},
    {"row": 6, "col": 7},
    {"row": 4, "col": 9},
    {"row": 8, "col": 7},
    {"row": 6, "col": 9},
    {"row": 8, "col": 9}
]
