"""Contact sheet of PNGs: sheet.py OUT.png SCALE COLS BG FILE... (each tile labelled with its file stem)."""
import os, sys
from PIL import Image, ImageDraw


def sheet(out, files, scale=2, cols=8, bg=(40, 40, 48), label=True, pad=4):
    ims = [Image.open(f).convert('RGBA') for f in files]
    tw = max(i.width for i in ims) * scale; th = max(i.height for i in ims) * scale
    lh = 12 if label else 0
    rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGBA', (cols * (tw + pad) + pad, rows * (th + lh + pad) + pad), bg + (255,))
    d = ImageDraw.Draw(S)
    for n, (f, im) in enumerate(zip(files, ims)):
        x = pad + (n % cols) * (tw + pad); y = pad + (n // cols) * (th + lh + pad)
        # checker behind transparent pixels so alpha reads
        ch = Image.new('RGBA', (im.width * scale, im.height * scale), (90, 90, 100, 255))
        cd = ImageDraw.Draw(ch)
        for yy in range(0, ch.height, 8):
            for xx in range(0, ch.width, 8):
                if (xx // 8 + yy // 8) % 2: cd.rectangle([xx, yy, xx + 7, yy + 7], fill=(120, 120, 130, 255))
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        ch.alpha_composite(big)
        S.paste(ch, (x, y + lh))
        if label: d.text((x, y), os.path.basename(f)[:-4][-18:], fill=(230, 230, 230, 255))
    S.save(out)
    return out


if __name__ == '__main__':
    out, scale, cols, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
    sheet(out, files, scale, cols)


def rows(out, spec, bg=(40, 40, 48), pad=4):
    """Labelled rows: spec is [(title, scale, [png...]), ...]; each tile shows its file stem."""
    from PIL import ImageFont
    rendered = []
    for title, scale, files in spec:
        ims = [(f, Image.open(f).convert('RGBA')) for f in files]
        rendered.append((title, scale, ims))
    W = max(pad + sum(im.width * s + pad for _, im in ims) for _, s, ims in rendered)
    W = max(W, 400)
    H = sum(14 + 12 + max(im.height * s for _, im in ims) + pad for _, s, ims in rendered) + pad
    S = Image.new('RGBA', (W, H), bg + (255,))
    d = ImageDraw.Draw(S)
    y = pad
    for title, s, ims in rendered:
        d.text((pad, y), title, fill=(255, 220, 120, 255)); y += 14
        x = pad
        for f, im in ims:
            d.text((x, y), os.path.basename(f)[:-4][-20:], fill=(200, 200, 200, 255))
            ch = Image.new('RGBA', (im.width * s, im.height * s), (90, 90, 100, 255))
            cd = ImageDraw.Draw(ch)
            for yy in range(0, ch.height, 8):
                for xx in range(0, ch.width, 8):
                    if (xx // 8 + yy // 8) % 2: cd.rectangle([xx, yy, xx + 7, yy + 7], fill=(120, 120, 130, 255))
            ch.alpha_composite(im.resize((im.width * s, im.height * s), Image.NEAREST))
            S.paste(ch, (x, y + 12))
            x += im.width * s + pad
        y += 12 + max(im.height * s for _, im in ims) + pad
    S.save(out)
    return out
