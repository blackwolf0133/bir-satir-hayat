"""İçten okuma denemesi: aynı bölümü farklı ayarlarla Fenrir'e okutur, yeni fon müziğiyle karıştırıp mp3 yapar.
Kullanım: python tools/duygu_test.py <bölüm_id> <çıktı_klasörü> <ad>  (ayarlar ortam değişkenlerinden)"""
import json, glob, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import voice as V
from engine.make import plan
eid, out, ad = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
ep = json.load(open(glob.glob(f"episodes/{eid}_*.json")[0], encoding="utf-8"))
work = f"/tmp/work_{ad}"
parts = V.speak_lines([s["text"] for s in ep["scenes"]], work)
starts, total = plan([d for _, d in parts])
wav = os.path.join(work, "mix.wav")
V.assemble(parts, starts, total, wav, work)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "160k", os.path.join(out, f"{ad}.mp3")], check=True)
print("hazır:", ad, total, "sn")
