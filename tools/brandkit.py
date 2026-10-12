"""Drawing kit for the Your EZ Payroll brand: colours, kerned text, the logo, PNG frames and SVG output.

Call configure(fonts_dir, out_dir) first. Text is shaped with HarfBuzz so it is kerned; SVG text is
converted to outlines so logo files need no font installed. Sizes are in final pixels; frames are
drawn at SS times that and scaled down so edges come out smooth.
"""
import math
import os

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

SS = 2
NAME = "Your EZ Payroll"

GROUND, SURFACE, RAISED, LINE, LINE_STRONG = "#f2f7f7", "#ffffff", "#e8eff0", "#d8e2e2", "#738485"
INK, TEXT_MUTED = "#04191e", "#4f5e62"
RAIL, BONE, MUTED = "#001a1f", "#f1f6f7", "#96b1b4"
TEAL, AQUA, AQUA_SOFT = "#006060", "#4ae6d6", "#d1f8f3"
AMBER, FLARE, FLARE_SOFT, WHITE = "#ffb135", "#c5002b", "#ffe9e9", "#ffffff"

SANS_400, SANS_500, SANS_600 = "Geist-Regular.ttf", "Geist-Medium.ttf", "Geist-SemiBold.ttf"
MONO_400, MONO_500 = "GeistMono-Regular.ttf", "GeistMono-Medium.ttf"

# The mark on a 48-unit grid: three right-aligned rows that grow, the last one aqua.
ROWS = [(28, 0, 20, 12), (14, 18, 34, 12), (0, 36, 48, 12)]
ROW_RADIUS = 3.5
# variant: (row colours, name colour)
VARIANTS = {
    "light": ((TEAL, TEAL, AQUA), INK),
    "dark": ((BONE, BONE, AQUA), BONE),
    "mono": ((INK, INK, INK), INK),
    "white": ((WHITE, WHITE, WHITE), WHITE),
}
# Horizontal lockup: 40px mark, 14px gap, 30px name at -0.03em. Stacked: a larger mark above the name.
MARK_PER_EM, GAP_PER_EM, TRACKING, CAP, DESCENT = 40 / 30, 14 / 30, -0.03, 0.71, 0.22
STACK_MARK_PER_EM, STACK_GAP_PER_EM = 2.4, 0.8

FONTS = OUT = ""
_fonts = {}


def configure(fonts_dir, out_dir):
    global FONTS, OUT
    FONTS, OUT = fonts_dir.rstrip("/") + "/", out_dir.rstrip("/") + "/"


def _path(name):
    path = OUT + name
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def load(name):
    if name not in _fonts:
        with open(FONTS + name, "rb") as fh:
            face = hb.Face(fh.read())
        _fonts[name] = (hb.Font(face), face.upem, TTFont(FONTS + name))
    return _fonts[name]


def shape(s, name, tracking=0.0):
    """Kerned glyph positions: [(char, glyph name, x in em)], and the total width in em."""
    if not s:
        return [], 0.0
    font, upem, tt = load(name)
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": False, "calt": False})
    x, out = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((s[info.cluster], tt.getGlyphName(info.codepoint), (x + pos.x_offset) / upem))
        x += pos.x_advance + tracking * upem
    return out, (x - tracking * upem) / upem if out else 0.0


def width(s, name, size, tracking=0.0):
    return shape(s, name, tracking)[1] * size


def baseline_in(name, size, line_height):
    """Where the baseline falls inside a line box, measured from its top (as CSS places it)."""
    _, upem, tt = load(name)
    asc, desc = tt["hhea"].ascent / upem, -tt["hhea"].descent / upem
    return (line_height - (asc + desc) * size) / 2 + asc * size


def wrap(s, name, size, max_width, tracking=0.0):
    lines, line = [], ""
    for word in s.split():
        trial = (line + " " + word).strip()
        if line and width(trial, name, size, tracking) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def rgb(hex_):
    hex_ = hex_.lstrip("#")
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4))


