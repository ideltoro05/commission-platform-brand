"""Build the Your EZ Payroll logo (SVG and PNG) and the brand page images.

Usage: python make_brand.py <fonts_dir> <png_out_dir> <svg_out_dir>
Text is shaped with HarfBuzz so the wordmark is kerned; SVG text is converted to outlines,
so the logo files need no font installed.
"""
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONTS, PNG_OUT, SVG_OUT = (a.rstrip("/") + "/" for a in sys.argv[1:4])
SS = 2  # supersample, then downsample, so rounded corners come out smooth

NAME = "Your EZ Payroll"
RAIL, RAISED, BONE, MUTED = "#001a1f", "#e8eff0", "#f1f6f7", "#96b1b4"
INK, TEAL, AQUA = "#04191e", "#006060", "#4ae6d6"
SANS_600, SANS_400, MONO_500 = "Geist-SemiBold.ttf", "Geist-Regular.ttf", "GeistMono-Medium.ttf"

# The mark on a 48-unit grid: three right-aligned rows that grow, the last one aqua.
ROWS = [(28, 0, 20, 12), (14, 18, 34, 12), (0, 36, 48, 12)]
ROW_RADIUS = 3.5
MARK_COLORS = {"light": (TEAL, TEAL, AQUA), "dark": (BONE, BONE, AQUA), "mono": (INK, INK, INK)}
TEXT_COLORS = {"light": INK, "dark": BONE, "mono": INK}
# Lockup proportions, as shown on the options canvas: 40px mark, 14px gap, 30px name at -0.03em.
MARK_PER_EM, GAP_PER_EM, TRACKING, CAP = 40 / 30, 14 / 30, -0.03, 0.71

_fonts = {}


def load(name):
    if name not in _fonts:
        with open(FONTS + name, "rb") as fh:
            face = hb.Face(fh.read())
        _fonts[name] = (hb.Font(face), face.upem, TTFont(FONTS + name))
    return _fonts[name]


def shape(s, name, tracking=0.0):
    """Kerned glyph positions: [(char, glyph name, x in em)], and the total width in em."""
    font, upem, tt = load(name)
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": False, "calt": False})
    x, out = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((s[info.cluster], tt.getGlyphName(info.codepoint), (x + pos.x_offset) / upem))
        x += pos.x_advance + tracking * upem
    return out, (x - tracking * upem) / upem


def width(s, name, size, tracking=0.0):
    return shape(s, name, tracking)[1] * size


def num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def text_path(s, name, size, x0, baseline, tracking):
    """The outlines of s as one SVG path."""
    glyphs, w = shape(s, name, tracking)
    _, upem, tt = load(name)
    glyph_set = tt.getGlyphSet()
    pen = SVGPathPen(glyph_set, ntos=num)
    k = size / upem
    for _, glyph, x_em in glyphs:
        glyph_set[glyph].draw(TransformPen(pen, (k, 0, 0, -k, x0 + x_em * size, baseline)))
    return pen.getCommands(), w * size


def rgb(hex_):
    hex_ = hex_.lstrip("#")
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4))


