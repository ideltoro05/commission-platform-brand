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
TEAL, TEAL_STRONG, AQUA, AQUA_SOFT = "#006060", "#004b4c", "#4ae6d6", "#d1f8f3"
AMBER, FLARE, FLARE_SOFT, WHITE = "#ffb135", "#c5002b", "#ffe9e9", "#ffffff"

SANS_400, SANS_500, SANS_600 = "Geist-Regular.ttf", "Geist-Medium.ttf", "Geist-SemiBold.ttf"
MONO_400, MONO_500 = "GeistMono-Regular.ttf", "GeistMono-Medium.ttf"

# The mark on a 100 by 140 grid, top to bottom: a slanted bar, a slanted bar with a leg, and a block.
# It stands for "Your"; the name beside it reads "EZ Payroll".
MARK_W, MARK_H = 100, 140
MARK_SHAPES = [
    [(0, 36), (100, 0), (100, 40), (0, 76)],
    [(0, 89), (100, 53), (100, 77), (30, 102.2), (30, 140), (0, 140)],
    [(40, 112), (100, 112), (100, 140), (40, 140)],
]
MARK_CORNER = 7  # how far from each corner, along both edges, the rounding starts
LINE_1, LINE_2 = "EZ", "Payroll"
# variant: (shape colours top to bottom, name colour)
VARIANTS = {
    "light": ((AQUA, TEAL_STRONG, TEAL), INK),
    "dark": ((AQUA, BONE, MUTED), BONE),
    "mono": ((INK, INK, INK), INK),
    "white": ((WHITE, WHITE, WHITE), WHITE),
}
# The logo: the mark, then the name on two lines. The name's first cap line sits just under the mark's
# top and its second baseline on the mark's bottom. Sizes are in em of the name (Geist 600, -0.03em).
MARK_PER_EM, GAP_PER_EM, TOP_PER_EM = 140 / 86, 30 / 86, 3 / 86
TRACKING, CAP, DESCENT = -0.03, 0.71, 0.22
# One-line form, for wide and short spaces: the mark, then "EZ Payroll" centred on it.
LINE_MARK_PER_EM, LINE_GAP_PER_EM = 1.5, 0.42

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

    def mark(self, x, y, height, variant):
        k = height / MARK_H
        for shape, color in zip(MARK_SHAPES, VARIANTS[variant][0]):
            self.polygon([(x + px * k, y + py * k) for px, py in rounded_points(shape, MARK_CORNER)], color)

    def logo(self, x, y, em, variant):
        """The logo: the mark, then EZ over Payroll. y is the top of the mark."""
        h = em * MARK_PER_EM
        tx, ink = x + h * MARK_W / MARK_H + em * GAP_PER_EM, VARIANTS[variant][1]
        self.mark(x, y, h, variant)
        self.text(tx, y + em * (TOP_PER_EM + CAP), LINE_1, SANS_600, em, ink, TRACKING)
        self.text(tx, y + h, LINE_2, SANS_600, em, ink, TRACKING)

    def logo_line(self, x, y, em, variant):
        """One-line logo: the mark, then EZ Payroll. y is the top of the mark."""
        h = em * LINE_MARK_PER_EM
        self.mark(x, y, h, variant)
        self.text(x + h * MARK_W / MARK_H + em * LINE_GAP_PER_EM, y + h / 2 + em * CAP / 2, LINE_1 + " " + LINE_2,
                  SANS_600, em, VARIANTS[variant][1], TRACKING)

    def save(self, name):
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        if self.opaque:
            out = out.convert("RGB")
        out.save(_path(name), optimize=True)
        return name


def corners(points, cut):
    """For each corner: where the rounding starts, the corner itself, and where the rounding ends."""
    out, n = [], len(points)
    for i, v in enumerate(points):
        ends = []
        for other in (points[i - 1], points[(i + 1) % n]):
            dx, dy = other[0] - v[0], other[1] - v[1]
            length = math.hypot(dx, dy)
            d = min(cut, length / 2)
            ends.append((v[0] + dx / length * d, v[1] + dy / length * d))
        out.append((ends[0], v, ends[1]))
    return out


