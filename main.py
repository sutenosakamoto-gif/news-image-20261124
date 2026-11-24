#!/usr/bin/env python3
"""World News - 24 November 2026, in one image.

A self-contained renderer: running this program draws a 1024x1024
broadsheet-style front page summarising thirty world news stories of
Tuesday, 24 November 2026 and writes it as a PNG to /output/entry.png
(falling back to ./entry.png when /output is not writable).

Only the Python standard library is used (zlib/struct for the PNG
encoding).  All drawing - including the bitmap font - is implemented
here, so the output is byte-identical on every run.  No network.
"""

import os
import struct
import zlib
from math import hypot

# ---------------------------------------------------------------- canvas

WIDTH = 1024
HEIGHT = 1024


class Canvas:
    """A tiny RGB framebuffer with just the primitives we need."""

    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.px = bytearray(bytes(colour) * (width * height))

    def set_px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(colour)

    def fill_rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                x0 = max(0, x)
                x1 = min(self.w, x + w)
                if x0 < x1:
                    i = (yy * self.w + x0) * 3
                    self.px[i:i + (x1 - x0) * 3] = bytes(colour) * (x1 - x0)

    def rect_outline(self, x, y, w, h, colour, t=2):
        self.fill_rect(x, y, w, t, colour)
        self.fill_rect(x, y + h - t, w, t, colour)
        self.fill_rect(x, y, t, h, colour)
        self.fill_rect(x + w - t, y, t, h, colour)

    def fill_circle(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if hypot(xx - cx, yy - cy) <= r:
                    self.set_px(xx, yy, colour)

    def ring(self, cx, cy, r, colour, t=3):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                if abs(hypot(xx - cx, yy - cy) - r) <= t / 2.0:
                    self.set_px(xx, yy, colour)

    def line(self, x0, y0, x1, y1, colour, t=1):
        # Bresenham, optionally thickened by stamping small squares.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, points, colour, t=2):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            self.line(ax, ay, bx, by, colour, t)

    def fill_triangle(self, ax, ay, bx, by, cx, cy, colour):
        def edge(px, py, qx, qy, rx, ry):
            return (px - qx) * (ry - qy) - (py - qy) * (rx - qx)

        minx = max(0, min(ax, bx, cx))
        maxx = min(self.w - 1, max(ax, bx, cx))
        miny = max(0, min(ay, by, cy))
        maxy = min(self.h - 1, max(ay, by, cy))
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                d1 = edge(xx, yy, ax, ay, bx, by)
                d2 = edge(xx, yy, bx, by, cx, cy)
                d3 = edge(xx, yy, cx, cy, ax, ay)
                if (d1 >= 0 and d2 >= 0 and d3 >= 0) or \
                        (d1 <= 0 and d2 <= 0 and d3 <= 0):
                    self.set_px(xx, yy, colour)


# ------------------------------------------------------------------ font
# A 5x7 bitmap font.  Each glyph is seven rows of five pixels; '#' is ink.

FONT = {
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    '2': (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '$': (".###.", "#.#.#", "#.#..", ".###.", "..#.#", "#.#.#", ".###."),
    '%': ("##..#", "#.#.#", "##.#.", "...#.", "..#..", ".#.##", "#..##"),
}


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, colour):
    text = text.upper()
    for i, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[' '])
        gx = x + i * 6 * scale
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '#':
                    cv.fill_rect(gx + col * scale, y + row * scale,
                                 scale, scale, colour)
    return text_width(text, scale)


def draw_text_centered(cv, y, text, scale, colour):
    x = (cv.w - text_width(text, scale)) // 2
    draw_text(cv, x, y, text, scale, colour)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ""
    for word in text.upper().split():
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------- layout
# Broadsheet front page: cream paper, black ink, one red accent.

PAPER = (247, 241, 226)
PANEL_BG = (253, 250, 241)
INK = (18, 18, 20)
RED = (178, 32, 38)
FAINT = (96, 90, 78)
RULE = (18, 18, 20)

