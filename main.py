"""The Sunday Ledger: one front page summing up Sunday 22 November 2026.

Pure standard library: the page is painted pixel by pixel into a buffer
and encoded as a PNG by hand (zlib + struct, no Pillow, no network, no
clock, no randomness). Writes entry.png (1024x1024, far under 1 MiB) into
MAKEFUN_OUTPUT_DIR (default /output). Two runs write identical bytes.

Six stories, all events of 22 November 2026 (or first reported that day):
the Gulf war widening to Kuwait and Bahrain, Trump's permanent Iran
accord, cartel bloodshed in Mexico, the strike on Zelensky's hometown,
Hong Kong's Election Committee vote, and the COP31 deadlock.
"""

import math
import os
import struct
import zlib
from pathlib import Path

W = H = 1024
PAPER = (247, 241, 222)
CREAM = (253, 249, 237)
INK = (27, 42, 51)
CRIMSON = (169, 50, 38)
NAVY = (31, 78, 121)
GOLD = (183, 121, 31)
SLATE = (91, 107, 112)
TEAL = (15, 118, 110)
SAND = (222, 205, 164)
SEA = (168, 208, 205)
PALE = (233, 224, 198)


class Page:
    """A 1024x1024 RGB canvas stored as one bytearray per scanline."""

    def __init__(self):
        self.rows = [bytearray(PAPER * W) for _ in range(H)]

    def fill(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        span = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            self.rows[yy][x0 * 3:x1 * 3] = span

    def dot(self, x, y, colour):
        if 0 <= x < W and 0 <= y < H:
            self.rows[y][x * 3:x * 3 + 3] = bytes(colour)

    def bar_h(self, x, y, w, colour):
        self.fill(x, y, w, 1, colour)

    def bar_v(self, x, y, h, colour):
        self.fill(x, y, 1, h, colour)

    def rule(self, x, y, w, colour, thick=1):
        self.fill(x, y, w, thick, colour)

    def segment(self, x0, y0, x1, y1, colour):
        """Bresenham line between two points."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.dot(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def blob(self, cx, cy, r, colour):
        """Filled disc centred on (cx, cy)."""
        for yy in range(cy - r, cy + r + 1):
            off = yy - cy
            if abs(off) > r:
                continue
            half = int((r * r - off * off) ** 0.5)
            self.bar_h(cx - half, yy, 2 * half + 1, colour)

    def loop(self, cx, cy, r, colour):
        """Thin ring outline."""
        steps = max(32, r * 10)
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.dot(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), colour)

    def wedge(self, points, colour):
        """Fill a polygon given as a list of (x, y) corners."""
        if len(points) < 3:
            return
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        n = len(points)
        for y in range(max(0, top), min(H, bottom + 1)):
            hits = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if ay == by:
                    continue
                lo, hi = (ay, by) if ay < by else (by, ay)
                if lo <= y < hi:
                    t = (y - ay) / (by - ay)
                    hits.append(ax + (bx - ax) * t)
            hits.sort()
            for j in range(0, len(hits) - 1, 2):
                x0 = int(math.ceil(hits[j]))
                x1 = int(math.floor(hits[j + 1]))
                if x1 >= x0:
                    self.bar_h(x0, y, x1 - x0 + 1, colour)

    def burst(self, cx, cy, r, colour, rays=12):
        """Starburst: short rays out of a centre point."""
        for i in range(rays):
            a = 2 * math.pi * i / rays
            x1 = int(cx + r * math.cos(a))
            y1 = int(cy + r * math.sin(a))
            self.segment(cx, cy, x1, y1, colour)
        self.blob(cx, cy, max(2, r // 5), colour)

    def png_bytes(self):
        raw = bytearray()
        for row in self.rows:
            raw.append(0)
            raw.extend(row)
        body = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return out

        head = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head)
                + chunk(b"IDAT", body) + chunk(b"IEND", b""))


PAGE = Page()

# --- 5x7 bitmap lettering, one glyph = seven rows of five bits ----------
# Stored as ints (bit 4 = leftmost column) so a row is one number.
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ',': (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ':': (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ';': (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    '-': (0, 0, 0, 0x1F, 0, 0, 0),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '=': (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '+': (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    '*': (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
}

ADV = 6  # advance per character, in font units


def text_w(s, scale):
    return len(s) * ADV * scale - scale if s else 0


def glyph(ch, x, y, scale, colour):
    rows = FONT.get(ch)
    if not rows:
        return
    for r, bits in enumerate(rows):
        for c in range(5):
            if bits >> (4 - c) & 1:
                PAGE.fill(x + c * scale, y + r * scale, scale, scale, colour)


def write(s, x, y, scale, colour, align="left"):
    s = s.upper()
    if align == "center":
        x -= text_w(s, scale) // 2
    elif align == "right":
        x -= text_w(s, scale)
    for ch in s:
        glyph(ch, x, y, scale, colour)
        x += ADV * scale


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    lines = []
    for chunk in s.upper().split("\n"):
        words = chunk.split()
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def para(s, x, y, scale, colour, max_w, leading=None):
    lines = wrap(s, scale, max_w)
    step = leading if leading is not None else 7 * scale + scale + 2
    for i, line in enumerate(lines):
        write(line, x, y + i * step, scale, colour)
    return y + len(lines) * step

# --- layout ---------------------------------------------------------------
MARGIN = 36
LEFT = MARGIN
RIGHT = W - MARGIN
MID = W // 2


def kicker(text, x, y, colour=CRIMSON):
    write(text, x, y, 2, colour)


def headline(text, x, y, scale, max_w):
    lines = wrap(text, scale, max_w)
    step = 7 * scale + scale + 2
    for i, line in enumerate(lines):
        write(line, x, y + i * step, scale, INK)
    return y + len(lines) * step


def masthead():
    write("THE SUNDAY LEDGER", MID, 44, 6, INK, align="center")
    PAGE.rule(LEFT, 98, RIGHT - LEFT, INK, 3)
    PAGE.rule(LEFT, 104, RIGHT - LEFT, INK, 1)
    write("SUNDAY, 22 NOVEMBER 2026", LEFT, 116, 2, INK)
    write("SIX STORIES - ONE PAGE", RIGHT, 116, 2, INK, align="right")
    PAGE.rule(LEFT, 140, RIGHT - LEFT, INK, 3)
    PAGE.rule(LEFT, 146, RIGHT - LEFT, INK, 1)


def gulf_map(x0, y0, x1, y1):
    """Stylised Gulf: sand land, teal sea, two struck bases, missile arcs."""
    PAGE.fill(x0, y0, x1 - x0, y1 - y0, SAND)
    PAGE.fill(x0, y0, x1 - x0, y1 - y0, CREAM)
    sea = [(x0 + 150, y0), (x1, y0), (x1, y1), (x0 + 210, y1),
           (x0 + 170, y0 + 130), (x0 + 150, y0 + 70)]
    PAGE.wedge(sea, SEA)
    PAGE.segment(x0 + 150, y0, x0 + 170, y0 + 130, NAVY)
    PAGE.segment(x0 + 170, y0 + 130, x0 + 210, y1, NAVY)
    # missile arcs from the upper-left (Iran) down to the two bases
    PAGE.segment(x0 + 40, y0 + 18, x0 + 150, y0 + 60, CRIMSON)
    PAGE.segment(x0 + 150, y0 + 60, x0 + 235, y0 + 88, CRIMSON)
    PAGE.segment(x0 + 40, y0 + 18, x0 + 130, y0 + 110, CRIMSON)
    PAGE.segment(x0 + 130, y0 + 110, x0 + 205, y0 + 158, CRIMSON)
    for bx, by in ((x0 + 240, y0 + 92), (x0 + 210, y0 + 162)):
        PAGE.blob(bx, by, 6, CRIMSON)
        PAGE.loop(bx, by, 11, CRIMSON)
        PAGE.loop(bx, by, 16, INK)
    write("KUWAIT", x0 + 260, y0 + 89, 1, INK)
    write("BAHRAIN", x0 + 232, y0 + 159, 1, INK)
    write("GULF", x0 + 268, y0 + 220, 1, NAVY)
    write("IRAN", x0 + 18, y0 + 8, 1, INK)
    PAGE.rule(x0, y0, x1 - x0, GOLD, 2)
    PAGE.rule(x0, y1 - 2, x1 - x0, GOLD, 2)
    PAGE.bar_v(x0, y0, y1 - y0, GOLD)
    PAGE.bar_v(x1 - 2, y0, y1 - y0, GOLD)


def lead_story():
    kicker("THE GULF WAR WIDENS", LEFT + 20, 172)
    end = headline("IRAN STRIKES US BASES IN KUWAIT AND BAHRAIN",
                   LEFT + 20, 200, 3, 560)
    end = para("IRAN FIRED MISSILES AND DRONES AT AMERICAN BASES IN KUWAIT "
               "AND BAHRAIN IN THE EARLY HOURS OF SUNDAY. TEHRAN CLAIMS EIGHT "
               "SITES WERE DESTROYED. US CENTRAL COMMAND SAYS EVERY WEAPON WAS "
               "INTERCEPTED, WITH NO CASUALTIES AND NO DAMAGE TO THE BASES. "
               "TANKERS WERE ALSO HIT NEAR THE STRAIT OF HORMUZ AS THE "
               "NINE-MONTH-OLD WAR SPREAD.",
               LEFT + 20, end + 12, 2, INK, 560)
    write("KUWAIT CITY AND MANAMA - EARLY SUNDAY", LEFT + 20, end + 8, 2, SLATE)
    gulf_map(640, 172, 968, 448)
    write("IRAN'S STRIKES REACHED ACROSS THE GULF", 804, 454, 1, SLATE,
          align="center")


def flags_deal(x0, y0, x1, y1):
    """US and Iranian flags with a gold seal between them."""
    # United States flag: stripes + canton
    for i in range(7):
        PAGE.fill(x0, y0 + i * 7, 140, 7, CRIMSON if i % 2 == 0 else CREAM)
    PAGE.fill(x0, y0, 56, 28, NAVY)
    for r in range(3):
        for c in range(4):
            PAGE.dot(x0 + 6 + c * 12, y0 + 6 + r * 8, CREAM)
    # Iranian flag: green, white, red bands
    ix = x1 - 140
    PAGE.fill(ix, y0, 140, 16, TEAL)
    PAGE.fill(ix, y0 + 16, 140, 17, CREAM)
    PAGE.fill(ix, y0 + 33, 140, 16, CRIMSON)
    PAGE.blob(ix + 70, y0 + 24, 6, CRIMSON)
    # gold seal in the middle
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    PAGE.loop(cx, cy, 16, GOLD)
    PAGE.loop(cx, cy, 12, GOLD)
    PAGE.blob(cx, cy, 4, GOLD)
    PAGE.bar_h(x0 + 140, cy - 1, cx - 16 - (x0 + 140), GOLD)
    PAGE.bar_h(cx + 17, cy - 1, ix - (cx + 17), GOLD)


def mountains(x0, y0, x1, y1):
    """Sierra ridges, a road, and a red alert at the pass."""
    PAGE.wedge([(x0, y1), (x0 + 130, y0 + 8), (x0 + 260, y1)], SLATE)
    PAGE.wedge([(x0 + 200, y1), (x0 + 330, y0 + 22), (x1, y1)], INK)
    PAGE.blob(x0 + 130, y0 + 8, 5, CRIMSON)
    PAGE.loop(x0 + 130, y0 + 8, 10, CRIMSON)
    PAGE.blob(x1 - 30, y0 + 12, 10, GOLD)
    PAGE.segment(x0 + 10, y1 - 6, x0 + 120, y1 - 26, CRIMSON)
    PAGE.segment(x0 + 120, y1 - 26, x0 + 210, y1 - 10, CRIMSON)
    PAGE.segment(x0 + 210, y1 - 10, x1 - 12, y1 - 22, CRIMSON)


def skyline_burst(x, y):
    """Three rooftops with a gold burst above the middle one."""
    PAGE.fill(x, y + 22, 12, 22, INK)
    PAGE.fill(x + 16, y + 10, 12, 34, INK)
    PAGE.fill(x + 32, y + 26, 12, 18, INK)
    PAGE.burst(x + 22, y + 4, 9, GOLD, rays=8)
    PAGE.blob(x + 40, y + 16, 3, SLATE)
    PAGE.blob(x + 46, y + 10, 2, SLATE)


def ballot_box(x, y):
    """A ballot box with a paper going in."""
    PAGE.fill(x + 4, y - 16, 26, 18, CREAM)
    PAGE.segment(x + 10, y - 6, x + 16, y + 2, CRIMSON)
    PAGE.segment(x + 16, y + 2, x + 26, y - 12, CRIMSON)
    PAGE.fill(x, y + 2, 34, 28, NAVY)
    PAGE.fill(x + 6, y + 2, 22, 3, GOLD)


def globe_icon(cx, cy, r):
    PAGE.blob(cx, cy, r, SEA)
    PAGE.loop(cx, cy, r, NAVY)
    PAGE.segment(cx - r, cy, cx + r, cy, NAVY)
    PAGE.segment(cx, cy - r, cx, cy + r, NAVY)
    PAGE.loop(cx, cy, r // 2, NAVY)


def middle_row():
    # Story 2: Trump / Iran accord
    kicker("DIPLOMACY", LEFT, 514)
    headline("TRUMP SEEKS A PERMANENT IRAN NUCLEAR DEAL", LEFT, 540, 3, 440)
    flags_deal(LEFT + 20, 598, 478, 664)
    para("PRESIDENT TRUMP SAID HE WANTS A PERMANENT NUCLEAR ACCORD WITH "
         "IRAN, A DEAL BUILT TO LAST 'REGARDLESS OF WHO OCCUPIES THE "
         "WHITE HOUSE'.",
         LEFT, 672, 2, INK, 440)
    # Story 3: Mexico cartel bloodshed
    rx = MID + 26
    kicker("MEXICO", rx, 514)
    headline("11 KILLED AS CARTEL HITS BACK AFTER KINGPIN FALLS",
             rx, 540, 3, 440)
    mountains(rx + 20, 598, 968, 664)
    para("ELEVEN PEOPLE WERE KILLED IN CARTEL VIOLENCE ACROSS NORTHERN "
         "MEXICO AFTER SOLDIERS CAPTURED KINGPIN FAUSTO ISIDRO MEZA "
         "FLORES IN SINALOA.",
         rx, 672, 2, INK, 440)
    PAGE.bar_v(MID, 500, 252, INK)


def bottom_row():
    # Story 4: Russia hits Kryvyi Rih
    kicker("UKRAINE", LEFT, 796)
    skyline_burst(432, 788)
    headline("RUSSIA HITS ZELENSKY'S HOMETOWN", LEFT, 820, 2, 440)
    para("RUSSIA LAUNCHED A BALLISTIC-MISSILE ATTACK ON KRYVYI RIH, "
         "PRESIDENT ZELENSKY'S HOMETOWN, AS KYIV REAFFIRMED ITS WISH TO "
         "JOIN NATO.",
         LEFT, 844, 2, INK, 440)
    # Story 5: Hong Kong votes
    rx = MID + 26
    kicker("HONG KONG", rx, 796)
    ballot_box(924, 806)
    headline("HONG KONG PICKS ELECTION COMMITTEE", rx, 820, 2, 440)
    para("ABOUT 5,700 VOTERS BEGAN CHOOSING MEMBERS OF HONG KONG'S "
         "POWERFUL ELECTION COMMITTEE, THE BODY THAT PICKS THE CITY'S "
         "LEADER.",
         rx, 844, 2, INK, 440)
    PAGE.bar_v(MID, 784, 136, INK)


def bottom_strip():
    PAGE.rule(LEFT, 932, RIGHT - LEFT, INK, 3)
    globe_icon(56, 956, 12)
    write("CLIMATE: COP31 TALKS DEADLOCKED OVER FOSSIL FUELS",
          84, 942, 2, INK)
    write("AND FINANCE AS THE SUMMIT NEARS ITS END", 84, 962, 2, INK)
    write("THE SUNDAY LEDGER - 22 NOVEMBER 2026 - SIX STORIES FROM ONE DAY",
          MID, 988, 1, SLATE, align="center")


def build():
    masthead()
    lead_story()
    PAGE.rule(LEFT, 484, RIGHT - LEFT, INK, 2)
    middle_row()
    PAGE.rule(LEFT, 768, RIGHT - LEFT, INK, 2)
    bottom_row()
    bottom_strip()
    return PAGE.png_bytes()


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    data = build()
    target = out_dir / "entry.png"
    target.write_bytes(data)
    print(f"wrote {target} {len(data)} bytes")


if __name__ == "__main__":
    main()
