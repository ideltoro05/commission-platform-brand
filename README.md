# Your EZ Payroll brand page

A static page that presents the Deep Aqua brand kit (logo, colors, Geist and Geist Mono, lesson frames) at a public URL, so tools that build a brand kit from a website link can read it.

Live at https://ideltoro05.github.io/commission-platform-brand/

- `index.html`, `styles.css`: the page. Hex values are written out in full so an importer finds the palette.
- `assets/`: the logo (SVG and PNG), icons and 1920 by 1080 lesson frames.
- `tools/make_brand.py`: rebuilds the logo files and page images from the fonts (needs `fonttools`, `uharfbuzz` and `pillow`).
- `fonts/`: Geist and Geist Mono (SIL Open Font License, see `fonts/OFL.txt`), from https://github.com/vercel/geist-font.

The brand kit itself is the copy of record. Change values there first, then here.