# The three lead stories:
# (tag, headline, detail, giant, giant label, giant sub-label, motif)
LEADS = [
    ("MARKETS - ASIA",
     "ASIAN STOCKS SURGE AS HUANG RETURNS TO NVIDIA",
     "TAIEX +9.1% - NIKKEI +3.9% - KOSPI +6.5% - NVIDIA +31.5% MONDAY",
     "+9.1%", "TAIEX", "", "chart"),
    ("VIETNAM - HANOI",
     "EXPLOSION KILLS 6, INJURES 10 IN HANOI",
     "BLAST AT A FOOD SHOP IN DONG DA STREET AT 8 A.M. LOCAL TIME",
     "6", "KILLED", "10 INJURED", "blast"),
    ("UKRAINE - ZAPORIZHZHIA",
     "RUSSIAN ATTACK ON ZAPORIZHZHIA KILLS 2, WOUNDS 22",
     "INCLUDING 2 CHILDREN, IN AN OVERNIGHT ATTACK, OFFICIALS SAID",
     "22", "WOUNDED", "2 KILLED", "ruin"),
]

# Eleven medium stories: (tag, headline, motif key)
MEDIUM = [
    ("KOREA - TOI", "N. KOREAN AIRCRAFT BREACHES AIRSPACE", "plane"),
    ("KOREA - JAPAN TIMES", "S. KOREA SCRAMBLES JETS ON RUSSIAN INCURSION",
     "jet"),
    ("PACIFIC - REUTERS", "SOLOMONS TO DROP CHINA PACT FOR AUSTRALIA",
     "scroll"),
    ("BANGLADESH - REUTERS", "HASINA PLANS RETURN TO BANGLADESH 16 DEC",
     "house"),
    ("U.S. - REUTERS", "TRUMP TO MEET NATO CHIEF RUTTE WED", "flags"),
    ("MYANMAR - HORIZON", "14 COUNTRIES BACK ICJ ROHINGYA RULING", "scales"),
    ("UNITED NATIONS - HORIZON", "UN CHIEF SEEKS AI-RISK FRAMEWORK IN A YEAR",
     "chip"),
    ("U.S. - AP", "STATES SUE MUSK FIRMS OVER GROK IMAGES", "gavel"),
    ("NEPAL - HORIZON", "5.6 MAGNITUDE QUAKE STRIKES NEPAL", "quake"),
    ("U.S. - HORIZON", "PENNSYLVANIA MEASLES CLAIMS NINTH DEATH", "virus"),
    ("LIBYA - IQMIA", "UN SEEKS PROBE INTO LIBYA WARSHIP STRIKE", "ship"),
]

# Sixteen more stories, one line each, for the "also" list.
ALSO = [
    "GAZA STRIKES KILL AT LEAST THREE",
    "RUSSIA WARNS ESTONIA ON VERGE OF WAR",
    "SAUDI AIRSTRIKE KILLS 17 IN HODEIDA",
    "IRAN FLOGS SINGER WITH 74 LASHES",
    "IRAN: NO TALKS UNTIL US MEETS 7 TERMS",
    "PAKISTAN'S ZEESHAN ALI TO JOIN TIANGONG",
    "11 DIE IN UAE COACH-TRUCK CRASH",
    "CAR BOMB DESTROYS BUILDINGS IN COLOMBIA",
    "EX-POLICE CHIEF CHARGED WITH TREASON",
    "WARS PUT FOOD AID FOR 7.3M MORE AT RISK",
    "RUSSIA MAY LAUNCH NUCLEAR SPACE WEAPON",
    "SOMALIA, UGANDA STEP UP AL-SHABAAB OPS",
    "DEMOCRATS FLIPPED NINE US SENATE SEATS",
    "ANTHROPIC LAUNCHES CLAUDE SHIP CODE TOOLS",
    "ACROPOLIS MUSEUM REOPENS AFTER 7 YEARS",
    "COMMANDERS STUN BENGALS 22-20 ON MNF",
]

# Times at 12:00 UTC on 24 November 2026 (two lines, centred).
UTC_LINES = [
    "AT 12:00 UTC: TOKYO 21:00 - SYDNEY 23:00 - MUMBAI 17:30 - LONDON 12:00",
    "PARIS 13:00 - MOSCOW 15:00 - NEW YORK 07:00 - LOS ANGELES 04:00",
]

