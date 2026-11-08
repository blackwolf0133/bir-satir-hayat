"""Seslendirme. Varsayılan: Chatterbox Multilingual (MIT) + pocket-tts-turkish'in hazır "male_2" ses örneği
(CC-BY-4.0, wite-tech/pocket-tts-turkish) — kanal sahibinin seçtiği ses (15 numara).
VOICE_ENGINE=pocket verilirse eski düzen: kullanıcının klonlanmış sesi (pocket-tts-turkish).
Her cümle ayrı dosya olarak üretilir; süreleri sahne zamanlamasında kullanılır.
Kullanıcı sesi yalnızca assets/voice/aktif varken ve /tmp/ref.wav çözülmüşken kullanılır."""
import os
import re, subprocess, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOTION = os.environ.get("VOICE_EMOTION", "sakin")
TEMPO = float(os.environ.get("VOICE_TEMPO", "1.0"))
MUSIC_VOL = float(os.environ.get("MUSIC_VOL", "0.3"))
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,")
FILTERS = ("highpass=f=70,lowpass=f=11000,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
           "aecho=0.8:0.6:45|90:0.18|0.10,loudnorm=I=-16:TP=-1.5:LRA=7")


def clean(text):
    from .numbers import seslendirme_metni  # rakam / Roma rakamı / sıra sayısı -> yazı
    return seslendirme_metni(" ".join(text.replace("\n", " ").replace('"', "").replace("“", "").replace("”", "").split()))


def duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


ENGINE = os.environ.get("VOICE_ENGINE", "chatterbox")
CB_REF = os.environ.get("CB_REF", "male_2")
CB_EX = float(os.environ.get("CB_EXAGGERATION", "0.5"))
CB_CFG = float(os.environ.get("CB_CFG", "0.5"))


def _post(raw, dst):
    af = TRIM + (f"atempo={TEMPO}," if abs(TEMPO - 1) > 0.01 else "") + FILTERS
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", dst], check=True)
    os.remove(raw)


def speak_lines_chatterbox(lines, workdir):
    import torch
    _load = torch.load
    torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": "cpu"})
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from huggingface_hub import hf_hub_download
    os.makedirs(workdir, exist_ok=True)
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    ref = hf_hub_download("wite-tech/pocket-tts-turkish", f"voices/{CB_REF}.wav")
    print(f"Ses: Chatterbox, örnek ses {CB_REF}")
    out = []
    for i, line in enumerate(lines, 1):
        torch.manual_seed(7 + i)
        wav = m.generate(clean(line), language_id="tr", audio_prompt_path=ref, exaggeration=CB_EX, cfg_weight=CB_CFG)
        raw = os.path.join(workdir, f"v{i}_raw.wav")
        write_wav(raw, wav.squeeze(0).numpy(), m.sr)
        dst = os.path.join(workdir, f"v{i}.wav")
        _post(raw, dst)
        out.append((dst, duration(dst)))
    return out


_GEM = {"model": None, "dead": set()}


def _gem_models():
    """Önce bu bölümde çalışmış model, sonra sıradakiler; kotası dolanlar atlanır."""
    order = os.environ.get("GEMINI_TTS_MODELS",
                           "gemini-3.8-flash-lite-tts,gemini-3.1-flash-tts-preview,gemini-2.5-flash-preview-tts").split(",")
    order = [m.strip() for m in order if m.strip()]
    if _GEM["model"]:
        order = [_GEM["model"]] + [m for m in order if m != _GEM["model"]]
    return [m for m in order if m not in _GEM["dead"]]


GEM_VOICE = os.environ.get("GEMINI_VOICE", "Fenrir")
GEM_PROMPT = ("Read this Turkish text aloud slowly, warmly and softly, like a heartfelt, emotional narrator "
              "speaking to someone they love. Natural Istanbul Turkish, calm pace, gentle and sincere:")


