"""Sahne çizimi: FLUX.2-klein-4B (Apache-2.0), stable-diffusion.cpp ile CPU'da.
Kullanım: python -m engine.scenes <bölüm.json> <sahne_no> <sd-cli yolu> <çıktı_klasörü>"""
import os, re, sys, time, subprocess
from huggingface_hub import list_repo_files, hf_hub_download

MODEL = {
    "diffusion": [("leejet/FLUX.2-klein-4B-GGUF", r"Q4_0\.gguf$")],
    "llm": [("unsloth/Qwen3-4B-GGUF", r"Q4_K_M\.gguf$")],
    "vae": [("Comfy-Org/flux2-klein-4B", r"vae/.*\.safetensors$")],
    "steps": 4,
}
STYLE = ("Children's storybook illustration, hand-drawn watercolor and colored pencil with fine ink outlines, "
         "warm cozy palette, soft golden light, textured cream paper, gentle and heartfelt mood. No text, no letters.")
WIDTH, HEIGHT = 768, 896


def fetch(cands):
    for repo, pat in cands:
        files = list_repo_files(repo)
        hits = sorted(f for f in files if re.search(pat, f))
        if hits:
            return hf_hub_download(repo, hits[0])
    raise SystemExit(f"model bulunamadı: {cands}")


def build_prompt(ep, idx):
    sc = ep["scenes"][idx - 1]["prompt"]
    for key, desc in ep.get("characters", {}).items():
        sc = sc.replace("{" + key + "}", desc)
    return f"{sc} {STYLE}"


def main():
    import json
    ep_path, idx, sd, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    ep = json.load(open(ep_path, encoding="utf-8"))
    if idx > len(ep["scenes"]):
        print(f"Bölümde {idx}. sahne yok, atlanıyor.")
        return
    os.makedirs(out, exist_ok=True)
    paths = {k: fetch(MODEL[k]) for k in ("diffusion", "llm", "vae")}
    dst = os.path.join(out, f"sahne{idx}.png")
    seed = int(ep.get("seed", 100)) + idx
    t = time.time()
    cmd = [sd, "--diffusion-model", paths["diffusion"], "--llm", paths["llm"], "--vae", paths["vae"],
           "-p", build_prompt(ep, idx), "--cfg-scale", "1.0", "--steps", str(MODEL["steps"]),
           "--sampling-method", "euler", "-W", str(WIDTH), "-H", str(HEIGHT), "-s", str(seed),
           "-t", str(os.cpu_count() or 4), "-o", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"sahne {idx} çizilemedi")
    print(f"sahne {idx}: {time.time() - t:.0f} sn")


if __name__ == "__main__":
    main()
