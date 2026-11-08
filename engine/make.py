"""Bölüm videosu: sahne resimleri + kullanıcının sesi + el yazısı + imza.
Kullanım: python -m engine.make <bölüm.json> <resim_klasörü> <çıktı.mp4>"""
import json, os, sys
from . import voice as V
from . import video as VID

LEAD = 0.3       # ilk cümleden önce sessizlik
GAP = 0.35       # cümleler arası nefes
LONG_GAP = 0.6   # son cümleden önce
TAIL = 2.6       # son cümleden sonra (imza çizilir)


def plan(durs):
    starts, t = [], LEAD
    for i, d in enumerate(durs):
        if i == len(durs) - 1 and i > 0:
            t += LONG_GAP - GAP
        starts.append(t)
        t += d + GAP
    total = max(starts[-1] + durs[-1] + 1.2, starts[-1] + TAIL)
    return starts, round(total, 2)


def main():
    ep_path, img_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    ep = json.load(open(ep_path, encoding="utf-8"))
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "work_" + ep["id"])
    os.makedirs(work, exist_ok=True)
    lines = [s["text"] for s in ep["scenes"]]
    parts = V.speak_lines(lines, work)
    starts, total = plan([d for _, d in parts])
    audio = os.path.join(work, "audio.wav")
    V.assemble(parts, starts, total, audio, work)
    scenes = []
    for i, (s, st) in enumerate(zip(ep["scenes"], starts), 1):
        scenes.append({"t": 0 if i == 1 else round(st - 0.3, 2), "img": os.path.join(img_dir, f"sahne{i}.png"),
                       "text": s["text"], "prompt": s.get("prompt", "")})
    VID.render(scenes, audio, out, total)
    print(f"Hazır: {out} ({total} sn)")


if __name__ == "__main__":
    main()