def _gemini_pcm(text):
    import base64, json, time, urllib.error, urllib.request
    key = os.environ["GEMINI_API_KEY"]
    body = json.dumps({"contents": [{"parts": [{"text": GEM_PROMPT + "\n\n" + text}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                           "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEM_VOICE}}}}}).encode()
    pcm, last = None, None
    for model in _gem_models():
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    data=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req, timeout=90))
                pcm = base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
                if _GEM["model"] != model:
                    print(f"Gemini sesi: {model}", flush=True)
                _GEM["model"] = model          # bölümün geri kalanı aynı modelle (tutarlı ses)
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:300]
                last = f"{model}: HTTP {e.code} {msg}"
                print(f"::warning::{last}", flush=True)
                if e.code == 429 and "quota" in msg.lower() and "minute" not in msg.lower():
                    _GEM["dead"].add(model)    # günlük kota dolu: bu çalıştırmada bir daha deneme
                    break
                if e.code in (429, 500, 503):
                    time.sleep(10 * (attempt + 1))
                    continue
                _GEM["dead"].add(model)
                break
            except (KeyError, IndexError, TimeoutError, urllib.error.URLError) as e:
                last = f"{model}: {e}"
                print(f"::warning::{last}", flush=True)
                time.sleep(3)
        if pcm:
            break
    if pcm:
        return pcm
    raise RuntimeError(last)


def speak_lines_gemini(lines, workdir):
    """Bölüm başına TEK istek: bütün satırlar bir kerede okunur, duraklamalardan satırlara bölünür."""
    import numpy as np
    from . import gemini_ses
    os.makedirs(workdir, exist_ok=True)
    os.environ.setdefault("GEMINI_VOICE", GEM_VOICE)
    metinler = [clean(l) for l in lines]
    if os.environ.get("METIN_DUYGU"):          # içten okuma: cümle sonlarında üç nokta (daha uzun, yumuşak duraklar)
        metinler = [re.sub(r"[.!]+$", "…", m.strip()) for m in metinler]
    etiket = os.environ.get("GEMINI_ETIKET", "").strip()
    if etiket:                                 # ör. [softly] — modelin ses etiketi
        metinler = [f"{etiket} {m}" for m in metinler]
    a24, _ = gemini_ses.seslendir(metinler, GEM_PROMPT)
    out = []
    for i, part in enumerate(gemini_ses.bol(a24, 24000, metinler), 1):
        raw = os.path.join(workdir, f"v{i}_raw.pcm")
        (np.clip(part, -1, 1) * 32767).astype("<i2").tofile(raw)
        dst = os.path.join(workdir, f"v{i}.wav")
        af = TRIM + (f"atempo={TEMPO}," if abs(TEMPO - 1) > 0.01 else "") + FILTERS
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", raw,
                        "-af", af, "-ar", str(SR), "-ac", "1", dst], check=True)
        os.remove(raw)
        out.append((dst, duration(dst)))
    return out

def speak_lines(lines, workdir):
    if ENGINE == "gemini":
        if os.environ.get("GEMINI_API_KEY"):
            try:
                return speak_lines_gemini(lines, workdir)
            except Exception as e:  # noqa: BLE001
                print(f"::warning::Gemini sesi çalışmadı, Chatterbox'a geçiliyor: {e}")
        else:
            print("::warning::GEMINI_API_KEY yok, Chatterbox kullanılacak")
        return speak_lines_chatterbox(lines, workdir)
    if ENGINE == "chatterbox":
        return speak_lines_chatterbox(lines, workdir)
    from pocket_tts_turkish import TurkishTTS, save_wav
    os.makedirs(workdir, exist_ok=True)
    tts = TurkishTTS.from_pretrained(device="cpu")
    ref = os.environ.get("VOICE_REF", "/tmp/ref.wav")
    use_mine = os.path.exists(os.path.join(ROOT, "assets", "voice", "aktif")) and os.path.exists(ref)
    voice = tts.voice_from_file(ref) if use_mine else os.environ.get("POCKET_VOICE", "male_1")
    print("Ses:", "kullanıcının kendi sesi" if use_mine else f"hazır ses {voice}")
    out = []
    for i, line in enumerate(lines, 1):
        raw = os.path.join(workdir, f"v{i}_raw.wav")
        dst = os.path.join(workdir, f"v{i}.wav")
        kw = {"voice": voice, "seed": 7}
        if EMOTION:
            kw["emotion"] = EMOTION
        save_wav(raw, tts.generate(clean(line), **kw), tts.sample_rate)
        _post(raw, dst)
        out.append((dst, duration(dst)))
    return out


def _piano_note(f, dur, sr, vel=1.0, rng=None):
    """Sıcak piyano tınısı: hafif inharmonik harmonikler, her harmoniğin kendi sönümü, yumuşak vuruş."""
    t = np.arange(int(sr * dur)) / sr
    out = np.zeros_like(t)
    B = 0.0004                                            # tel sertliği (inharmoniklik)
    for k, amp in enumerate([1.0, 0.42, 0.22, 0.12, 0.07, 0.04], 1):
        fk = f * k * np.sqrt(1 + B * k * k)
        decay = 1.1 + 0.9 * k                            # tiz harmonikler daha hızlı söner
        det = 1 + (rng.uniform(-0.0006, 0.0006) if rng is not None else 0)
        out += amp * np.sin(2 * np.pi * fk * det * t) * np.exp(-t * decay * (f / 440) ** 0.35)
    att = 1 - np.exp(-t * 180)
    return out * att * vel


