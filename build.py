#!/usr/bin/env python3
"""Build the "Nord cards" GRUB theme for panels that are natively PORTRAIT (e.g. GPD MicroPC / Pocket).

GRUB cannot rotate text, so the background and the card contents (icon + name) are pre-rotated
images and GRUB's own item text is painted in the card colour (invisible). Result: it reads upright
when the device is held in landscape.

  python3 build.py                       # Nord gradient background
  python3 build.py --wallpaper foo.jpg   # your wallpaper (blurred + darkened)
  python3 build.py --out theme

Entries (4 cards): Linux Mint, Windows, Advanced options, UEFI Firmware. Edit LABELS/ICONS below
if your menu differs; the card order must match the order in your grub.cfg.
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

W, H = 1920, 1080                    # landscape view you see
CW, CH, GAP = 350, 280, 40           # card size / gap (landscape)
N = 4
LX0 = (W - (N * CW + (N - 1) * GAP)) // 2
LY0 = 350
R = 32                               # corner radius; GRUB adds 2*R to a box along the item_height axis
ICON = 96
SS = 4                               # supersampling for drawn shapes

RM = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Medium.ttf"
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WHITE = (236, 239, 244, 255)

# Nord palette
UN, UNB = (59, 66, 82, 255), (66, 75, 94, 255)        # card fill / border (border ~ fill: hidden text can't show)
SE, SEB = (94, 129, 172, 255), (129, 161, 193, 255)   # selected fill / border

LABELS = ["Linux Mint", "Windows", "Advanced options", "UEFI Firmware"]


def to_portrait(img):                # landscape -> framebuffer (rotate 90 deg clockwise)
    return img.rotate(-90, expand=True)


def pos_portrait(lx, ly, w, h):      # landscape rect -> top-left in the portrait framebuffer
    return (H - (ly + h), lx)


# ---------------------------------------------------------------- background
def make_background(wallpaper):
    if wallpaper:
        im = Image.open(wallpaper).convert("RGB")
        im = ImageOps.fit(im, (W, H), Image.LANCZOS)
        im = im.filter(ImageFilter.GaussianBlur(5))
        im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(0.48)).enhance(0.85)
    else:
        top, bottom = (46, 52, 64), (59, 66, 82)
        im = ImageOps.colorize(Image.linear_gradient("L").resize((W, H)), top, bottom)
        glow = ImageOps.colorize(Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - v),
                                 (0, 0, 0), (94, 129, 172))
        im = Image.blend(im, Image.blend(im, glow, 0.5), 0.35)
    shade = Image.linear_gradient("L").resize((W, H)).point(lambda v: int(25 + v * 0.45))
    im = Image.composite(Image.new("RGB", (W, H), (46, 52, 64)), im, shade)
    return im


# ---------------------------------------------------------------- 9-slice cards
def ninepatch(out, prefix, fill, border):
    n = 2 * R + 1
    big = Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((0, 0, n * SS - 1, n * SS - 1), radius=R * SS, fill=border)
    b = 2 * SS
    d.rounded_rectangle((b, b, n * SS - 1 - b, n * SS - 1 - b), radius=(R - 2) * SS, fill=fill)
    im = big.resize((n, n), Image.LANCZOS)
    parts = {"nw": (0, 0, R, R), "n": (R, 0, R + 1, R), "ne": (R + 1, 0, n, R),
             "w": (0, R, R, R + 1), "c": (R, R, R + 1, R + 1), "e": (R + 1, R, n, R + 1),
             "sw": (0, R + 1, R, n), "s": (R, R + 1, R + 1, n), "se": (R + 1, R + 1, n, n)}
    for k, box in parts.items():
        im.crop(box).save(os.path.join(out, "%s_%s.png" % (prefix, k)))


# ---------------------------------------------------------------- icons
def _canvas():
    return Image.new("RGBA", (ICON * SS, ICON * SS), (0, 0, 0, 0))


def _fin(im):
    return im.resize((ICON, ICON), Image.LANCZOS)


def icon_windows():
    im = _canvas(); d = ImageDraw.Draw(im); u = ICON * SS
    g = u * 0.045; m = u * 0.12; c = WHITE
    d.polygon([(m, m + u * .06), (u / 2 - g, m + u * .02), (u / 2 - g, u / 2 - g), (m, u / 2 - g)], fill=c)
    d.polygon([(u / 2 + g, m + u * .01), (u - m, m - u * .03), (u - m, u / 2 - g), (u / 2 + g, u / 2 - g)], fill=c)
    d.polygon([(m, u / 2 + g), (u / 2 - g, u / 2 + g), (u / 2 - g, u - m - u * .02), (m, u - m - u * .06)], fill=c)
    d.polygon([(u / 2 + g, u / 2 + g), (u - m, u / 2 + g), (u - m, u - m + u * .03), (u / 2 + g, u - m + u * .01)], fill=c)
    return _fin(im)


def icon_gear():
    im = _canvas(); d = ImageDraw.Draw(im); u = ICON * SS
    cx = cy = u / 2; col = (216, 222, 233, 255); teeth = 8
    ro, ri = u * .46, u * .35
    pts = []
    for i in range(teeth):
        base = 2 * math.pi * i / teeth
        for da, r in ((-0.30, ri), (-0.17, ro), (0.17, ro), (0.30, ri)):
            a = base + da
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=col)
    d.ellipse((cx - u * .17, cy - u * .17, cx + u * .17, cy + u * .17), fill=(0, 0, 0, 0))
    return _fin(im)


def icon_chip():
    im = _canvas(); d = ImageDraw.Draw(im); u = ICON * SS
    col = (216, 222, 233, 255); m = u * .27
    d.rounded_rectangle((m, m, u - m, u - m), radius=u * .05, fill=col)
    d.rounded_rectangle((m + u * .07, m + u * .07, u - m - u * .07, u - m - u * .07), radius=u * .03, fill=(0, 0, 0, 0))
    d.rectangle((m + u * .15, m + u * .15, u - m - u * .15, u - m - u * .15), fill=col)
    for i in range(4):
        p = m + u * .07 + i * (u - 2 * m - u * .14) / 3
        pw = u * .035
        d.rectangle((p - pw, u * .13, p + pw, m), fill=col)
        d.rectangle((p - pw, u - m, p + pw, u * .87), fill=col)
        d.rectangle((u * .13, p - pw, m, p + pw), fill=col)
        d.rectangle((u - m, p - pw, u * .87, p + pw), fill=col)
    return _fin(im)


def icon_mint():
    return Image.open(os.path.join(A, "linuxmint.png")).convert("RGBA").resize((ICON, ICON), Image.LANCZOS)


def fit_font(text, maxw):
    s = 32
    f = ImageFont.truetype(RM, s)
    while f.getlength(text) > maxw and s > 20:
        s -= 2
        f = ImageFont.truetype(RM, s)
    return f


def text_img(text, font, color, pad=6):
    w = int(font.getlength(text)) + 2 * pad
    h = font.size + 2 * pad + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad, pad), text, font=font, fill=color)
    return im


def hint_img():
    fw, fs = ImageFont.truetype(RM, 26), ImageFont.truetype(DJ, 24)
    col, acc = (190, 198, 212, 255), (136, 192, 208, 255)
    parts = [("▲", fs, acc), (" Up: move left", fw, col), ("        ", fw, col),
             ("▼", fs, acc), (" Down: move right", fw, col), ("        ", fw, col),
             ("Enter", fw, acc), (": boot", fw, col)]
    width = int(sum(f.getlength(t) for t, f, c in parts)) + 24
    im = Image.new("RGBA", (width, 54), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 12
    for t, f, c in parts:
        d.text((x, 8), t, font=f, fill=c)
        x += f.getlength(t)
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wallpaper", help="image to use as (blurred, darkened) background")
    ap.add_argument("--out", default=os.path.join(HERE, "theme"))
    args = ap.parse_args()
    out = args.out
    os.makedirs(out, exist_ok=True)

    for f in ("roboto-22.pf2", "roboto-30.pf2"):
        with open(os.path.join(A, f), "rb") as s, open(os.path.join(out, f), "wb") as d:
            d.write(s.read())

    land_bg = make_background(args.wallpaper)
    to_portrait(land_bg.convert("RGBA")).convert("RGB").save(os.path.join(out, "background.png"))

    ninepatch(out, "item", UN, UNB)
    ninepatch(out, "select", SE, SEB)

    icons = [icon_mint(), icon_windows(), icon_gear(), icon_chip()]
    for i, (ic, lab) in enumerate(zip(icons, LABELS)):
        card = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        card.alpha_composite(ic, ((CW - ICON) // 2, 46))
        f = fit_font(lab, CW - 40)
        ImageDraw.Draw(card).text(((CW - f.getlength(lab)) / 2, CH - 88), lab, font=f, fill=WHITE)
        to_portrait(card).save(os.path.join(out, "card%d.png" % i))

    title = text_img("Select a system", ImageFont.truetype(RM, 50), WHITE)
    hint = hint_img()
    to_portrait(title).save(os.path.join(out, "title.png"))
    to_portrait(hint).save(os.path.join(out, "hint.png"))
    tp = pos_portrait((W - title.width) // 2, 190, title.width, title.height)
    hp = pos_portrait((W - hint.width) // 2, LY0 + CH + 80, hint.width, hint.height)

    cx, cy = H - (LY0 + CH), LX0
    item_h = CW - 2 * R              # GRUB draws each box item_height + 2*R long -> exactly CW
    spacing = (CW + GAP) - item_h    # pitch between boxes = item_height + spacing
    theme = '''# Nord GRUB theme "cards": portrait framebuffer (1080x1920), pre-rotated so it reads upright in landscape.
# Entry names/icons are images (GRUB cannot rotate text); GRUB's own item text is painted in the card
# colour so it is invisible. GRUB paints later-declared components UNDER earlier ones.
desktop-image: "background.png"
desktop-color: "#2e3440"
title-text: ""
terminal-font: "Roboto Regular 22"
terminal-left: "5%"
terminal-top: "5%"
terminal-width: "90%"
terminal-height: "90%"
terminal-border: "0"
'''
    for i in range(N):
        px, py = pos_portrait(LX0 + i * (CW + GAP), LY0, CW, CH)
        theme += '\n+ image {\n    left = %d\n    top = %d\n    file = "card%d.png"\n}\n' % (px, py, i)
    theme += '\n+ image {\n    left = %d\n    top = %d\n    file = "title.png"\n}\n' % tp
    theme += '\n+ image {\n    left = %d\n    top = %d\n    file = "hint.png"\n}\n' % hp
    theme += '''
+ boot_menu {
    left = %d
    top = %d
    width = %d
    height = %d
    item_font = "Roboto Regular 22"
    selected_item_font = "Roboto Regular 22"
    item_color = "#3b4252"
    selected_item_color = "#5e81ac"
    item_height = %d
    item_padding = 0
    item_spacing = %d
    item_icon_space = 0
    icon_width = 1
    icon_height = 1
    item_pixmap_style = "item_*.png"
    selected_item_pixmap_style = "select_*.png"
    scrollbar = false
}
''' % (cx, cy, CH, N * (CW + GAP) + 20, item_h, spacing)
    with open(os.path.join(out, "theme.txt"), "w") as fh:
        fh.write(theme)

    # preview = what you see holding the device in landscape (2nd card selected)
    bg = Image.open(os.path.join(out, "background.png")).convert("RGBA")
    for i in range(N):
        px, py = pos_portrait(LX0 + i * (CW + GAP), LY0, CW, CH)
        pill = Image.new("RGBA", (CH, CW), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, CH - 1, CW - 1), radius=R,
                                               fill=SE if i == 1 else UN, outline=SEB if i == 1 else UNB, width=2)
        bg.alpha_composite(pill, (px, py))
        bg.alpha_composite(Image.open(os.path.join(out, "card%d.png" % i)), (px, py))
    bg.alpha_composite(Image.open(os.path.join(out, "title.png")), tp)
    bg.alpha_composite(Image.open(os.path.join(out, "hint.png")), hp)
    bg.rotate(90, expand=True).convert("RGB").resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "preview.png"))
    print("theme written to", out)


if __name__ == "__main__":
    main()
