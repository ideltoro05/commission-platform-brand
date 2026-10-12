"""Build the Your EZ Payroll video asset pack: logos, blank backgrounds, example lesson frames and overlays.

Usage: python make_pack.py <fonts_dir> <out_dir>
Frames are 1920 by 1080. The sample text comes from the Insurance Principles Lesson 1 scripts.
"""
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

import brandkit as k
from brandkit import (AMBER, AQUA, AQUA_SOFT, BONE, FLARE, FLARE_SOFT, INK, LINE, LINE_STRONG, MONO_400, MONO_500,
                      MUTED, RAIL, RAISED, SANS_400, SANS_500, SANS_600, SURFACE, TEAL, TEXT_MUTED, Frame,
                      baseline_in, width, wrap)

W, H, SAFE = 1920, 1080, 96
made = []  # (folder, file) in the order built, for the overview sheets


def out(f, name):
    made.append(f.save(name))


def frame(bg):
    return Frame(W, H, bg)


# ---- small parts ----

def label(f, x, baseline, s, color, size=24, anchor="l"):
    return f.text(x, baseline, s.upper(), MONO_500, size, color, 0.1, anchor)


def eyebrow(f, x, baseline, s, color=MUTED, size=26):
    f.rect(x, baseline - size * 0.35 - 10, 20, 20, 4, AQUA)
    label(f, x + 44, baseline, s, color, size)


def blocks_right(f, x=1440, s=1.0):
    """A tall aqua slab bled off the top and side, with a teal and a bone block beneath."""
    f.rect(x, -32 * s, 512 * s, 744 * s, 20 * s, AQUA)
    f.rect(x, 744 * s, 240 * s, 240 * s, 20 * s, TEAL)
    f.rect(x + 272 * s, 744 * s, 240 * s, 240 * s, 20 * s, BONE)


def blocks_left(f):
    f.rect(-32, -32, 512, 744, 20, AQUA)
    f.rect(-32, 744, 240, 240, 20, BONE)
    f.rect(240, 744, 240, 240, 20, TEAL)


def avatar(f, cx):
    """A stand-in for the presenter, so a frame shows where she goes."""
    f.ellipse(cx, 430, 118, 118, LINE)
    f.rect(cx - 250, 590, 500, 600, 190, LINE)
    label(f, cx, 800, "Avatar", TEXT_MUTED, 24, "m")


def card(f, side="right"):
    """White card on two thirds of the frame. Returns the left edge of its content."""
    x = 704 if side == "right" else SAFE
    f.rect(x, SAFE, 1120, 888, 20, SURFACE)
    f.outline(x, SAFE, 1120, 888, 20, 2, LINE)
    return x + 64


def panel(f, side="right"):
    """Rail panel on three fifths of the frame. Returns the left edge of its content."""
    if side == "right":
        f.rect(768, -40, 1200, 1160, 0, RAIL)
        return 864
    f.rect(-40, -40, 1192, 1160, 0, RAIL)
    return SAFE


def check_card(f):
    f.rect(240, SAFE, 1440, 888, 28, SURFACE)
    return 304


def lower_third(f, title, sub, x=SAFE, bottom=H - SAFE, min_w=660):
    w = max(min_w, 84 + max(width(title, SANS_600, 44, -0.025), width(sub.upper(), MONO_400, 24, 0.08)) + 56)
    top = bottom - 164
    f.rect(x, top, w, 164, 12, RAIL)
    f.rect(x + 40, top + 50, 20, 20, 4, AQUA)
    if title:
        f.text(x + 84, top + 32 + baseline_in(SANS_600, 44, 56), title, SANS_600, 44, BONE, -0.025)
    if sub:
        f.text(x + 84, top + 100 + baseline_in(MONO_400, 24, 32), sub.upper(), MONO_400, 24, MUTED, 0.08)


def check(f, cx, cy, s, color):
    f.line([(cx - s * 0.30, cy + s * 0.02), (cx - s * 0.08, cy + s * 0.24), (cx + s * 0.32, cy - s * 0.22)],
           s * 0.14, color)


def cross(f, cx, cy, s, color):
    a = s * 0.24
    f.line([(cx - a, cy - a), (cx + a, cy + a)], s * 0.14, color)
    f.line([(cx + a, cy - a), (cx - a, cy + a)], s * 0.14, color)