class Frame:
    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), rgb(bg) + (255,) if bg else (0, 0, 0, 0))

    def _layer(self, color):
        # Start each layer on its own colour at zero alpha so soft edges do not pick up a dark fringe.
        layer = Image.new("RGBA", self.img.size, rgb(color) + (0,))
        return layer, ImageDraw.Draw(layer)

    def rect(self, x, y, w, h, r, color, opacity=1.0):
        layer, d = self._layer(color)
        d.rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], radius=r * SS,
                            fill=rgb(color) + (round(255 * opacity),))
        self.img = Image.alpha_composite(self.img, layer)

    def text(self, x, baseline, s, name, size, color, tracking=0.0, anchor="l"):
        glyphs, w = shape(s, name, tracking)
        if anchor == "m":
            x -= w * size / 2
        layer, d = self._layer(color)
        f = ImageFont.truetype(FONTS + name, round(size * SS))
        for ch, _, x_em in glyphs:
            d.text(((x + x_em * size) * SS, baseline * SS), ch, font=f, fill=rgb(color) + (255,), anchor="ls")
        self.img = Image.alpha_composite(self.img, layer)

    def dashed(self, x0, x1, y, stroke, dash, gap, color):
        x = x0
        while x < x1:
            self.rect(x, y - stroke / 2, min(dash, x1 - x), stroke, 0, color)
            x += dash + gap

    def mark(self, x, y, size, variant):
        k = size / 48
        for (rx, ry, rw, rh), color in zip(ROWS, MARK_COLORS[variant]):
            self.rect(x + rx * k, y + ry * k, rw * k, rh * k, ROW_RADIUS * k, color)

    def lockup(self, x, y, em, variant):
        """Mark, then the name. y is the top of the mark."""
        m = em * MARK_PER_EM
        self.mark(x, y, m, variant)
        self.text(x + m + em * GAP_PER_EM, y + m / 2 + em * CAP / 2, NAME, SANS_600, em, TEXT_COLORS[variant], TRACKING)

    def save(self, name, opaque=False):
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        if opaque:
            out = out.convert("RGB")
        out.save(PNG_OUT + name, optimize=True)
        print(name, out.size)


def lockup_width(em):
    return em * (MARK_PER_EM + GAP_PER_EM) + width(NAME, SANS_600, em, TRACKING)


# ---- SVG ----

def svg(view_w, view_h, body, label):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" role="img" aria-label="%s">'
            '<title>%s</title>%s</svg>\n') % (num(view_w), num(view_h), label, label, body)


def mark_rects(variant, x=0.0, y=0.0, size=48.0):
    k = size / 48
    return "".join('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>'
                   % (num(x + rx * k), num(y + ry * k), num(rw * k), num(rh * k), num(ROW_RADIUS * k), color)
                   for (rx, ry, rw, rh), color in zip(ROWS, MARK_COLORS[variant]))


def write_svg(filename, content):
    with open(SVG_OUT + filename, "w") as fh:
        fh.write(content)
    print(filename, len(content), "bytes")


def lockup_svg(filename, variant, em=100.0):
    m = em * MARK_PER_EM
    d, text_w = text_path(NAME, SANS_600, em, m + em * GAP_PER_EM, m / 2 + em * CAP / 2, TRACKING)
    body = mark_rects(variant, size=m) + '<path d="%s" fill="%s"/>' % (d, TEXT_COLORS[variant])
    write_svg(filename, svg(m + em * GAP_PER_EM + text_w, m, body, NAME))


def app_icon_svg(filename):
    body = '<rect width="64" height="64" rx="14" fill="%s"/>' % RAIL + mark_rects("dark", 14, 14, 36)
    write_svg(filename, svg(64, 64, body, NAME + " icon"))


# ---- PNG ----

def logo_png(filename, variant, bg=None, em=120):
    m = em * MARK_PER_EM
    pad = m * 0.3
    f = Frame(round(lockup_width(em) + pad * 2), round(m + pad * 2), bg)
    f.lockup(pad, pad, em, variant)
    f.save(filename, opaque=bool(bg))


def app_icon_png(filename, px):
    f = Frame(px, px)
    f.rect(0, 0, px, px, px * 14 / 64, RAIL)
    f.mark(px * 14 / 64, px * 14 / 64, px * 36 / 64, "dark")
    f.save(filename)


def brand_blocks(f, x, scale=1.0):
    """The title card's blocks: a tall aqua slab bled off the top, teal and bone beneath, bled off the right."""
    s = scale
    f.rect(x, -32 * s, 512 * s, 744 * s, 20 * s, AQUA)
    f.rect(x, 744 * s, 240 * s, 240 * s, 20 * s, TEAL)
    f.rect(x + 272 * s, 744 * s, 240 * s, 240 * s, 20 * s, BONE)