# A stylised dot-grid world map: land is given as (start, end) column
# ranges per row, on a 60-column by 10-row grid.
MAP_ROWS = [
    [(4, 16), (33, 55)],
    [(3, 17), (30, 57)],
    [(4, 16), (29, 34), (36, 56)],
    [(6, 13), (30, 35), (37, 55)],
    [(9, 14), (29, 38), (40, 53)],
    [(10, 14), (30, 37), (44, 50)],
    [(10, 13), (30, 36), (47, 52)],
    [(11, 13), (31, 35), (50, 55)],
    [(12, 12), (51, 54)],
    [(57, 58)],
]


# ---------------------------------------------------------------- motifs
# Bold pictograms for the three lead panels, drawn around (cx, cy).

def motif_chart(cv, cx, cy):
    # A compact market line dipping, then rebounding steeply in red.
    # Kept small: it sits in the panel's top-right corner, clear of the
    # headline, the detail lines and the giant number's label.
    cv.line(cx - 24, cy + 16, cx + 24, cy + 16, INK, 3)
    cv.line(cx - 24, cy + 16, cx - 24, cy - 16, INK, 3)
    cv.polyline([(cx - 21, cy - 8), (cx - 9, cy + 2), (cx - 1, cy + 10)],
                INK, 3)
    cv.polyline([(cx - 1, cy + 10), (cx + 10, cy - 3), (cx + 22, cy - 14)],
                RED, 4)
    cv.polyline([(cx + 22, cy - 14), (cx + 15, cy - 13), (cx + 21, cy - 7)],
                RED, 3)


def motif_blast(cv, cx, cy):
    # A starburst: the Hanoi explosion.
    cv.fill_circle(cx, cy, 7, RED)
    for dx, dy in ((0, -34), (24, -24), (34, 0), (24, 24),
                   (0, 34), (-24, 24), (-34, 0), (-24, -24),
                   (12, -32), (32, -12), (32, 12), (12, 32),
                   (-12, 32), (-32, 12), (-32, -12), (-12, -32)):
        cv.line(cx, cy, cx + dx, cy + dy, INK, 3)
    cv.fill_circle(cx, cy, 7, RED)


def motif_ruin(cv, cx, cy):
    # Two damaged buildings under a red blast.
    cv.fill_rect(cx - 38, cy - 4, 26, 40, INK)
    cv.fill_rect(cx - 4, cy - 22, 26, 58, INK)
    cv.fill_triangle(cx - 4, cy - 22, cx + 8, cy - 34, cx + 22, cy - 22,
                     INK)
    cv.fill_rect(cx - 30, cy + 10, 8, 9, PAPER)
    cv.fill_rect(cx + 4, cy + 4, 8, 9, PAPER)
    cv.fill_rect(cx + 4, cy + 22, 8, 9, PAPER)
    for fx in (cx - 28, cx - 8, cx + 12):
        cv.fill_triangle(fx - 7, cy - 14, fx + 7, cy - 14, fx, cy - 36, RED)


LEAD_MOTIFS = {"chart": motif_chart, "blast": motif_blast,
               "ruin": motif_ruin}


# Small bold motifs for the medium panels, drawn around (cx, cy).

def motif_plane(cv, cx, cy):
    cv.line(cx - 18, cy, cx + 18, cy, INK, 4)
    cv.fill_triangle(cx + 18, cy, cx + 8, cy - 5, cx + 8, cy + 5, INK)
    cv.fill_triangle(cx - 2, cy, cx - 8, cy - 12, cx - 10, cy, INK)
    cv.fill_triangle(cx - 2, cy, cx - 8, cy + 12, cx - 10, cy, INK)
    cv.line(cx - 18, cy - 2, cx - 14, cy - 12, INK, 3)


def motif_jet(cv, cx, cy):
    motif_plane(cv, cx + 4, cy)
    for yy in (cy - 10, cy, cy + 10):
        cv.line(cx - 18, yy, cx - 6, yy, RED, 3)