def rounded_points(points, cut, steps=8):
    """The outline with every corner rounded, as a list of points."""
    out = []
    for a, v, b in corners(points, cut):
        for i in range(steps + 1):
            t = i / steps
            out.append(((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * v[0] + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * v[1] + t * t * b[1]))
    return out


def logo_size(em):
    """Width and height of the logo, down to the baseline of Payroll (the y hangs below it)."""
    text = max(width(LINE_1, SANS_600, em, TRACKING), width(LINE_2, SANS_600, em, TRACKING))
    return em * MARK_PER_EM * MARK_W / MARK_H + em * GAP_PER_EM + text, em * MARK_PER_EM


def logo_line_size(em):
    return (em * LINE_MARK_PER_EM * MARK_W / MARK_H + em * LINE_GAP_PER_EM
            + width(LINE_1 + " " + LINE_2, SANS_600, em, TRACKING), em * LINE_MARK_PER_EM)


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


def mark_paths(variant, x=0.0, y=0.0, height=float(MARK_H)):
    k = height / MARK_H
    out = []
    for shape, color in zip(MARK_SHAPES, VARIANTS[variant][0]):
        d = ""
        for i, (a, v, b) in enumerate(corners([(x + px * k, y + py * k) for px, py in shape], MARK_CORNER * k)):
            d += "%s%s %sQ%s %s %s %s" % ("M" if i == 0 else "L", num(a[0]), num(a[1]), num(v[0]), num(v[1]),
                                          num(b[0]), num(b[1]))
        out.append('<path d="%sZ" fill="%s"/>' % (d, color))
    return "".join(out)


def write_svg(name, view_w, view_h, body, label):
    with open(_path(name), "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" role="img" aria-label="%s">'
                 '<title>%s</title>%s</svg>\n' % (num(view_w), num(view_h), label, label, body))
    return name


def logo_svg(name, variant, em=86.0):
    w, h = logo_size(em)
    tx, ink = h * MARK_W / MARK_H + em * GAP_PER_EM, VARIANTS[variant][1]
    d1, _ = text_path(LINE_1, SANS_600, em, tx, em * (TOP_PER_EM + CAP), TRACKING)
    d2, _ = text_path(LINE_2, SANS_600, em, tx, h, TRACKING)
    body = mark_paths(variant, height=h) + '<path d="%s%s" fill="%s"/>' % (d1, d2, ink)
    return write_svg(name, w, h + em * DESCENT, body, NAME)


def logo_line_svg(name, variant, em=86.0):
    w, h = logo_line_size(em)
    d, _ = text_path(LINE_1 + " " + LINE_2, SANS_600, em, h * MARK_W / MARK_H + em * LINE_GAP_PER_EM,
                     h / 2 + em * CAP / 2, TRACKING)
    body = mark_paths(variant, height=h) + '<path d="%s" fill="%s"/>' % (d, VARIANTS[variant][1])
    return write_svg(name, w, h, body, NAME)


def mark_svg(name, variant):
    return write_svg(name, MARK_W, MARK_H, mark_paths(variant), NAME + " icon")


# App icon: the mark on a rounded tile, on a 64 grid.
ICON_MARK_H = 42


def app_icon_svg(name, tile=RAIL, variant="dark"):
    w = ICON_MARK_H * MARK_W / MARK_H
    body = '<rect width="64" height="64" rx="14" fill="%s"/>' % tile + mark_paths(variant, (64 - w) / 2,
                                                                                  (64 - ICON_MARK_H) / 2, ICON_MARK_H)
    return write_svg(name, 64, 64, body, NAME + " app icon")


def app_icon_frame(px, tile=RAIL, variant="dark"):
    f = Frame(px, px)
    k = px / 64
    f.rect(0, 0, px, px, 14 * k, tile)
    f.mark((64 - ICON_MARK_H * MARK_W / MARK_H) / 2 * k, (64 - ICON_MARK_H) / 2 * k, ICON_MARK_H * k, variant)
    return f