def eyebrow(f, x, baseline, s, size=26):
    f.rect(x, baseline - size * 0.7 / 2 - 10, 20, 20, 4, AQUA)
    f.text(x + 44, baseline, s.upper(), MONO_500, size, MUTED, tracking=0.1)


def title_card(filename, with_text):
    f = Frame(1920, 1080, RAIL)
    brand_blocks(f, 1440)
    if with_text:
        eyebrow(f, 96, 124, "Insurance principles / Lesson 01")
        f.text(96, 754, "What insurance is,", SANS_600, 108, BONE, tracking=-0.04)
        f.text(96, 868, "and what it is not", SANS_600, 108, BONE, tracking=-0.04)
        f.text(96, 974, "VIDEO 1 OF 3 · 06:00", MONO_500, 28, MUTED, tracking=0.1)
    f.save(filename, opaque=True)


def key_term(filename):
    f = Frame(1920, 1080, RAIL)
    eyebrow(f, 96, 290, "Key term")
    f.rect(88, 338, width("Indemnity", SANS_600, 120, -0.04) + 64, 156, 8, AQUA)
    f.text(120, 458, "Indemnity", SANS_600, 120, INK, tracking=-0.04)
    for i, line in enumerate(["Putting someone back where they", "were before the loss. No better off,", "and no worse off."]):
        f.text(96, 592 + i * 68, line, SANS_400, 48, BONE)
    # Figure: before the loss, after the loss, after the claim. First and last bars match.
    fx, fy = 1104, 200
    f.text(fx, fy + 44, "SAME POSITION", MONO_500, 24, AQUA, tracking=0.08)
    f.dashed(fx, fx + 720, fy + 80, 4, 8, 12, MUTED)
    f.rect(fx + 24, fy + 80, 176, 480, 12, MUTED)
    f.rect(fx + 272, fy + 352, 176, 208, 12, MUTED, opacity=0.35)
    f.rect(fx + 520, fy + 80, 176, 480, 12, AQUA)
    f.rect(fx, fy + 561, 720, 2, 0, MUTED, opacity=0.5)
    for cx, (a, b) in zip((112, 360, 608), (("BEFORE", "THE LOSS"), ("AFTER", "THE LOSS"), ("AFTER", "THE CLAIM"))):
        f.text(fx + cx, fy + 612, a, MONO_500, 24, MUTED, tracking=0.08, anchor="m")
        f.text(fx + cx, fy + 648, b, MONO_500, 24, MUTED, tracking=0.08, anchor="m")
    f.save(filename, opaque=True)


def social_card(filename):
    f = Frame(1200, 630, RAIL)
    brand_blocks(f, 840, scale=0.62)
    f.lockup(64, 64, 34, "dark")
    f.text(64, 452, "Pay, worked out", SANS_600, 88, BONE, tracking=-0.04)
    f.text(64, 548, "line by line", SANS_600, 88, BONE, tracking=-0.04)
    f.save(filename, opaque=True)


for variant, suffix in (("light", ""), ("dark", "-on-dark"), ("mono", "-mono")):
    lockup_svg("logo%s.svg" % suffix, variant)
    write_svg("mark%s.svg" % suffix, svg(48, 48, mark_rects(variant), NAME + " mark"))
app_icon_svg("app-icon.svg")

logo_png("logo-on-light.png", "light")
logo_png("logo-on-dark.png", "dark")
logo_png("logo-rail.png", "dark", bg=RAIL)
app_icon_png("logo-mark.png", 512)
app_icon_png("apple-touch-icon.png", 180)
app_icon_png("favicon-32.png", 32)
title_card("lesson-title-card.png", with_text=True)
title_card("lesson-title-background.png", with_text=False)
key_term("lesson-key-term.png")
social_card("social-card.png")
Frame(1920, 1080, RAISED).save("lesson-avatar-backdrop.png", opaque=True)