def arrow(f, x0, y, x1, color, stroke=6, head=28):
    d = 1 if x1 > x0 else -1
    f.line([(x0, y), (x1 - d * head * 0.7, y)], stroke, color)
    f.polygon([(x1, y), (x1 - d * head, y - head * 0.62), (x1 - d * head, y + head * 0.62)], color)


def house(f, x, y, s, color, opacity=1.0):
    f.polygon([(x + s / 2, y), (x + s * 1.1, y + s * 0.45), (x + s, y + s * 0.45), (x + s, y + s), (x, y + s),
               (x, y + s * 0.45), (x - s * 0.1, y + s * 0.45)], color, opacity)


def caption(f, lines, size=56, line_height=68, color=BONE, name=SANS_600, bottom=H - SAFE, x=SAFE):
    """Lines of text that end on the bottom safe margin."""
    top = bottom - len(lines) * line_height
    for i, line in enumerate(lines):
        f.text(x, top + i * line_height + baseline_in(name, size, line_height), line, name, size, color, -0.02)


def title_frame(name, eyebrow_text, title, meta, logo=False, size=108):
    f = frame(RAIL)
    blocks_right(f)
    if logo:
        f.lockup(SAFE, 84, 36, "dark")
    else:
        eyebrow(f, SAFE, 124, eyebrow_text)
    lines = wrap(title, SANS_600, size, 1240, -0.04)
    for i, line in enumerate(lines):
        f.text(SAFE, 868 - (len(lines) - 1 - i) * size * 114 / 108, line, SANS_600, size, BONE, -0.04)
    label(f, SAFE, 974, meta, MUTED, 28)
    out(f, name)


# ---- logos ----

def logos():
    kinds = (("dark-text", "light"), ("white-text", "dark"), ("all-dark", "mono"), ("all-white", "white"))
    for suffix, variant in kinds:
        em = 240
        w, h = k.lockup_size(em)
        pad = h * 0.3
        f = Frame(w + pad * 2, h + pad * 2)
        f.lockup(pad, pad, em, variant)
        out(f, "logos/png/logo-horizontal-%s.png" % suffix)
        k.lockup_svg("logos/svg/logo-horizontal-%s.svg" % suffix, variant)

        em = 200
        w, h = k.stacked_size(em)
        pad = em * 0.6
        f = Frame(w + pad * 2, h + pad * 2)
        f.stacked((w + pad * 2) / 2, pad, em, variant)
        out(f, "logos/png/logo-stacked-%s.png" % suffix)
        k.stacked_svg("logos/svg/logo-stacked-%s.svg" % suffix, variant)

        f = Frame(1024, 1024)
        f.mark(112, 112, 800, variant)
        out(f, "logos/png/icon-%s.png" % {"light": "color-for-light", "dark": "color-for-dark",
                                          "mono": "all-dark", "white": "all-white"}[variant])
        k.mark_svg("logos/svg/icon-%s.svg" % {"light": "color-for-light", "dark": "color-for-dark",
                                              "mono": "all-dark", "white": "all-white"}[variant], variant)

    for suffix, variant in (("dark", "mono"), ("white", "white")):
        em = 240
        pad = em * 0.4
        f = Frame(k.wordmark_width(em) + pad * 2, em * (k.CAP + k.DESCENT) + pad * 2)
        f.wordmark(pad, pad + em * k.CAP, em, variant)
        out(f, "logos/png/wordmark-%s.png" % suffix)
        k.wordmark_svg("logos/svg/wordmark-%s.svg" % suffix, variant)

    # With a background, for anywhere a transparent file will not read.
    for suffix, variant, bg in (("on-rail", "dark", RAIL), ("on-white", "light", SURFACE)):
        em = 240
        w, h = k.lockup_size(em)
        pad = h * 0.6
        f = Frame(w + pad * 2, h + pad * 2, bg)
        f.lockup(pad, pad, em, variant)
        out(f, "logos/png/logo-horizontal-%s.png" % suffix)

    out(k.app_icon_frame(1024), "logos/png/app-icon-dark.png")
    out(k.app_icon_frame(1024, RAISED, "light"), "logos/png/app-icon-light.png")
    k.app_icon_svg("logos/svg/app-icon-dark.svg")
    k.app_icon_svg("logos/svg/app-icon-light.svg", RAISED, "light")


# ---- blank backgrounds ----

