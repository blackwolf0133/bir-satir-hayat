"""Seslendirme. Varsayılan: Chatterbox Multilingual (MIT) + pocket-tts-turkish'in hazır "male_2" ses örneği
(CC-BY-4.0, wite-tech/pocket-tts-turkish) — kanal sahibinin seçtiği ses (15 numara).
VOICE_ENGINE=pocket verilirse eski düzen: kullanıcının klonlanmış sesi (pocket-tts-turkish).
Her cümle ayrı dosya olarak üretilir; süreleri sahne zamanlamasında kullanılır.
Kullanıcı sesi yalnızca assets/voice/aktif varken ve /tmp/ref.wav çözülmüşken kullanılır."""
import os, subprocess, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOTION = os.environ.get("VOICE_EMOTION", "sakin")
TEMPO = float(os.environ.get("VOICE_TEMPO", "1.0"))
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
    af = (f"atempo={TEMPO}," if abs(TEMPO - 1) > 0.01 else "") + FILTERS
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


GEM_VOICE = os.environ.get("GEMINI_VOICE", "Fenrir")
GEM_PROMPT = ("Read this Turkish line aloud slowly, warmly and softly, like a heartfelt, emotional narrator "
              "speaking to someone they love. Natural Istanbul Turkish, calm pace, gentle and sincere:")


def _gemini_pcm(text):
    import base64, json, time, urllib.error, urllib.request
    key = os.environ["GEMINI_API_KEY"]
    models = os.environ.get("GEMINI_TTS_MODELS",
                            "gemini-3.8-flash-lite-tts,gemini-3.1-flash-tts-preview,gemini-2.5-flash-preview-tts").split(",")
    body = json.dumps({"contents": [{"parts": [{"text": GEM_PROMPT + "\n\n" + text}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                           "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEM_VOICE}}}}}).encode()
    last = None
    for model in models:
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model.strip()}:generateContent",
                    data=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req, timeout=180))
                return base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            except urllib.error.HTTPError as e:
                last = f"{model}: HTTP {e.code} {e.read().decode()[:200]}"
                if e.code in (429, 500, 503):
                    time.sleep(20 * (attempt + 1))
                    continue
                break
            except (KeyError, IndexError, TimeoutError, urllib.error.URLError) as e:
                last = f"{model}: {e}"
                time.sleep(5)
    raise RuntimeError(last)


def speak_lines_gemini(lines, workdir):
    os.makedirs(workdir, exist_ok=True)
    print(f"Ses: Google Gemini, {GEM_VOICE}")
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,")
    out = []
    for i, line in enumerate(lines, 1):
        raw = os.path.join(workdir, f"v{i}_raw.pcm")
        open(raw, "wb").write(_gemini_pcm(clean(line)))
        dst = os.path.join(workdir, f"v{i}.wav")
        af = trim + (f"atempo={TEMPO}," if abs(TEMPO - 1) > 0.01 else "") + FILTERS
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


def piano_bed(seconds, sr=SR):
    """Yumuşak arpej: Am - F - C - G, tamamen sentetik (telifsiz)."""
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    beat = 0.55
    n = int(seconds * sr) + sr * 3
    buf = np.zeros(n, dtype=np.float32)
    t_note = np.arange(int(sr * 2.6)) / sr
    env = np.exp(-t_note * 2.2) * (1 - np.exp(-t_note * 80))
    pos, i = 0.0, 0
    while pos < seconds + 1:
        ch = chords[(i // 8) % 4]
        note = ch[[0, 1, 2, 3, 2, 1, 2, 3][i % 8]]
        f = 440 * 2 ** ((note - 69) / 12)
        tone = (np.sin(2 * np.pi * f * t_note) + 0.35 * np.sin(4 * np.pi * f * t_note)
                + 0.12 * np.sin(6 * np.pi * f * t_note)) * env
        if i % 8 == 0:
            tone += 0.6 * np.sin(np.pi * f * t_note) * np.exp(-t_note * 1.2)
        s = int(pos * sr)
        e = min(n, s + len(tone))
        buf[s:e] += tone[: e - s] * 0.22
        pos += beat
        i += 1
    buf = buf[: int(seconds * sr)]
    return buf / (np.abs(buf).max() + 1e-6) * 0.9


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
                    f"[1]aecho=0.8:0.7:120|240:0.3|0.2,volume=0.13,afade=t=in:d=1.2,afade=t=out:st={total - 1.6:.2f}:d=1.5[m];"
                    "[0][m]amix=inputs=2:duration=first:normalize=0", "-ar", str(SR), out_path], check=True)
