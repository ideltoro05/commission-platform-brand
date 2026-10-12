"""Build the images the brand page itself shows (its assets/ folder).

Usage: python make_brand.py <fonts_dir> <assets_dir>
The video asset pack is built by make_pack.py; both draw with brandkit.py.
"""
import sys

import brandkit as k
import make_pack as pack
from brandkit import BONE, RAIL, RAISED, SANS_600, Frame


def logo(name, variant, bg=None, em=120):
    w, h = k.lockup_size(em)
    pad = h * 0.3
    f = Frame(w + pad * 2, h + pad * 2, bg)
    f.lockup(pad, pad, em, variant)
    f.save(name)


def main():
    k.configure(sys.argv[1], sys.argv[2])

    logo("logo-on-light.png", "light")
    logo("logo-on-dark.png", "dark")
    logo("logo-rail.png", "dark", bg=RAIL)
    for name, variant in (("logo.svg", "light"), ("logo-on-dark.svg", "dark"), ("logo-mono.svg", "mono")):
        k.lockup_svg(name, variant)
    for name, variant in (("mark.svg", "light"), ("mark-on-dark.svg", "dark"), ("mark-mono.svg", "mono")):
        k.mark_svg(name, variant)
    k.app_icon_svg("app-icon.svg")
    k.app_icon_svg("favicon.svg")
    for name, px in (("logo-mark.png", 512), ("apple-touch-icon.png", 180), ("favicon-32.png", 32)):
        k.app_icon_frame(px).save(name)

    pack.title_frame("lesson-title-card.png", "Insurance principles / Lesson 01", "What insurance is",
                     "Part 1 of 3 · 06:18")
    pack.key_term_frame("lesson-key-term.png")
    f = pack.frame(RAIL)
    pack.blocks_right(f)
    f.save("lesson-title-background.png")
    pack.frame(RAISED).save("lesson-avatar-backdrop.png")

    f = Frame(1200, 630, RAIL)
    pack.blocks_right(f, 840, 0.62)
    f.lockup(64, 64, 34, "dark")
    f.text(64, 452, "Pay, worked out", SANS_600, 88, BONE, -0.04)
    f.text(64, 548, "line by line", SANS_600, 88, BONE, -0.04)
    f.save("social-card.png")


if __name__ == "__main__":
    main()