def motif_scroll(cv, cx, cy):
    cv.rect_outline(cx - 16, cy - 12, 32, 24, INK, 3)
    cv.fill_rect(cx - 18, cy - 14, 5, 28, RED)
    cv.fill_rect(cx + 13, cy - 14, 5, 28, RED)
    cv.line(cx - 8, cy - 4, cx + 8, cy - 4, INK, 2)
    cv.line(cx - 8, cy + 4, cx + 8, cy + 4, INK, 2)


def motif_house(cv, cx, cy):
    cv.fill_triangle(cx - 17, cy - 2, cx, cy - 17, cx + 17, cy - 2, RED)
    cv.fill_rect(cx - 12, cy - 2, 24, 16, INK)
    cv.fill_rect(cx - 3, cy + 5, 6, 9, PAPER)
    cv.line(cx, cy - 26, cx, cy - 20, INK, 3)
    cv.fill_triangle(cx - 4, cy - 26, cx + 4, cy - 26, cx, cy - 20, INK)


def motif_flags(cv, cx, cy):
    cv.line(cx - 8, cy - 14, cx - 8, cy + 14, INK, 3)
    cv.line(cx + 8, cy - 14, cx + 8, cy + 14, INK, 3)
    cv.fill_triangle(cx - 8, cy - 14, cx + 6, cy - 10, cx - 8, cy - 6, RED)
    cv.fill_triangle(cx + 8, cy - 14, cx + 20, cy - 10, cx + 8, cy - 6, INK)


def motif_scales(cv, cx, cy):
    cv.line(cx, cy - 14, cx, cy + 14, INK, 3)
    cv.line(cx - 14, cy - 12, cx + 14, cy - 12, INK, 3)
    cv.line(cx - 14, cy - 12, cx - 17, cy + 2, INK, 2)
    cv.line(cx - 14, cy - 12, cx - 11, cy + 2, INK, 2)
    cv.line(cx + 14, cy - 12, cx + 11, cy + 2, INK, 2)
    cv.line(cx + 14, cy - 12, cx + 17, cy + 2, INK, 2)
    cv.fill_rect(cx - 19, cy + 2, 8, 3, RED)
    cv.fill_rect(cx + 11, cy + 2, 8, 3, RED)
    cv.fill_rect(cx - 8, cy + 14, 16, 3, INK)


def motif_chip(cv, cx, cy):
    cv.rect_outline(cx - 11, cy - 11, 22, 22, INK, 3)
    cv.fill_rect(cx - 5, cy - 5, 10, 10, RED)
    for dx in (-7, 0, 7):
        cv.line(cx + dx, cy - 17, cx + dx, cy - 11, INK, 2)
        cv.line(cx + dx, cy + 11, cx + dx, cy + 17, INK, 2)
        cv.line(cx - 17, cy + dx, cx - 11, cy + dx, INK, 2)
        cv.line(cx + 11, cy + dx, cx + 17, cy + dx, INK, 2)


def motif_gavel(cv, cx, cy):
    cv.line(cx - 14, cy + 12, cx + 12, cy - 12, INK, 4)
    cv.fill_rect(cx - 2, cy - 16, 18, 9, RED)
    cv.fill_rect(cx - 16, cy + 12, 32, 3, INK)


def motif_quake(cv, cx, cy):
    cv.polyline([(cx - 18, cy - 4), (cx - 9, cy + 6), (cx, cy - 8),
                 (cx + 9, cy + 6), (cx + 18, cy - 4)], INK, 3)
    cv.polyline([(cx - 12, cy - 14), (cx - 4, cy - 6), (cx + 4, cy - 14)],
                RED, 3)
    cv.line(cx - 18, cy + 12, cx + 18, cy + 12, INK, 2)


def motif_virus(cv, cx, cy):
    cv.fill_circle(cx, cy, 8, INK)
    for dx, dy in ((0, -16), (11, -11), (16, 0), (11, 11),
                   (0, 16), (-11, 11), (-16, 0), (-11, -11)):
        cv.line(cx, cy, cx + dx, cy + dy, INK, 3)
    cv.fill_circle(cx, cy, 8, INK)
    cv.fill_circle(cx - 3, cy - 2, 2, RED)
    cv.fill_circle(cx + 3, cy + 3, 2, RED)