def backgrounds():
    out(frame(RAIL), "backgrounds/bg-01-rail-plain.png")
    out(frame(RAISED), "backgrounds/bg-02-light-plain.png")

    f = frame(RAIL)
    blocks_right(f)
    out(f, "backgrounds/bg-03-title-blocks-right.png")

    f = frame(RAIL)
    blocks_left(f)
    out(f, "backgrounds/bg-04-title-blocks-left.png")

    for i, side in ((5, "right"), (6, "left")):
        f = frame(RAISED)
        card(f, side)
        out(f, "backgrounds/bg-%02d-avatar-with-white-card-%s.png" % (i, side))
    for i, side in ((7, "right"), (8, "left")):
        f = frame(RAISED)
        panel(f, side)
        out(f, "backgrounds/bg-%02d-avatar-with-dark-panel-%s.png" % (i, side))

    f = frame(RAIL)
    check_card(f)
    out(f, "backgrounds/bg-09-knowledge-check-card.png")

    f = frame(RAIL)
    f.rect(-32, -32, 640, 1144, 20, AQUA)
    out(f, "backgrounds/bg-10-section-divider.png")

    f = frame(RAISED)
    f.rect(SAFE, SAFE, W - SAFE * 2, 888, 20, SURFACE)
    f.outline(SAFE, SAFE, W - SAFE * 2, 888, 20, 2, LINE)
    out(f, "backgrounds/bg-11-full-white-card.png")

    f = frame(RAIL)
    f.rect(SAFE, SAFE, W - SAFE * 2, 888, 20, MUTED, 0.12)
    out(f, "backgrounds/bg-12-dark-with-panel.png")


# ---- example frames ----

def key_term_frame(name):
    f = frame(RAIL)
    eyebrow(f, SAFE, 290, "Key term")
    f.rect(88, 338, width("Indemnify", SANS_600, 120, -0.04) + 64, 156, 8, AQUA)
    f.text(120, 458, "Indemnify", SANS_600, 120, INK, -0.04)
    for i, line in enumerate(("To make someone whole again.", "No better off, and no worse off.")):
        f.text(SAFE, 548 + i * 68 + baseline_in(SANS_400, 48, 68), line, SANS_400, 48, BONE)
    fx, fy = 1104, 200
    f.text(fx, fy + 44, "SAME POSITION", MONO_500, 24, AQUA, 0.08)
    f.dashed(fx, fx + 720, fy + 80, 4, 8, 12, MUTED)
    f.rect(fx + 24, fy + 80, 176, 480, 12, MUTED)
    f.rect(fx + 272, fy + 352, 176, 208, 12, MUTED, 0.35)
    f.rect(fx + 520, fy + 80, 176, 480, 12, AQUA)
    f.rect(fx, fy + 561, 720, 2, 0, MUTED, 0.5)
    for cx, (a, b) in zip((112, 360, 608), (("Before", "the loss"), ("After", "the loss"), ("After", "the claim"))):
        label(f, fx + cx, fy + 612, a, MUTED, 24, "m")
        label(f, fx + cx, fy + 648, b, MUTED, 24, "m")
    out(f, name)


def question_frame(name, reveal):
    f = frame(RAIL)
    x = check_card(f)
    label(f, x, 176, "Question 1 of 3", TEXT_MUTED)
    bottom = f.para(x, 200, "Why can an insurer pay a $60,000 claim on a policy that costs $1,400 a year?",
                    SANS_600, 50, 62, INK, 1312, -0.02)
    options = (("A", "It raises that customer's premium until the money is recovered.", "wrong"),
               ("B", "Premiums from many policyholders are pooled to pay the losses of the few.", "right"),
               ("C", "The state reimburses insurers for large claims.", None))
    y = bottom + 32
    for letter, text, state in options:
        lines = wrap(text, SANS_400, 36, 936)
        h = max(112, len(lines) * 48 + 56)
        fill, edge, stroke = SURFACE, LINE_STRONG, 2
        if reveal and state == "right":
            fill, edge, stroke = AQUA_SOFT, TEAL, 4
        elif reveal and state == "wrong":
            fill, edge, stroke = FLARE_SOFT, FLARE, 4
        f.rect(x, y, 1312, h, 12, fill)
        f.outline(x, y, 1312, h, 12, stroke, edge)
        f.rect(x + 24, y + h / 2 - 32, 64, 64, 8, SURFACE if reveal and state else RAISED)
        f.text(x + 56, y + h / 2 + 10, letter, MONO_500, 28, TEXT_MUTED, anchor="m")
        top = y + (h - len(lines) * 48) / 2
        for i, line in enumerate(lines):
            f.text(x + 112, top + i * 48 + baseline_in(SANS_400, 36, 48), line, SANS_400, 36, INK)
        if reveal and state == "right":
            label(f, x + 1312 - 32, y + h / 2 + 9, "Correct", TEAL, 24, "r")
            check(f, x + 1312 - 32 - width("CORRECT", MONO_500, 24, 0.1) - 36, y + h / 2, 40, TEAL)
        elif reveal and state == "wrong":
            label(f, x + 1312 - 32, y + h / 2 + 9, "Not quite", FLARE, 24, "r")
            cross(f, x + 1312 - 32 - width("NOT QUITE", MONO_500, 24, 0.1) - 36, y + h / 2, 40, FLARE)
        y += h + 16
    if reveal:
        f.para(x, y + 16, "Most policyholders have no loss in a given year, and their premiums pay for the few who do.",
               SANS_400, 36, 50, TEXT_MUTED, 1312)
    out(f, name)