class Frame:
    def __init__(self, w, h, bg=None):
        self.w, self.h, self.opaque = round(w), round(h), bool(bg)
        self.img = Image.new("RGBA", (self.w * SS, self.h * SS), rgb(bg) + (255,) if bg else (0, 0, 0, 0))

    def _region(self, box, color, draw):
        """Draw on a small layer covering the box, then composite it in place.
        The layer starts as the shape's own colour at zero alpha, so soft edges never pick up a dark fringe."""
        pad = 4
        x0 = max(0, math.floor(box[0] * SS) - pad)
        y0 = max(0, math.floor(box[1] * SS) - pad)
        x1 = min(self.w * SS, math.ceil(box[2] * SS) + pad)
        y1 = min(self.h * SS, math.ceil(box[3] * SS) + pad)
        if x1 <= x0 or y1 <= y0:
            return
        layer = Image.new("RGBA", (x1 - x0, y1 - y0), rgb(color) + (0,))
        draw(ImageDraw.Draw(layer), lambda x, y: (x * SS - x0, y * SS - y0))
        self.img.alpha_composite(layer, (x0, y0))

    def rect(self, x, y, w, h, r, color, opacity=1.0):
        fill = rgb(color) + (round(255 * opacity),)
        self._region((x, y, x + w, y + h), color,
                     lambda d, p: d.rounded_rectangle([p(x, y), p(x + w, y + h)], radius=r * SS, fill=fill))

    def outline(self, x, y, w, h, r, stroke, color):
        self._region((x, y, x + w, y + h), color,
                     lambda d, p: d.rounded_rectangle([p(x, y), p(x + w, y + h)], radius=r * SS,
                                                      outline=rgb(color) + (255,), width=round(stroke * SS)))

    def ellipse(self, cx, cy, rx, ry, color, opacity=1.0):
        fill = rgb(color) + (round(255 * opacity),)
        self._region((cx - rx, cy - ry, cx + rx, cy + ry), color,
                     lambda d, p: d.ellipse([p(cx - rx, cy - ry), p(cx + rx, cy + ry)], fill=fill))

    def polygon(self, points, color, opacity=1.0):
        fill = rgb(color) + (round(255 * opacity),)
        xs, ys = [q[0] for q in points], [q[1] for q in points]
        self._region((min(xs), min(ys), max(xs), max(ys)), color,
                     lambda d, p: d.polygon([p(*q) for q in points], fill=fill))

    def line(self, points, stroke, color, opacity=1.0, round_caps=True):
        fill = rgb(color) + (round(255 * opacity),)
        xs, ys = [q[0] for q in points], [q[1] for q in points]
        half = stroke / 2

        def draw(d, p):
            d.line([p(*q) for q in points], fill=fill, width=round(stroke * SS), joint="curve")
            if round_caps:
                for q in (points[0], points[-1]):
                    d.ellipse([p(q[0] - half, q[1] - half), p(q[0] + half, q[1] + half)], fill=fill)

        self._region((min(xs) - stroke, min(ys) - stroke, max(xs) + stroke, max(ys) + stroke), color, draw)

    def dashed(self, x0, x1, y, stroke, dash, gap, color):
        x = x0
        while x < x1:
            self.rect(x, y - stroke / 2, min(dash, x1 - x), stroke, 0, color)
            x += dash + gap

    def text(self, x, baseline, s, name, size, color, tracking=0.0, anchor="l"):
        """Draw one line. anchor: l, m or r. Returns the x where the text ends."""
        glyphs, w_em = shape(s, name, tracking)
        total = w_em * size
        if anchor == "m":
            x -= total / 2
        elif anchor == "r":
            x -= total
        f = ImageFont.truetype(FONTS + name, round(size * SS))
        fill = rgb(color) + (255,)

        def draw(d, p):
            for ch, _, x_em in glyphs:
                d.text(p(x + x_em * size, baseline), ch, font=f, fill=fill, anchor="ls")

        self._region((x - size, baseline - size * 1.3, x + total + size, baseline + size * 0.6), color, draw)
        return x + total

    def para(self, x, top, s, name, size, line_height, color, max_width, tracking=0.0, anchor="l"):
        """Draw wrapped text from the top of its first line box. Returns the bottom of the last line box."""
        for i, line in enumerate(wrap(s, name, size, max_width, tracking)):
            self.text(x, top + i * line_height + baseline_in(name, size, line_height), line, name, size, color,
                      tracking, anchor)
        return top + len(wrap(s, name, size, max_width, tracking)) * line_height

    # ---- the logo ----

    def mark(self, x, y, size, variant):
        k = size / 48
        for (rx, ry, rw, rh), color in zip(ROWS, VARIANTS[variant][0]):
            self.rect(x + rx * k, y + ry * k, rw * k, rh * k, ROW_RADIUS * k, color)

    def wordmark(self, x, baseline, em, variant):
        return self.text(x, baseline, NAME, SANS_600, em, VARIANTS[variant][1], TRACKING)

    def lockup(self, x, y, em, variant):
        """Horizontal logo: the mark, then the name. y is the top of the mark."""
        m = em * MARK_PER_EM
        self.mark(x, y, m, variant)
        self.wordmark(x + m + em * GAP_PER_EM, y + m / 2 + em * CAP / 2, em, variant)

    def stacked(self, cx, y, em, variant):
        """Stacked logo: the mark centred above the name. y is the top of the mark."""
        m = em * STACK_MARK_PER_EM
        self.mark(cx - m / 2, y, m, variant)
        self.wordmark(cx - wordmark_width(em) / 2, y + m + em * (STACK_GAP_PER_EM + CAP), em, variant)

    def save(self, name):
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        if self.opaque:
            out = out.convert("RGB")
        out.save(_path(name), optimize=True)
        return name