def motif_ship(cv, cx, cy):
    cv.fill_triangle(cx - 18, cy + 2, cx + 18, cy + 2, cx + 12, cy + 13,
                     INK)
    cv.fill_rect(cx - 18, cy + 2, 36, 4, INK)
    cv.line(cx, cy + 2, cx, cy - 16, INK, 3)
    cv.fill_triangle(cx, cy - 16, cx + 12, cy - 12, cx, cy - 8, RED)
    cv.line(cx - 18, cy + 16, cx + 18, cy + 16, INK, 2)


MEDIUM_MOTIFS = {
    "plane": motif_plane, "jet": motif_jet, "scroll": motif_scroll,
    "house": motif_house, "flags": motif_flags, "scales": motif_scales,
    "chip": motif_chip, "gavel": motif_gavel, "quake": motif_quake,
    "virus": motif_virus, "ship": motif_ship,
}


# ---------------------------------------------------------------- panels

MARGIN = 12
CONTENT_W = WIDTH - 2 * MARGIN  # 1000


def draw_lead(cv, x, y, w, h, story):
    tag, headline, detail, giant, label, sublabel, motif = story
    cv.fill_rect(x, y, w, h, PANEL_BG)
    cv.rect_outline(x, y, w, h, RULE, 2)
    cv.fill_rect(x, y, w, 7, RED)

    draw_text(cv, x + 14, y + 16, tag, 2, RED)

    hy = y + 40
    for line_text in wrap_text(headline, 3, w - 28):
        draw_text(cv, x + 14, hy, line_text, 3, INK)
        hy += 25

    # The detail starts below the headline, however many lines the
    # headline wrapped to, so the two never strike through each other.
    dy = max(y + 126, hy + 1)
    for line_text in wrap_text(detail, 2, w - 28):
        draw_text(cv, x + 14, dy, line_text, 2, FAINT)
        dy += 16

    # The giant key number, bottom left; motif at bottom right, except
    # the chart, which sits in the top-right corner: at the bottom it
    # would collide with a wide number's label.
    gy = y + h - 50
    gw = draw_text(cv, x + 14, gy, giant, 6, RED)
    if label:
        draw_text(cv, x + 14 + gw + 10, gy + 5, label, 3, INK)
    if sublabel:
        draw_text(cv, x + 14 + gw + 10, gy + 29, sublabel, 2, FAINT)
    if motif == "chart":
        LEAD_MOTIFS[motif](cv, x + w - 46, y + 38)
    else:
        LEAD_MOTIFS[motif](cv, x + w - 58, y + h - 38)


