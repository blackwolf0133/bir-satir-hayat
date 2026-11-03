"""Bir Satır Hayat video birleştirici.
Sahne = görsel + el yazısı cümle. Krem kâğıt zemin, üstte yazı, altta görsel (üst kenarı kâğıda eriyor),
yavaş zoom, sahneler arası yumuşak geçiş, yazı yavaşça beliriyor."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
PAPER = (247, 240, 228)
INK = (72, 46, 36)
FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "PatrickHand-Regular.ttf")
HANDLE = "@birsatir.hayat"
IMG_TOP = 640          # görselin başladığı y
FADE = 0.55            # sahne geçiş süresi (sn)


def paper():
    rng = np.random.default_rng(3)
    base = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
    noise = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    noise = np.array(Image.fromarray(((noise * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) - 128
    base += noise[..., None] * 0.18
    # hafif kenar kararması
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    base *= (1 - 0.06 * np.clip(d - 0.6, 0, 1))[..., None]
    return base.clip(0, 255)


def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def text_layer(text, info=None):
    """Şeffaf RGBA yazı katmanı (üst bölge ortasında). info'ya yazının alt sınırı yazılır."""
    lay = Image.new("RGBA", (W, IMG_TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    size = 96
    while True:
        font = ImageFont.truetype(FONT, size)
        lines = [l for part in text.split('\n') for l in wrap(d, part, font, W - 160)]
        lh = int(size * 1.22)
        if len(lines) * lh < IMG_TOP - 200 or size < 60:
            break
        size -= 4
    y = (IMG_TOP - len(lines) * lh) // 2 + 30
    for ln in lines:
        x = (W - d.textlength(ln, font=font)) / 2
        d.text((x, y), ln, font=font, fill=INK + (255,))
        y += lh
    if info is not None:
        info["bottom"] = y
    return lay


RUST = (184, 84, 52)


def signature(frame, prog, ybase, alpha):
    """İmza: el çizimi tek satır (prog 0..1 ile soldan sağa çizilir) + kalp + kullanıcı adı."""
    import math
    lay = Image.new("RGBA", (W, IMG_TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1 = 300, 780
    y0 = ybase + 34
    n = max(2, int(120 * prog))
    pts = [(x0 + (x1 - x0) * i / 119, y0 + math.sin(i / 119 * math.pi * 1.3) * 6 - i / 119 * 5) for i in range(n)]
    d.line(pts, fill=RUST + (255,), width=7, joint="curve")
    if prog >= 1:
        hx, hy, hs = x1 + 22, y0 - 10, 17
        heart = [(hx + hs * math.sin(t) ** 3, hy - hs * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
                 for t in np.linspace(0, 2 * math.pi, 60)]
        d.polygon(heart, fill=RUST + (255,))
        f = ImageFont.truetype(FONT, 44)
        tx = HANDLE
        d.text(((W - d.textlength(tx, font=f)) / 2, y0 + 30), tx, font=f, fill=INK + (200,))
    a = np.asarray(lay, np.float32)
    al = a[..., 3:4] / 255 * alpha
    frame[:IMG_TOP] = frame[:IMG_TOP] * (1 - al) + a[..., :3] * al


def image_layer(path):
    """Görseli alt bölgeye yerleştirmek için hazırlar (biraz büyük: zoom payı)."""
    im = Image.open(path).convert("RGB")
    bh = H - IMG_TOP
    scale = max(W / im.width, bh / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    return im


def mask_top():
    bh = H - IMG_TOP
    m = np.ones((bh, W), np.float32)
    g = 170
    m[:g] = (np.linspace(0, 1, g) ** 1.6)[:, None]
    return m[..., None]


def render(scenes, audio, out, total):
    bg = paper()
    mtop = mask_top()
    bh = H - IMG_TOP
    prepared = []
    for s in scenes:
        info = {}
        prepared.append({"t": s["t"], "img": image_layer(s["img"]),
                         "txt": np.array(text_layer(s["text"], info), np.float32), "bottom": info["bottom"]})
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for f in range(n):
        t = f / FPS
        # aktif sahne ve bir önceki (geçiş için)
        idx = max(i for i, p in enumerate(prepared) if p["t"] <= t)
        frame_layers = []
        for j in (idx - 1, idx):
            if j < 0:
                continue
            p = prepared[j]
            nxt = prepared[j + 1]["t"] if j + 1 < len(prepared) else total
            if j == idx - 1:
                a = 1 - min(1, (t - prepared[idx]["t"]) / FADE)
                if a <= 0:
                    continue
            else:
                a = min(1, (t - p["t"]) / FADE) if j > 0 else 1.0
            frame_layers.append((p, a, (t - p["t"]) / max(0.1, nxt - p["t"] + FADE)))
        frame = bg.copy()
        for p, a, prog in frame_layers:
            im = p["img"]
            z = 1.0 + 0.06 * min(1, max(0, prog))
            # kırpma kutusu: zoom arttıkça daha küçük alan
            r = W / bh
            bw0 = min(im.width, im.height * r); bh0 = bw0 / r
            cw, ch = bw0 / z, bh0 / z
            cx = im.width / 2
            cy = min(max(im.height * 0.5, ch / 2), im.height - ch / 2)
            box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
            crop = im.crop(box).resize((W, bh), Image.BILINEAR)
            # görsel bölge oranına göre kırp (resize zaten W x bh)
            region = frame[IMG_TOP:]
            ci = np.asarray(crop, np.float32)
            m = mtop * a
            frame[IMG_TOP:] = region * (1 - m) + ci * m
            # yazı: sahne başlangıcından 0.15 sn sonra 0.5 sn'de belirir
            ta = a * min(1, max(0, (t - p["t"] - 0.1) / 0.5)) if p is frame_layers[-1][0] else a
            tl = p["txt"]
            al = tl[..., 3:4] / 255 * ta
            frame[:IMG_TOP] = frame[:IMG_TOP] * (1 - al) + tl[..., :3] * al
        sig_start = prepared[-1]["t"] + 2.2
        if t >= sig_start:
            signature(frame, min(1, (t - sig_start) / 1.0), prepared[-1]["bottom"], 1.0)
        ff.stdin.write(frame.clip(0, 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    render(cfg["scenes"], cfg["audio"], cfg["out"], cfg["total"])
