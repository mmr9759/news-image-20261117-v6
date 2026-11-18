#!/usr/bin/env python3
"""THE WORLD TODAY - Tuesday 17 November 2026.
Draws a one-page newspaper front page summing up the day's world news:
48 real stories from 17 November 2026, six continents, 12 illustrated
panels and a world map. Pure standard library, no network, deterministic.
Writes only to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import os
import struct
import sys
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
NAVY = (20, 38, 74)
RED = (179, 32, 44)
GOLD = (198, 148, 52)
GREY = (110, 108, 100)
LIGHT = (232, 226, 210)
BLUE = (52, 96, 148)
SEA = (168, 196, 214)
GREEN = (62, 110, 74)
ORANGE = (214, 110, 44)

# ---------------------------------------------------------------- PNG writer
def write_png(path, rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            row = bytes(c) * (x1 - x0)
            self.px[i:i + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)

    def tri(self, a, b, c_, col):
        self.poly([a, b, c_], col)

# --------------------------------------------------------------------- font
# 5x7 bitmap font, '#' = on, '.' = off. 7 rows per glyph.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
}

def text_w(s, scale):
    return len(s) * 6 * scale - scale

def draw_text(cv, x, y, s, color, scale=1):
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT['?'])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    cv.fill(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx

def wrap(s, max_chars):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if len(t) <= max_chars:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

# ------------------------------------------------------------- the 48 stories
# (region, headline) - every headline is a real event of 17 Nov 2026.
STORIES = [
    ("ME", "US strikes Iran's Qeshm Island after attacks on US forces"),
    ("ME", "Fourth tanker hit by mine in Strait of Hormuz; IRGC seizes drone"),
    ("ME", "Oman evacuates 24 seafarers from burning gas tanker Tara Gas"),
    ("ME", "Iran fires drones at US targets in Bahrain, third attack in 4 days"),
    ("ME", "Houthis launch drones at Saudi pipeline pumping stations"),
    ("ME", "Saudi Arabia replaces anti-Houthi coalition commander"),
    ("ME", "West urges Israel to open Gaza crossings as aid crisis deepens"),
    ("ME", "UN: winter rains flood Gaza shelters, worsen food crisis"),
    ("ME", "Israeli airstrikes and shelling hit southern Lebanon"),
    ("ME", "Israeli settlers shoot dead Palestinian woman near Jericho"),
    ("ME", "Houthi advance pushes Yemeni army back from Red Sea coast"),
    ("ME", "Dubai airport traffic falls 28.1%; job payouts top AED 250m"),
    ("EU", "Ukraine strikes Crimean Bridge again; main span collapses"),
    ("EU", "Russia hits Kyiv bridges after Crimean Bridge attack"),
    ("EU", "Russian missiles hit Kyiv, cutting heat and water"),
    ("EU", "Russian strike on Zaporizhzhia kills 40; aid centre hit kills 26"),
    ("EU", "Russia says it downed 300+ drones headed for Moscow"),
    ("EU", "Depardieu pleads guilty, drops appeal in sex assault case"),
    ("EU", "Man charged over attack on US military plane in Ireland"),
    ("EU", "Germany thrash Netherlands 5-0"),
    ("EU", "Eastern Europe crypto activity drops 7.9% in a year"),
    ("EU", "Five EU states plan a Rwanda deportation hub for 2027"),
    ("AP", "Trump, Xi and Putin set for first three-way summit in Shenzhen"),
    ("AP", "Putin arrives in Shenzhen for APEC summit"),
    ("AP", "Xi urges free trade as China hosts Asia-Pacific forum"),
    ("AP", "Modi joins ASEAN-India summit in Manila"),
    ("AP", "Quad leaders unveil minerals pacts at Manila summit"),
    ("AP", "India and Japan hold 2+2 defence and foreign ministers' talks"),
    ("AP", "Japan scrambles jets as Russian planes enter its airspace"),
    ("AP", "India edge Pakistan in U19 Asia Cup final thriller"),
    ("AP", "Pakistan cuts petrol and diesel prices by Rs2 a litre"),
    ("AP", "ECO summit adopts Vision 2035 in Islamabad"),
    ("AM", "Wall Street falls as AI and tech stocks slide; Nvidia in focus"),
    ("AM", "US loses measles elimination status, health body announces"),
    ("AM", "Trump takes CNN 'dirty bomb' report seriously; Iran denies plot"),
    ("AM", "US tightens AI chip export rules to block China's access"),
    ("AM", "Apple sign-in and App Store outages resolved"),
    ("AM", "Rocket failure destroys Amazon satellite payload"),
    ("AM", "Rosary beads thrown at Pope Leo during Peru visit"),
    ("CL", "COP31 draft deal calls for faster fossil-fuel phase-out"),
    ("AF", "DR Congo Ebola out of control, 5,500 dead, Africa CDC says"),
    ("AF", "Seventeen dead in two mass shootings in South Africa"),
    ("AF", "Guinea arrests 1,200 in Siguiri gold-mining crackdown"),
    ("AF", "ANC clings to national lead as coalition talks shape landscape"),
    ("OC", "Australia sanctions Israeli settlers, construction company"),
    ("OC", "Qantas flight diverts to Auckland after technical issue"),
    ("OC", "NZ publishes 58-nation visa waiver list"),
    ("OC", "Pacific Forum tests maritime security plan in Suva"),
]

LEAD_HEAD = ["U.S. STRIKES IRAN'S", "QESHM ISLAND AS", "HORMUZ STAND-OFF", "DEEPENS"]
LEAD_BODY = (
    "US warplanes hit a missile site on Qeshm Island in retaliation for "
    "Iranian attacks on American personnel in Bahrain, as a fourth tanker "
    "was hit by a mine in the Strait of Hormuz and Oman evacuated 24 "
    "seafarers from a burning gas tanker. Mediators in Oman and Qatar are "
    "seeking an end to the nine-month war."
)

# ---------------------------------------------------------------- world map
# Rough continent polygons in map-panel coordinates (476 x 164 space).
CONTINENTS = [
    [(10, 10), (60, 4), (110, 8), (150, 14), (160, 30), (140, 45), (120, 52),
     (110, 70), (95, 78), (80, 74), (60, 60), (40, 55), (25, 45), (8, 30)],
    [(150, 90), (170, 88), (185, 100), (190, 120), (180, 145), (165, 158),
     (150, 140), (140, 115)],
    [(160, 4), (175, 2), (180, 12), (168, 16)],
    [(235, 18), (255, 10), (270, 16), (275, 30), (265, 42), (250, 48),
     (238, 40), (230, 28)],
    [(235, 60), (255, 55), (275, 58), (290, 70), (295, 90), (285, 115),
     (265, 135), (248, 128), (238, 105), (232, 80)],
    [(275, 10), (320, 4), (380, 6), (430, 14), (455, 25), (470, 40),
     (450, 55), (420, 70), (400, 80), (370, 75), (340, 65), (310, 60),
     (290, 50), (278, 35), (272, 20)],
    [(400, 95), (420, 92), (435, 100), (420, 108), (405, 105)],
    [(400, 125), (430, 120), (455, 128), (460, 142), (440, 152), (410, 148),
     (395, 138)],
    [(238, 22), (244, 20), (246, 28), (240, 30)],
]
# (x, y, label) story dots on the map.
DOTS = [
    (299, 61, "HORMUZ"), (270, 56, "GAZA"), (264, 32, "KYIV"),
    (270, 38, "CRIMEA"), (228, 33, "PARIS"), (409, 51, "TOKYO"),
    (385, 76, "MANILA"), (376, 67, "SHENZHEN"), (127, 43, "NEW YORK"),
    (321, 53, "ISLAMABAD"), (284, 78, "ADEN"), (271, 53, "LEBANON"),
]

def draw_map(cv, mx, my):
    cv.fill(mx, my, 476, 164, SEA)
    for pts in CONTINENTS:
        cv.poly([(mx + x, my + y) for x, y in pts], (216, 205, 170))
    for pts in CONTINENTS:
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            cv.line(mx + x0, my + y0, mx + x1, my + y1, (150, 140, 115))
    for (x, y, lab) in DOTS:
        cv.disc(mx + x, my + y, 4, RED)
        cv.disc(mx + x, my + y, 2, (255, 255, 255))
    draw_text(cv, mx + 4, my + 2, "NORTH AMERICA", INK, 1)
    draw_text(cv, mx + 300, my + 2, "ASIA", INK, 1)
    draw_text(cv, mx + 238, my + 140, "AFRICA", INK, 1)
    draw_text(cv, mx + 150, my + 150, "S. AMERICA", INK, 1)
    draw_text(cv, mx + 405, my + 152, "OCEANIA", INK, 1)
    draw_text(cv, mx + 228, my + 52, "EUROPE", INK, 1)

# ------------------------------------------------------- illustrated panels
def scene_tanker(cv, x, y, w, h):
    cv.fill(x, y, w, h, SEA)
    cv.fill(x, y + h - 26, w, 26, (38, 74, 110))
    cv.fill(x + 18, y + h - 44, w - 36, 18, (30, 30, 30))
    cv.fill(x + 30, y + h - 58, 26, 16, (30, 30, 30))
    cv.tri((x + 60, y + 8), (x + 74, y + 34), (x + 88, y + 8), ORANGE)
    cv.tri((x + 84, y + 14), (x + 96, y + 34), (x + 108, y + 14), RED)
    cv.fill(x + 62, y + h - 62, 44, 4, (60, 60, 60))

def scene_bridge(cv, x, y, w, h):
    cv.fill(x, y, w, h, (190, 205, 220))
    cv.fill(x, y + h - 30, w, 30, SEA)
    cv.fill(x + 8, y + 34, w - 16, 8, (90, 90, 95))
    cv.line(x + 30, y + 6, x + 30, y + 34, (70, 70, 75))
    cv.line(x + w - 30, y + 6, x + w - 30, y + 34, (70, 70, 75))
    cv.line(x + 30, y + 6, x + w // 2, y + 34, (70, 70, 75))
    cv.line(x + w - 30, y + 6, x + w // 2, y + 34, (70, 70, 75))
    cv.tri((x + w // 2 - 14, y + 42), (x + w // 2, y + 30), (x + w // 2 + 14, y + 42), RED)
    cv.fill(x + w // 2 - 26, y + h - 18, 52, 6, (60, 60, 65))

def scene_jet(cv, x, y, w, h):
    cv.fill(x, y, w, h, (176, 200, 226))
    cv.fill(x + 20, y + 30, 90, 10, (60, 64, 70))
    cv.tri((x + 110, y + 30), (x + 140, y + 35), (x + 110, y + 40), (60, 64, 70))
    cv.tri((x + 55, y + 30), (x + 70, y + 8), (x + 80, y + 30), (60, 64, 70))
    cv.tri((x + 55, y + 40), (x + 70, y + 62), (x + 80, y + 40), (60, 64, 70))
    cv.disc(x + 30, y + 35, 4, RED)
    cv.fill(x, y + h - 14, w, 14, (120, 140, 160))

def scene_chip(cv, x, y, w, h):
    cv.fill(x, y, w, h, (24, 30, 44))
    cv.fill(x + w // 2 - 26, y + 10, 52, 40, (40, 90, 70))
    cv.fill(x + w // 2 - 16, y + 20, 32, 20, (24, 30, 44))
    draw_text(cv, x + w // 2 - 8, y + 24, "AI", (120, 220, 180), 1)
    for i in range(5):
        cv.fill(x + w // 2 - 26 + i * 11, y + 4, 4, 6, GOLD)
        cv.fill(x + w // 2 - 26 + i * 11, y + 50, 4, 6, GOLD)
        cv.fill(x + w // 2 - 32, y + 14 + i * 8, 6, 4, GOLD)
        cv.fill(x + w // 2 + 26, y + 14 + i * 8, 6, 4, GOLD)
    cv.line(x + 14, y + 60, x + w - 14, y + 60, RED)

def scene_court(cv, x, y, w, h):
    cv.fill(x, y, w, h, (226, 214, 190))
    cv.fill(x + 14, y + 44, w - 28, 6, (120, 90, 60))
    cv.line(x + 24, y + 50, x + 24, y + h - 8, (120, 90, 60))
    cv.line(x + w - 24, y + 50, x + w - 24, y + h - 8, (120, 90, 60))
    cv.fill(x + w // 2 - 24, y + 18, 48, 8, (90, 60, 40))
    cv.fill(x + w // 2 - 4, y + 26, 8, 18, (90, 60, 40))
    cv.fill(x + w // 2 - 30, y + 10, 60, 6, (90, 60, 40))

def scene_summit(cv, x, y, w, h):
    cv.fill(x, y, w, h, (250, 214, 150))
    cv.fill(x, y + h - 20, w, 20, (120, 60, 50))
    for i, c in enumerate(((179, 32, 44), (30, 60, 120), (198, 148, 52))):
        cx = x + 34 + i * 44
        cv.disc(cx, y + 34, 12, c)
        cv.fill(cx - 12, y + 46, 24, 16, c)
    cv.fill(x + 20, y + 58, w - 40, 4, (90, 60, 40))

def scene_manila(cv, x, y, w, h):
    cv.fill(x, y, w, h, (150, 190, 220))
    cv.fill(x, y + h - 24, w, 24, (60, 110, 90))
    cv.fill(x + 20, y + 18, 26, 34, (230, 220, 200))
    cv.fill(x + 56, y + 8, 30, 44, (200, 190, 170))
    cv.tri((x + 56, y + 8), (x + 71, y - 2), (x + 86, y + 8), (160, 60, 60))
    cv.fill(x + 100, y + 26, 24, 26, (230, 220, 200))
    cv.disc(x + 122, y + 14, 8, GOLD)

def scene_kyiv(cv, x, y, w, h):
    cv.fill(x, y, w, h, (60, 66, 80))
    cv.fill(x, y + h - 22, w, 22, (30, 32, 40))
    for i in range(3):
        bx = x + 16 + i * 44
        cv.fill(bx, y + 26, 30, h - 48, (110, 112, 124))
        cv.fill(bx + 6, y + 32, 6, 6, GOLD)
        cv.fill(bx + 18, y + 32, 6, 6, GOLD)
    cv.tri((x + 60, y + 4), (x + 72, y + 26), (x + 84, y + 4), ORANGE)
    cv.tri((x + 100, y + 10), (x + 110, y + 26), (x + 120, y + 10), RED)

def scene_ebola(cv, x, y, w, h):
    cv.fill(x, y, w, h, (220, 235, 225))
    cv.disc(x + w // 2, y + 30, 16, (90, 40, 60))
    for i in range(8):
        ang = i * 3.14159 / 4
        import math
        ex = int(x + w // 2 + 24 * math.cos(ang))
        ey = int(y + 30 + 24 * math.sin(ang))
        cv.line(x + w // 2, y + 30, ex, ey, (90, 40, 60))
    cv.disc(x + w // 2, y + 30, 6, (220, 235, 225))
    cv.fill(x + 16, y + h - 22, w - 32, 4, RED)

def scene_market(cv, x, y, w, h):
    cv.fill(x, y, w, h, (20, 36, 30))
    pts = [(x + 8, y + 18), (x + 34, y + 30), (x + 60, y + 24), (x + 86, y + 40),
           (x + 112, y + 34), (x + 138, y + 54)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED)
    for p in pts:
        cv.disc(p[0], p[1], 3, RED)
    cv.line(x + 8, y + h - 12, x + w - 8, y + h - 12, (120, 140, 120))
    draw_text(cv, x + 12, y + h - 10, "-3.1%", (255, 120, 120), 1)

def scene_cricket(cv, x, y, w, h):
    cv.fill(x, y, w, h, (120, 170, 90))
    cv.fill(x, y + h - 18, w, 18, (90, 140, 70))
    cv.fill(x + w // 2 - 3, y + 12, 6, 40, GOLD)
    cv.fill(x + w // 2 - 12, y + 52, 24, 6, GOLD)
    cv.fill(x + w // 2 + 20, y + 20, 18, 6, (120, 80, 50))
    cv.disc(x + w // 2 + 30, y + 14, 5, RED)
    cv.disc(x + 20, y + 60, 5, (255, 255, 255))

def scene_climate(cv, x, y, w, h):
    cv.fill(x, y, w, h, (200, 225, 235))
    cv.disc(x + 30, y + 22, 12, GOLD)
    cv.fill(x + 60, y + 16, 70, 10, (240, 240, 240))
    cv.fill(x + 70, y + 30, 60, 10, (240, 240, 240))
    cv.tri((x + 30, y + 44), (x + 44, y + 62), (x + 58, y + 44), GREEN)
    cv.tri((x + 58, y + 40), (x + 74, y + 62), (x + 90, y + 40), GREEN)
    cv.tri((x + 88, y + 44), (x + 102, y + 62), (x + 116, y + 44), GREEN)
    cv.fill(x + 20, y + 62, w - 40, 4, GREEN)

PANELS = [
    ("HORMUZ ON FIRE", "Tanker ablaze in strait", scene_tanker),
    ("BRIDGE DOWN", "Crimean Bridge span falls", scene_bridge),
    ("JETS SCRAMBLED", "Japan intercepts jets", scene_jet),
    ("CHIP CURBS", "US tightens AI chip rules", scene_chip),
    ("COURTROOM", "Depardieu pleads guilty", scene_court),
    ("SUMMIT IN SHENZHEN", "Trump, Xi, Putin to meet", scene_summit),
    ("MANILA", "Quad minerals pact agreed", scene_manila),
    ("KYIV UNDER FIRE", "Missiles cut heat, water", scene_kyiv),
    ("EBOLA", "DR Congo Ebola outbreak", scene_ebola),
    ("WALL STREET", "Stocks slide, tech slumps", scene_market),
    ("CRICKET THRILLER", "India beat Pakistan by 1", scene_cricket),
    ("CLIMATE", "COP31: phase out fuels", scene_climate),
]

# ------------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    cv.fill(0, 0, W, 6, GOLD)

    # Masthead
    cv.fill(0, 6, W, 92, NAVY)
    title = "THE WORLD TODAY"
    draw_text(cv, (W - text_w(title, 5)) // 2, 16, title, (255, 255, 255), 5)
    sub = "TUESDAY 17 NOVEMBER 2026  |  48 STORIES  |  SIX CONTINENTS  |  DATE CHECKED"
    draw_text(cv, (W - text_w(sub, 1)) // 2, 66, sub, GOLD, 1)
    cv.fill(16, 92, W - 32, 2, RED)

    # Lead story (left) + world map (right)
    draw_text(cv, 16, 108, "LEAD STORY", RED, 1)
    y = 128
    for ln in LEAD_HEAD:
        draw_text(cv, 16, y, ln, INK, 3)
        y += 24
    cv.fill(16, y + 2, 484, 2, RED)
    y += 12
    for ln in wrap(LEAD_BODY, 78):
        draw_text(cv, 16, y, ln, INK, 1)
        y += 11

    draw_text(cv, 516, 108, "WHERE THE NEWS HAPPENED", INK, 1)
    cv.rect(516, 122, 492, 180, INK, 1)
    draw_map(cv, 524, 130)
    draw_text(cv, 516, 306, "Red dots mark the day's flashpoints.", GREY, 1)

    # 12 illustrated panels
    draw_text(cv, 16, 326, "12 STORIES IN PICTURES", NAVY, 2)
    cv.fill(16, 348, W - 32, 2, NAVY)
    pw, gap, ph = 160, 6, 108
    for i, (t, cap, fn) in enumerate(PANELS):
        px = 17 + (i % 6) * (pw + gap)
        py = 358 + (i // 6) * (ph + 8)
        cv.rect(px, py, pw, ph, INK, 1)
        fn(cv, px + 1, py + 1, pw - 2, 74)
        draw_text(cv, px + 5, py + 79, t, INK, 1)
        draw_text(cv, px + 5, py + 91, cap[:25], GREY, 1)

    # Full index of 48 stories
    draw_text(cv, 16, 590, "ALL 48 STORIES - BY REGION", NAVY, 2)
    cv.fill(16, 612, W - 32, 2, NAVY)
    legend = "ME MIDDLE EAST  -  EU EUROPE  -  AP ASIA-PACIFIC  -  AM AMERICAS  -  AF AFRICA  -  OC OCEANIA  -  CL CLIMATE"
    draw_text(cv, 16, 620, legend, GREY, 1)
    y0 = 640
    for i, (reg, head) in enumerate(STORIES):
        col = i // 24
        row = i % 24
        x = 16 + col * 508
        yy = y0 + row * 15
        draw_text(cv, x, yy, "%02d %s  %s" % (i + 1, reg, head[:66]), INK, 1)
        if row % 2 == 1:
            cv.fill(x, yy + 10, 492, 1, LIGHT)

    cv.fill(16, 1004, W - 32, 1, GREY)
    foot = "Compiled from reports dated Tuesday 17 November 2026 - The World Today"
    draw_text(cv, (W - text_w(foot, 1)) // 2, 1010, foot, GREY, 1)
    return cv

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    write_png(path, cv.px, W, H)
    print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))

if __name__ == "__main__":
    main()