def frames():
    title_frame("frames/01-course-intro.png", "", "Insurance principles", "Course 01 · Commercial lines training",
                logo=True, size=132)
    title_frame("frames/02-lesson-title.png", "Insurance principles / Lesson 01", "What insurance is",
                "Part 1 of 3 · 06:18")

    f = frame(RAISED)
    avatar(f, 1100)
    lower_third(f, "Sarah Mitchell", "Senior Commercial Lines Agent")
    out(f, "frames/03-avatar-with-name.png")

    f = frame(RAISED)
    x = panel(f)
    avatar(f, 384)
    label(f, x, 300, "Premium, per year", MUTED, 26)
    f.text(x, 450, "$1,400", MONO_500, 148, BONE, -0.02)
    label(f, x, 620, "Repair estimate", MUTED, 26)
    f.rect(x - 28, 664, width("$60,000", MONO_500, 148, -0.02) + 56, 180, 8, AQUA)
    f.text(x, 800, "$60,000", MONO_500, 148, INK, -0.02)
    out(f, "frames/04-avatar-with-figures.png")

    # Motion graphic: the pool
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "The pool")
    losses = {(4, 1), (13, 3), (8, 4)}
    for r in range(6):
        for c in range(20):
            hit = (c, r) in losses
            house(f, SAFE + 4 + c * 48, 236 + r * 60, 30, AMBER if hit else MUTED, 1.0 if hit else 0.45)
    f.rect(1320, 236, 504, 330, 20, AQUA)
    label(f, 1368, 304, "One pool", INK)
    f.text(1368, 510, "Shared fund", SANS_600, 64, INK, -0.03)
    label(f, 1180, 322, "Premiums", BONE, 24, "m")
    arrow(f, 1090, 352, 1276, BONE)
    arrow(f, 1276, 462, 1090, MUTED)
    label(f, 1180, 512, "Claims", MUTED, 24, "m")
    caption(f, ["The losses of a few are paid", "from the premiums of many."])
    out(f, "frames/05-motion-diagram-pool.png")

    # Motion graphic: a line chart
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "Law of large numbers")
    left, right, top, bottom = 260, W - SAFE, 250, 730
    mid = (top + bottom) / 2
    label(f, left, top - 34, "Share of heads", MUTED)
    label(f, left - 32, top + 9, "100%", MUTED, 24, "r")
    label(f, left - 32, mid + 9, "50%", AQUA, 24, "r")
    label(f, left - 32, bottom + 9, "0%", MUTED, 24, "r")
    f.rect(left, top, right - left, 2, 0, MUTED, 0.25)
    f.rect(left, bottom, right - left, 2, 0, MUTED, 0.5)
    f.dashed(left, right, mid, 4, 10, 12, AQUA)
    points, seed = [], 7
    for i in range(72):
        seed = (seed * 1103515245 + 12345) % 2 ** 31
        noise = 1.0 if i < 2 else seed / 2 ** 31 * 2 - 1
        points.append((left + (right - left) * i / 71, mid - noise * (bottom - top) / 2 * math.exp(-i / 11)))
    f.line(points, 6, BONE)
    label(f, left, bottom + 58, "3 flips", MUTED)
    label(f, right, bottom + 58, "1,000,000 flips", MUTED, 24, "r")
    caption(f, ["Small groups are unpredictable.", "Large groups are not."])
    out(f, "frames/06-motion-chart-line.png")

    # Avatar + graphic: a numbered list
    f = frame(RAISED)
    x = card(f)
    avatar(f, 352)
    label(f, x, 190, "Insurance has three parts", TEXT_MUTED)
    for i, line in enumerate(("Risk moves to the insurer.", "A fund pays the losses.", "Many similar units.")):
        y = 250 + i * 224
        if i:
            f.rect(x, y - 2, 992, 2, 0, LINE)
        f.rect(x, y + 68, 88, 88, 8, AQUA_SOFT)
        f.text(x + 44, y + 124, "%02d" % (i + 1), MONO_500, 32, TEAL, anchor="m")
        f.text(x + 128, y + 130, line, SANS_500, 52, INK, -0.02)
    out(f, "frames/07-avatar-with-list.png")

    # Motion graphic: a two-way flow
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "The deal")
    for bx, small, big in ((SAFE, "The customer", "Insured"), (1184, "The company", "Insurer")):
        f.outline(bx, 300, 640, 320, 20, 4, MUTED)
        label(f, bx + 320, 420, small, MUTED, 24, "m")
        f.text(bx + 320, 520, big, SANS_600, 88, BONE, -0.04, "m")
    label(f, 960, 392, "Premium", BONE, 26, "m")
    arrow(f, 780, 424, 1140, BONE)
    arrow(f, 1140, 504, 780, AQUA)
    label(f, 960, 556, "Promise", AQUA, 26, "m")
    caption(f, ["The insured pays a premium. The insurer", "promises to pay for covered losses."], 52, 66,
            name=SANS_400)
    out(f, "frames/08-motion-diagram-flow.png")

    key_term_frame("frames/09-key-term.png")

    # Avatar + graphic: a table of figures
    f = frame(RAISED)
    x = card(f)
    avatar(f, 352)
    label(f, x, 190, "The pickup truck", TEXT_MUTED)
    rows = (("Worth", "$8,000.00"), ("Repair estimate", "$11,000.00"), ("Insurer pays", "$8,000.00"))
    for i, (what, figure) in enumerate(rows):
        y = 262 + i * 200
        last = i == len(rows) - 1
        if last:
            f.rect(x - 32, y + 20, 1056, 160, 12, AQUA)
        elif i:
            f.rect(x, y, 992, 2, 0, LINE)
        f.text(x, y + 118, what, SANS_600 if last else SANS_400, 52, INK, -0.02)
        f.text(x + 992, y + 118, figure, MONO_500, 56, INK, -0.02, "r")
    out(f, "frames/10-avatar-with-table.png")

    # Motion graphic: one statement
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "Remember")
    f.text(SAFE, 500, "You buy insurance", SANS_600, 120, BONE, -0.04)
    at = width("at", SANS_600, 120, -0.04)
    f.rect(SAFE, 548, at + 56, 148, 8, AQUA)
    f.text(SAFE + 28, 650, "at", SANS_600, 120, INK, -0.04)
    f.text(SAFE + at + 56 + 30, 650, "Lloyd's,", SANS_600, 120, BONE, -0.04)
    f.text(SAFE, 800, "not from Lloyd's.", SANS_600, 120, BONE, -0.04)
    out(f, "frames/11-motion-statement.png")

    # Avatar + graphic: a recap on the dark panel
    f = frame(RAISED)
    x = panel(f)
    avatar(f, 384)
    label(f, x, 220, "Three things to remember", MUTED, 26)
    y = 270
    for i, line in enumerate(("Many pay a little so a few can be paid a lot.", "Large numbers make losses predictable.",
                              "Indemnify = make whole.")):
        f.rect(x, y, 960, 2, 0, MUTED, 0.3)
        f.text(x, y + 46 + baseline_in(MONO_500, 28, 62), "%02d" % (i + 1), MONO_500, 28, MUTED)
        y = f.para(x + 96, y + 46, line, SANS_500, 50, 62, BONE, 780, -0.02) + 46
    out(f, "frames/12-avatar-with-recap.png")

    # Motion graphic: two columns
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "Not the same thing")
    for bx, head, items, rule in ((SAFE, "Gambling", ("Lose", "Break even", "Win"), MUTED),
                                  (1008, "Insurance", ("Loss", "No loss"), AQUA)):
        f.text(bx, 300, head, SANS_600, 80, BONE, -0.04)
        f.rect(bx, 336, 816, 4, 0, rule, 1.0 if rule == AQUA else 0.5)
        for i, item in enumerate(items):
            f.rect(bx, 376 + i * 136, 816, 116, 12, MUTED, 0.14)
            f.text(bx + 40, 376 + i * 136 + baseline_in(SANS_500, 48, 116), item, SANS_500, 48, BONE, -0.02)
    caption(f, ["With an insured risk, nobody comes out ahead."], 52, 66, name=SANS_400)
    out(f, "frames/13-motion-comparison.png")

    # Motion graphic: three labelled tiles
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "How a loss happens")
    tiles = (("Peril", "Fire", "The cause"), ("Hazard", "The greasy hood", "Raises the odds"),
             ("Loss", "$40,000 of damage", "The cost"))
    for i, (tag, what, why) in enumerate(tiles):
        bx = SAFE + i * 592
        f.rect(bx, 250, 544, 470, 20, MUTED, 0.14)
        label(f, bx + 48, 330, tag, MUTED, 28)
        f.para(bx + 48, 380, what, SANS_600, 68, 78, BONE, 448, -0.03)
        f.text(bx + 48, 660, why, SANS_400, 40, MUTED)
    caption(f, ["A peril causes the loss. A hazard makes it more likely."], 52, 66, name=SANS_400)
    out(f, "frames/14-motion-three-tiles.png")

    # Avatar + graphic: one phrase on the card
    f = frame(RAISED)
    x = card(f)
    avatar(f, 352)
    label(f, x, 190, "Say it precisely", TEXT_MUTED)
    bottom = f.para(x, 380, "Policies cover perils. Underwriters look for hazards.", SANS_600, 84, 96, INK, 992, -0.035)
    f.para(x, bottom + 48, "Use the wrong word and the underwriter hears a different question.", SANS_400, 40, 56,
           TEXT_MUTED, 900)
    out(f, "frames/15-avatar-with-statement.png")

    # Avatar + graphic: four tiles
    f = frame(RAISED)
    x = card(f)
    avatar(f, 352)
    label(f, x, 190, "Besides insurance", TEXT_MUTED)
    f.para(x, 214, "Four other ways to handle a risk", SANS_600, 56, 68, INK, 992, -0.03)
    for i, word in enumerate(("Retain", "Avoid", "Control", "Transfer")):
        bx, by = x + (i % 2) * 508, 330 + (i // 2) * 300
        f.rect(bx, by, 484, 276, 16, RAISED)
        label(f, bx + 40, by + 72, "%02d" % (i + 1), TEXT_MUTED, 26)
        f.text(bx + 40, by + 220, word, SANS_600, 72, INK, -0.035)
    out(f, "frames/16-avatar-with-four-tiles.png")

    # Avatar + graphic: a lettered list
    f = frame(RAISED)
    x = card(f)
    avatar(f, 352)
    words = ("not Catastrophic", "Accidental", "Large number", "Monetary", "Economically feasible", "Definite")
    for i, word in enumerate(words):
        y = 136 + i * 136
        f.rect(x, y, 104, 104, 8, AQUA_SOFT)
        f.text(x + 52, y + 74, "CALMED"[i], MONO_500, 60, TEAL, anchor="m")
        f.text(x + 148, y + 70, word, SANS_500, 52, INK, -0.02)
    out(f, "frames/17-avatar-with-letters.png")

    # Motion graphic: a term and its definition, with room for a picture
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "Ways to handle a risk / 01")
    f.text(SAFE, 540, "Retention", SANS_600, 148, BONE, -0.045)
    f.text(SAFE, 660, "Keep the risk yourself.", SANS_400, 64, BONE, -0.02)
    f.text(SAFE, 760, "A deductible is a small retention.", SANS_400, 44, MUTED)
    f.rect(1184, 250, 640, 580, 20, MUTED, 0.14)
    label(f, 1504, 550, "Picture", MUTED, 24, "m")
    out(f, "frames/18-motion-term-with-picture.png")

    # Motion graphic: a bar chart
    f = frame(RAIL)
    eyebrow(f, SAFE, 124, "The pickup truck")
    base, per_dollar = 720, 440 / 11000
    bars = ((280, 8000, "Worth", "$8,000", MUTED, 1.0), (800, 11000, "Repair estimate", "$11,000", MUTED, 0.35),
            (1320, 8000, "Insurer pays", "$8,000", AQUA, 1.0))
    f.dashed(SAFE, W - SAFE, base - 8000 * per_dollar, 4, 10, 12, MUTED)
    for bx, value, what, figure, color, opacity in bars:
        h = value * per_dollar
        f.rect(bx, base - h, 320, h, 12, color, opacity)
        f.text(bx + 160, base - h - 28, figure, MONO_500, 48, AQUA if color == AQUA else BONE, -0.02, "m")
        label(f, bx + 160, base + 52, what, MUTED, 24, "m")
    f.rect(SAFE, base, W - SAFE * 2, 2, 0, MUTED, 0.5)
    caption(f, ["Indemnity pays what was lost,", "not what the repair would cost."])
    out(f, "frames/19-motion-chart-bars.png")

    title_frame("frames/20-knowledge-check-intro.png", "Lesson 01 / Part 1", "Knowledge check", "3 questions")
    question_frame("frames/21-knowledge-check-question.png", reveal=False)
    question_frame("frames/22-knowledge-check-answer.png", reveal=True)

    # Book page
    f = frame(RAISED)
    eyebrow(f, SAFE, 124, "Course book / Page 2", TEXT_MUTED)
    f.text(SAFE, 868, "Key terms", SANS_600, 108, INK, -0.04)
    label(f, SAFE, 974, "Risk · Peril · Hazard · Loss", TEXT_MUTED, 28)
    px, py, pw, ph = 1051, 40, 773, 1000
    f.rect(px, py, pw, ph, 0, SURFACE)
    f.outline(px, py, pw, ph, 0, 2, LINE)
    f.rect(px + 72, py + 84, 300, 26, 0, LINE_STRONG, 0.6)
    line_y, widths = py + 160, (629, 600, 629, 560, 0, 629, 610, 629, 420, 0, 629, 590, 629, 629, 500, 0, 629, 600, 380)
    for i, lw in enumerate(widths):
        if lw:
            f.rect(px + 72, line_y + i * 40, lw, 14, 0, LINE)
    f.outline(px + 48, line_y + 5 * 40 - 20, pw - 96, 4 * 40 + 14, 0, 8, TEAL)
    out(f, "frames/23-book-page.png")

    # Section divider
    f = frame(RAIL)
    f.rect(-32, -32, 640, 1144, 20, AQUA)
    f.text(SAFE - 12, 984, "02", MONO_500, 360, INK, -0.04)
    eyebrow(f, 704, 124, "Part 2 of 3")
    for i, line in enumerate(wrap("Risk and its vocabulary", SANS_600, 108, 1100, -0.04)):
        f.text(704, 754 + i * 114, line, SANS_600, 108, BONE, -0.04)
    label(f, 704, 974, "05:54", MUTED, 28)
    out(f, "frames/24-section-divider.png")

    title_frame("frames/25-next-up.png", "Next / Part 2", "Risk and its vocabulary", "Up next · 05:54")
    title_frame("frames/26-lesson-complete.png", "Insurance principles / Lesson 01", "Lesson complete",
                "Next · Lesson 02 · Lines of insurance")

    for name, bg, variant in (("frames/27-closing-logo-dark.png", RAIL, "dark"),
                              ("frames/28-closing-logo-light.png", RAISED, "light")):
        f = frame(bg)
        w, h = k.lockup_size(132)
        f.lockup((W - w) / 2, (H - h) / 2, 132, variant)
        out(f, name)