def _pad(freqs, dur, sr):
    """Yumuşak yaylı katmanı: hafif detune edilmiş, az harmonikli, yavaş giriş/çıkış."""
    t = np.arange(int(sr * dur)) / sr
    out = np.zeros_like(t)
    for f in freqs:
        for d in (-0.004, 0.0, 0.0045):
            ph = np.random.uniform(0, 6.28)
            for k, amp in ((1, 1.0), (2, 0.28), (3, 0.12)):
                out += amp * np.sin(2 * np.pi * f * (1 + d) * k * t + ph)
    vib = 1 + 0.06 * np.sin(2 * np.pi * 0.23 * t)
    env = np.minimum(1, t / 1.6) * np.minimum(1, (dur - t) / 1.4).clip(0, 1)
    return out * env * vib


def _ekle(buf, s, x):
    if 0 <= s < len(buf):
        e = min(len(buf), s + len(x))
        buf[s:e] += x[: e - s]


def piano_bed(seconds, sr=SR):
    """Duygusal fon: yavaş, hüzünlü piyano (Am - F - C - Em) + yaylı katmanı. Tamamen sentetik (telifsiz)."""
    rng = np.random.default_rng(7)
    np.random.seed(7)
    mid = lambda n: 440 * 2 ** ((n - 69) / 12)            # noqa: E731
    chords = [(45, [57, 60, 64, 69, 72]), (41, [53, 57, 60, 65, 69]),
              (48, [55, 60, 64, 67, 72]), (40, [55, 59, 64, 67, 71])]
    bar = 3.6                                            # her akor 3,6 sn (yavaş)
    n = int((seconds + 10) * sr)
    piano = np.zeros(n, np.float32)
    pad = np.zeros(n, np.float32)
    pattern = [0, 2, 3, 4, 3, 2]                         # yumuşak arpej
    t0, i = 0.0, 0
    while t0 < seconds + 1:
        bass, notes = chords[i % 4]
        s = int(t0 * sr)
        nb = _piano_note(mid(bass), 4.5, sr, 0.55, rng)
        _ekle(piano, s, nb)
        for j, idx in enumerate(pattern):
            ts = t0 + j * bar / len(pattern) + rng.uniform(-0.02, 0.02)   # insan eli gibi hafif kayma
            vel = 0.32 + 0.12 * (j == 0) + rng.uniform(-0.04, 0.04)
            nt = _piano_note(mid(notes[idx]), 3.2, sr, vel, rng)
            ss = int(ts * sr)
            _ekle(piano, ss, nt)
        pd = _pad([mid(notes[0] - 12), mid(notes[1] - 12), mid(notes[2])], bar + 1.4, sr) * 0.05
        piano_s = int(max(0, t0 - 0.3) * sr)
        _ekle(pad, piano_s, pd)
        t0 += bar
        i += 1
    mix = piano * 0.55 + pad
    mix = mix[: int(seconds * sr)]
    return mix / (np.abs(mix).max() + 1e-6) * 0.9


def write_wav(path, a, sr=SR):
    a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def assemble(parts, starts, total, out_path, workdir):
    """Cümleleri verilen başlangıç zamanlarına yerleştirir, altına piyano koyar."""
    voice = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for (path, _), st in zip(parts, starts):
        a = read_wav(path)
        s = int(st * SR)
        voice[s:s + len(a)] += a[: len(voice) - s]
    voice = voice[: int(total * SR)]
    vw = os.path.join(workdir, "voice_full.wav")
    mw = os.path.join(workdir, "music.wav")
    write_wav(vw, voice)
    write_wav(mw, piano_bed(total))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vw, "-i", mw, "-filter_complex",
                    # müzik: yankı + yumuşatma; konuşma varken kısılır (sidechain), aralarda yükselir
                    f"[1]lowpass=f=5200,aecho=0.8:0.82:70|140|230|370:0.32|0.24|0.17|0.11,volume={MUSIC_VOL},"
                    f"afade=t=in:d=1.5,afade=t=out:st={total - 2.0:.2f}:d=1.9[m];"
                    "[0]asplit=2[v][sc];"
                    "[m][sc]sidechaincompress=threshold=0.03:ratio=3.5:attack=80:release=600[md];"
                    "[v][md]amix=inputs=2:duration=first:normalize=0", "-ar", str(SR), out_path], check=True)