def wordmark_width(em):
    return width(NAME, SANS_600, em, TRACKING)


def lockup_size(em):
    return em * (MARK_PER_EM + GAP_PER_EM) + wordmark_width(em), em * MARK_PER_EM


def stacked_size(em):
    return max(wordmark_width(em), em * STACK_MARK_PER_EM), em * (STACK_MARK_PER_EM + STACK_GAP_PER_EM + CAP + DESCENT)


# ---- SVG ----

def num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def text_path(s, name, size, x0, baseline, tracking):
    """The outlines of s as one SVG path, and its width."""
    glyphs, w_em = shape(s, name, tracking)
    _, upem, tt = load(name)
    glyph_set = tt.getGlyphSet()
    pen = SVGPathPen(glyph_set, ntos=num)
    k = size / upem
    for _, glyph, x_em in glyphs:
        glyph_set[glyph].draw(TransformPen(pen, (k, 0, 0, -k, x0 + x_em * size, baseline)))
    return pen.getCommands(), w_em * size


def mark_rects(variant, x=0.0, y=0.0, size=48.0):
    k = size / 48
    return "".join('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>'
                   % (num(x + rx * k), num(y + ry * k), num(rw * k), num(rh * k), num(ROW_RADIUS * k), color)
                   for (rx, ry, rw, rh), color in zip(ROWS, VARIANTS[variant][0]))


def write_svg(name, view_w, view_h, body, label):
    with open(_path(name), "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" role="img" aria-label="%s">'
                 '<title>%s</title>%s</svg>\n' % (num(view_w), num(view_h), label, label, body))
    return name


def lockup_svg(name, variant, em=100.0):
    m = em * MARK_PER_EM
    d, text_w = text_path(NAME, SANS_600, em, m + em * GAP_PER_EM, m / 2 + em * CAP / 2, TRACKING)
    body = mark_rects(variant, size=m) + '<path d="%s" fill="%s"/>' % (d, VARIANTS[variant][1])
    return write_svg(name, m + em * GAP_PER_EM + text_w, m, body, NAME)


def stacked_svg(name, variant, em=100.0):
    w, h = stacked_size(em)
    m = em * STACK_MARK_PER_EM
    d, text_w = text_path(NAME, SANS_600, em, (w - wordmark_width(em)) / 2, m + em * (STACK_GAP_PER_EM + CAP), TRACKING)
    body = mark_rects(variant, x=(w - m) / 2, size=m) + '<path d="%s" fill="%s"/>' % (d, VARIANTS[variant][1])
    return write_svg(name, w, h, body, NAME)


def wordmark_svg(name, variant, em=100.0):
    d, text_w = text_path(NAME, SANS_600, em, 0, em * CAP, TRACKING)
    return write_svg(name, text_w, em * (CAP + DESCENT), '<path d="%s" fill="%s"/>' % (d, VARIANTS[variant][1]), NAME)


def mark_svg(name, variant):
    return write_svg(name, 48, 48, mark_rects(variant), NAME + " icon")


def app_icon_svg(name, tile=RAIL, variant="dark"):
    body = '<rect width="64" height="64" rx="14" fill="%s"/>' % tile + mark_rects(variant, 14, 14, 36)
    return write_svg(name, 64, 64, body, NAME + " app icon")


def app_icon_frame(px, tile=RAIL, variant="dark"):
    f = Frame(px, px)
    f.rect(0, 0, px, px, px * 14 / 64, tile)
    f.mark(px * 14 / 64, px * 14 / 64, px * 36 / 64, variant)
    return f