# ---- overlays (transparent) ----

def overlays():
    for name, title, sub in (("lower-third-blank", "", ""),
                             ("lower-third-name", "Sarah Mitchell", "Senior Commercial Lines Agent"),
                             ("lower-third-knowledge-check", "Knowledge check", "3 questions"),
                             ("lower-third-up-next", "Risk and its vocabulary", "Up next · Part 2"),
                             ("lower-third-lesson-complete", "Lesson 01 complete", "Insurance principles")):
        f = Frame(W, H)
        lower_third(f, title, sub, min_w=760 if not title else 660)
        out(f, "overlays/%s.png" % name)

    f = Frame(W, H)
    blocks_right(f)
    out(f, "overlays/brand-blocks-right.png")
    f = Frame(W, H)
    blocks_left(f)
    out(f, "overlays/brand-blocks-left.png")

    f = Frame(1120, 888)
    f.rect(0, 0, 1120, 888, 20, SURFACE)
    f.outline(0, 0, 1120, 888, 20, 2, LINE)
    out(f, "overlays/card-white.png")

    f = Frame(900, 180)
    f.rect(0, 0, 900, 180, 8, AQUA)
    out(f, "overlays/highlight-aqua-block.png")
    f = Frame(1200, 320)
    f.outline(0, 0, 1200, 320, 0, 8, TEAL)
    out(f, "overlays/highlight-teal-outline.png")

    f = Frame(W, 140)
    f.rect(0, 0, W, 140, 0, RAIL, 0.9)
    out(f, "overlays/caption-strip.png")

    for n in range(1, 7):
        f = Frame(200, 200)
        f.rect(0, 0, 200, 200, 24, AQUA)
        f.text(100, 132, "%02d" % n, MONO_500, 88, INK, -0.02, "m")
        out(f, "overlays/number-%02d.png" % n)

    for name, color in (("arrow-right-light", BONE), ("arrow-right-aqua", AQUA), ("arrow-right-dark", INK)):
        f = Frame(480, 120)
        arrow(f, 24, 60, 456, color, 12, 56)
        out(f, "overlays/%s.png" % name)

    for name, text, color, soft, draw in (("label-correct", "Correct", TEAL, AQUA_SOFT, check),
                                          ("label-not-quite", "Not quite", FLARE, FLARE_SOFT, cross)):
        w = 56 + 64 + width(text.upper(), MONO_500, 44, 0.1) + 56
        f = Frame(w, 128)
        f.rect(0, 0, w, 128, 12, soft)
        draw(f, 80, 64, 72, color)
        label(f, 136, 80, text, color, 44)
        out(f, "overlays/%s.png" % name)

    f = Frame(240, 240)
    check(f, 120, 120, 220, AQUA)
    out(f, "overlays/icon-check-aqua.png")
    f = Frame(240, 240)
    cross(f, 120, 120, 220, FLARE)
    out(f, "overlays/icon-cross-red.png")
    f = Frame(200, 200)
    f.rect(0, 0, 200, 200, 40, AQUA)
    out(f, "overlays/signal-square.png")