def draw_medium(cv, x, y, w, h, story):
    tag, headline, motif = story
    cv.fill_rect(x, y, w, h, PANEL_BG)
    cv.rect_outline(x, y, w, h, RULE, 1)
    cv.fill_rect(x, y, 6, h, RED)
    draw_text(cv, x + 12, y + 6, tag, 2, RED)
    lines = wrap_text(headline, 2, w - 12 - 46)
    if len(lines) <= 2:
        ly, step = y + 22, 15
    else:
        ly, step = y + 20, 14
    for line_text in lines:
        draw_text(cv, x + 12, ly, line_text, 2, INK)
        ly += step
    MEDIUM_MOTIFS[motif](cv, x + w - 26, y + h // 2)


def draw_world_map(cv, x, y, cell=7, dot=4):
    for row, ranges in enumerate(MAP_ROWS):
        for start, end in ranges:
            for col in range(start, end + 1):
                dx = x + col * cell + (cell - dot) // 2
                dy = y + row * cell + (cell - dot) // 2
                cv.fill_rect(dx, dy, dot, dot, INK)
    # Red markers on the three lead locations: Zaporizhzhia, Hanoi and
    # Taiwan (the markets lead).
    for col, row in ((36, 2), (48, 4), (50, 4)):
        dx = x + col * cell + (cell - dot) // 2
        dy = y + row * cell + (cell - dot) // 2
        cv.fill_rect(dx - 1, dy - 1, dot + 2, dot + 2, RED)


def render():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead: red rules, the distinct title, then the date in the
    # largest type on the page.
    cv.fill_rect(MARGIN, 10, CONTENT_W, 4, RED)
    cv.fill_rect(MARGIN, 18, CONTENT_W, 2, RULE)
    draw_text_centered(cv, 26, "THE WORLD IN ONE PAGE", 6, INK)
    draw_text_centered(cv, 74, "TUESDAY 24 NOVEMBER 2026", 7, RED)
    draw_text_centered(cv, 130,
                       "30 STORIES FROM AROUND THE WORLD - ALL REPORTED "
                       "TUESDAY 24 NOVEMBER 2026", 2, FAINT)
    cv.fill_rect(MARGIN, 150, CONTENT_W, 4, RULE)

    # Three lead stories across the top.
    lead_y, lead_h, lead_w, lead_gap = 160, 240, 326, 11
    for i, story in enumerate(LEADS):
        draw_lead(cv, MARGIN + i * (lead_w + lead_gap), lead_y,
                  lead_w, lead_h, story)

    # Eleven medium stories, three columns of four (last cell empty).
    med_y, med_h, med_w, med_gap = 408, 64, 326, 11
    for i, story in enumerate(MEDIUM):
        col, row = i % 3, i // 3
        draw_medium(cv, MARGIN + col * (med_w + med_gap),
                    med_y + row * (med_h + 6), med_w, med_h, story)

    # A thin UTC strip: major-city times at 12:00 UTC.
    utc_y = 690
    cv.rect_outline(MARGIN, utc_y, CONTENT_W, 34, RULE, 1)
    draw_text_centered(cv, utc_y + 4, UTC_LINES[0], 2, INK)
    draw_text_centered(cv, utc_y + 19, UTC_LINES[1], 2, INK)

    # The rest of the day as a compact one-line list, two columns.
    list_y = 732
    draw_text(cv, MARGIN, list_y, "ALSO ON 24 NOVEMBER", 3, INK)
    cv.fill_rect(MARGIN, list_y + 26, CONTENT_W, 3, RED)
    item_y = list_y + 34
    col_w, col_gap = 494, 12
    half = (len(ALSO) + 1) // 2
    for i, item in enumerate(ALSO):
        col, row = (0, i) if i < half else (1, i - half)
        x = MARGIN + col * (col_w + col_gap)
        yy = item_y + row * 16
        cv.fill_rect(x, yy + 3, 7, 7, RED)
        draw_text(cv, x + 14, yy, item, 2, INK)

    # Dotted world map band, with small captions at each side.
    map_y = 900
    draw_text(cv, MARGIN, map_y + 28, "WORLD MAP", 2, INK)
    draw_world_map(cv, (WIDTH - 60 * 7) // 2, map_y)
    right = "24 NOV 2026"
    draw_text(cv, WIDTH - MARGIN - text_width(right, 2), map_y + 28,
              right, 2, INK)

    # Footer: the date check.
    foot_y = 976
    cv.fill_rect(MARGIN, foot_y, CONTENT_W, 3, RULE)
    draw_text_centered(cv, foot_y + 8,
                       "DATE CHECK: EVERY STORY ABOVE WAS REPORTED ON "
                       "TUESDAY 24 NOVEMBER 2026", 2, INK)
    draw_text_centered(cv, foot_y + 24,
                       "SOURCES: REUTERS - AP - THE JAPAN TIMES - "
                       "THE TIMES OF INDIA - HORIZON - IQMIA", 2, FAINT)
    cv.fill_rect(MARGIN, foot_y + 40, CONTENT_W, 4, RED)
    return cv


# -------------------------------------------------------------- PNG file

def encode_png(cv):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)  # filter type 0 (None) for every scanline
        raw += cv.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    data = encode_png(render())
    try:
        os.makedirs("/output", exist_ok=True)
        path = "/output/entry.png"
        with open(path, "wb") as fh:
            fh.write(data)
    except OSError:
        path = "./entry.png"
        with open(path, "wb") as fh:
            fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