# ---- overview sheets ----

def overview(name, folder, tile_w, tile_h, cols):
    files = [m for m in made if m.startswith(folder + "/") and m.endswith(".png")]
    rows = -(-len(files) // cols)
    gap, cap = 24, 44
    sheet = Image.new("RGB", (gap + cols * (tile_w + gap), gap + rows * (tile_h + cap + gap)), k.rgb(SURFACE))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(k.FONTS + MONO_400, 15)
    for i, path in enumerate(files):
        x, y = gap + (i % cols) * (tile_w + gap), gap + (i // cols) * (tile_h + cap + gap)
        base = os.path.basename(path)
        dark = any(t in base for t in ("white-text", "all-white", "for-dark", "wordmark-white", "on-white", "app-icon-light",
                                       "arrow-right-light", "card-white", "brand-blocks", "check-aqua", "signal-square",
                                       "highlight-aqua"))
        tile = Image.new("RGBA", (tile_w, tile_h), k.rgb(RAIL if dark else RAISED) + (255,))
        art = Image.open(k.OUT + path).convert("RGBA")
        art.thumbnail((tile_w - 24, tile_h - 24) if folder != "frames" and folder != "backgrounds" else (tile_w, tile_h),
                      Image.LANCZOS)
        tile.alpha_composite(art, ((tile_w - art.width) // 2, (tile_h - art.height) // 2))
        sheet.paste(tile.convert("RGB"), (x, y))
        d.text((x, y + tile_h + 12), base, font=font, fill=k.rgb(TEXT_MUTED))
    sheet.save(k.OUT + name, optimize=True)


def main():
    fonts, out_dir = sys.argv[1], sys.argv[2]
    k.configure(fonts, out_dir)
    logos()
    backgrounds()
    frames()
    overlays()
    overview("overview-logos.png", "logos", 400, 225, 4)
    overview("overview-backgrounds.png", "backgrounds", 480, 270, 4)
    overview("overview-frames.png", "frames", 480, 270, 4)
    overview("overview-overlays.png", "overlays", 400, 225, 4)
    os.makedirs(k.OUT + "fonts", exist_ok=True)
    for name in sorted(os.listdir(fonts)):
        if name.endswith(".ttf") or name == "OFL.txt":
            shutil.copy(os.path.join(fonts, name), k.OUT + "fonts/" + name)
    print(len(made), "images")


if __name__ == "__main__":
    main()
