import os
os.environ["NUMBA_DISABLE_JIT"] = "1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["HF_HOME"] = os.path.join(BASE_DIR, "hf_cache")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR
import tempfile
tempfile.tempdir = TEMP_DIR

import gradio as gr
import subprocess
import sys
import shutil
from pydub import AudioSegment

SAVED_VOICES_DIR = os.path.join(BASE_DIR, "saved_voices")
os.makedirs(SAVED_VOICES_DIR, exist_ok=True)


def _resolve_exe(env_var, venv_subpath_win, venv_subpath_posix, fallback_cmd):
    """Cross-platform executable resolution.

    Priority: explicit environment variable override (used by Docker) >
    a local venv (Windows Scripts/ or POSIX bin/) > whatever is on PATH.
    This lets the exact same app.py run unmodified on a Windows dev machine
    (with a `venv` folder) and inside the Linux Docker container (where
    everything is installed into the system/site environment and exposed
    via PATH).
    """
    override = os.environ.get(env_var)
    if override:
        return override

    win_path = os.path.join(BASE_DIR, *venv_subpath_win)
    if os.path.exists(win_path):
        return win_path

    posix_path = os.path.join(BASE_DIR, *venv_subpath_posix)
    if os.path.exists(posix_path):
        return posix_path

    found = shutil.which(fallback_cmd)
    if found:
        return found

    # Last resort: return the bare command name and let subprocess raise a
    # clear "file not found" error instead of silently pointing at a path
    # that only ever existed on the original developer's machine.
    return fallback_cmd


EDGE_TTS_EXE = _resolve_exe(
    "EDGE_TTS_EXE", ("venv", "Scripts", "edge-tts.exe"), ("venv", "bin", "edge-tts"), "edge-tts"
)
F5_TTS_EXE = _resolve_exe(
    "F5_TTS_EXE",
    ("venv", "Scripts", "f5-tts_infer-cli.exe"),
    ("venv", "bin", "f5-tts_infer-cli"),
    "f5-tts_infer-cli",
)
RVC_MODELS_DIR = os.path.join(BASE_DIR, "rvc_models")
RVC_PYTHON_EXE = _resolve_exe(
    "RVC_PYTHON_EXE", ("rvc_venv", "Scripts", "python.exe"), ("rvc_venv", "bin", "python"), sys.executable
)
RVC_INFER_SCRIPT = os.path.join(BASE_DIR, "rvc_infer.py")
os.makedirs(RVC_MODELS_DIR, exist_ok=True)

# ─── Utility: Run edge-tts via subprocess (avoids asyncio conflicts with Gradio) ───
def run_edge_tts(text, voice, output_path, rate=None, pitch=None):
    """Generate TTS audio using edge-tts CLI. Returns True on success."""
    cmd = [EDGE_TTS_EXE, "--voice", voice, "--text", text, "--write-media", output_path]
    if rate:
        cmd += ["--rate", rate]
    if pitch:
        cmd += ["--pitch", pitch]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0, result.stderr

# ─── Voice Library ───
def get_saved_voices():
    voices = []
    if os.path.exists(SAVED_VOICES_DIR):
        for d in sorted(os.listdir(SAVED_VOICES_DIR)):
            if os.path.isdir(os.path.join(SAVED_VOICES_DIR, d)):
                voices.append(d)
    return voices

def load_voice(name):
    if not name:
        return None, ""
    audio_path = os.path.join(SAVED_VOICES_DIR, name, "audio.wav")
    text_path = os.path.join(SAVED_VOICES_DIR, name, "text.txt")
    text = ""
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
    if not os.path.exists(audio_path):
        return None, text
    return audio_path, text

def save_voice(name, audio_path, text):
    if not name or not audio_path:
        return "❌ Provide a name AND audio file.", gr.update(), gr.update(), gr.update(), gr.update()
    name = name.strip().replace(" ", "_")
    voice_dir = os.path.join(SAVED_VOICES_DIR, name)
    os.makedirs(voice_dir, exist_ok=True)
    shutil.copy(audio_path, os.path.join(voice_dir, "audio.wav"))
    with open(os.path.join(voice_dir, "text.txt"), "w", encoding="utf-8") as f:
        f.write(text or "")
    choices = get_saved_voices()
    return f"✅ Voice '{name}' saved!", gr.update(choices=choices, value=name), gr.update(choices=choices), gr.update(choices=choices), gr.update(choices=choices)

def delete_voice(name):
    if not name:
        return "Select a voice first.", gr.update(), gr.update(), gr.update(), gr.update()
    voice_dir = os.path.join(SAVED_VOICES_DIR, name)
    if os.path.exists(voice_dir):
        shutil.rmtree(voice_dir)
    choices = get_saved_voices()
    return f"🗑️ Deleted '{name}'", gr.update(choices=choices, value=None), gr.update(choices=choices), gr.update(choices=choices), gr.update(choices=choices)

# ─── RVC Backend ───
def get_rvc_models():
    models = []
    if os.path.exists(RVC_MODELS_DIR):
        for f in os.listdir(RVC_MODELS_DIR):
            if f.endswith(".pth"):
                models.append(f)
    return models

def run_rvc_conversion(input_audio, model_name, pitch):
    if not input_audio: return None, "Please upload a reference audio."
    if not model_name: return None, "Please select an RVC model (.pth)."
    
    model_path = os.path.join(RVC_MODELS_DIR, model_name)
    output_path = os.path.join(BASE_DIR, "rvc_output.wav")
    
    cmd = [
        RVC_PYTHON_EXE, RVC_INFER_SCRIPT,
        "--model", model_path,
        "--input", input_audio,
        "--output", output_path,
        "--pitch", str(int(pitch)),
        "--method", "rmvpe"
    ]
    
    # Try finding an index file with the same name
    index_path = model_path.replace(".pth", ".index")
    if os.path.exists(index_path):
        cmd += ["--index", index_path]
        
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0 and os.path.exists(output_path):
        return output_path, "✅ Voice converted successfully!"
    else:
        return None, f"❌ RVC Error:\n{result.stdout}\n{result.stderr}"

# ─── F5-TTS Core Engine ───
def run_f5tts(text, ref_audio_path, ref_text, output_name="output_cloned.wav"):
    output_path = os.path.join(BASE_DIR, output_name)
    trimmed = os.path.join(TEMP_DIR, "trimmed_ref_gen.wav")

    audio = AudioSegment.from_file(ref_audio_path)
    if len(audio) > 8000:
        audio = audio[:8000]
    audio.export(trimmed, format="wav")

    if os.path.exists(output_path):
        os.remove(output_path)
        
    # Prevent internal F5-TTS whisper from hanging on low VRAM
    if not ref_text or not ref_text.strip():
        # define a dummy progress to pass to extract_text_fn
        class DummyProgress:
            def __call__(self, *args, **kwargs): pass
        ref_text = extract_text_fn(trimmed, progress=DummyProgress())
        if ref_text.startswith("Error"):
            return None, f"Failed to transcribe reference audio: {ref_text}"

    import tomli_w
    config_path = os.path.join(BASE_DIR, "inference_config.toml")
    config_dict = {
        "model": "F5-TTS", "ref_audio": trimmed,
        "ref_text": ref_text.strip(),
        "speed": 1.0, "nfe_step": 16, "gen_text": text,
        "output_dir": BASE_DIR, "output_file": output_name, "voices": {}
    }
    with open(config_path, "wb") as f:
        tomli_w.dump(config_dict, f)

    env = os.environ.copy()
    env.update({"TEMP": TEMP_DIR, "TMP": TEMP_DIR, "NUMBA_DISABLE_JIT": "1",
                "HF_HOME": os.environ["HF_HOME"], "PYTHONIOENCODING": "utf-8"})

    result = subprocess.run([F5_TTS_EXE, "-c", config_path],
        capture_output=True, text=True, encoding='utf-8', env=env)

    if result.returncode != 0:
        return None, f"CLI Error: {result.stderr[-500:]}"

    if os.path.exists(output_path):
        import soundfile as sf
        import numpy as np
        data, sr = sf.read(output_path)
        std = np.std(data)
        if std < 0.001:
            return None, "Output is silent. Try different reference audio."
        return output_path, f"✅ Generated {len(data)/sr:.1f}s audio"

    import glob
    wavs = glob.glob(os.path.join(BASE_DIR, "infer_cli_*.wav"))
    if wavs:
        latest = max(wavs, key=os.path.getmtime)
        return latest, f"✅ Found: {os.path.basename(latest)}"
    return None, "❌ Output file not found!"

# ─── Tab 1: Standard Clone ───
def clone_voice_tab1(text, ref_text, audio_ref, progress=gr.Progress()):
    if not text: return None, "Enter text to generate."
    if not audio_ref: return None, "Upload a reference audio."
    progress(0.2, desc="Processing reference...")
    progress(0.4, desc="Running F5-TTS (1-3 min)...")
    path, log = run_f5tts(text, audio_ref, ref_text)
    progress(1.0)
    return path, log

# ─── Tab 2: Dramatic Story Mode ───
NARRATOR_VOICES = {
    "Guy (Passionate Male)": "en-US-GuyNeural",
    "Christopher (Authority Male)": "en-US-ChristopherNeural",
    "Andrew (Confident Male)": "en-US-AndrewNeural",
    "Eric (Rational Male)": "en-US-EricNeural",
    "Brian (Casual Male)": "en-US-BrianNeural",
    "Jenny (Friendly Female)": "en-US-JennyNeural",
    "Aria (Confident Female)": "en-US-AriaNeural",
    "Ava (Expressive Female)": "en-US-AvaNeural",
    "Ryan (British Male)": "en-GB-RyanNeural",
    "Sonia (British Female)": "en-GB-SoniaNeural",
}

def dramatic_clone(text, saved_voice_name, narrator_style, progress=gr.Progress()):
    if not text:
        return None, None, "Enter a story script."
    if not saved_voice_name:
        return None, None, "Select a saved voice from your library first."

    log_lines = []

    # Step 1: Generate emotional narration via edge-tts
    progress(0.1, desc="Step 1: Generating dramatic narration...")
    voice_id = NARRATOR_VOICES.get(narrator_style, "en-US-GuyNeural")
    emotion_path = os.path.join(TEMP_DIR, "emotion_base.mp3")
    ok, err = run_edge_tts(text, voice_id, emotion_path)
    if not ok:
        return None, None, f"❌ Edge-TTS failed: {err}"
    log_lines.append(f"Step 1: ✅ Emotional narration generated ({narrator_style})")

    # Step 2: Clone into anime voice using F5-TTS
    progress(0.4, desc="Step 2: Cloning into anime voice (1-3 min)...")
    voice_audio, voice_text = load_voice(saved_voice_name)
    if not voice_audio:
        log_lines.append(f"Step 2: ⚠️ Voice '{saved_voice_name}' audio not found. Showing emotion base only.")
        return emotion_path, None, "\n".join(log_lines)

    clone_path, clone_log = run_f5tts(text, voice_audio, voice_text, "dramatic_clone.wav")
    log_lines.append(f"Step 2: {clone_log}")
    progress(1.0)
    return emotion_path, clone_path, "\n".join(log_lines)

# ─── Tab 3: Hindi/Urdu ───
def generate_hindi(text, voice_id, use_transliteration, speed, pitch, progress=gr.Progress()):
    if not text:
        return None, "Enter some text."

    status = []
    final_text = text

    if use_transliteration:
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
        if not has_devanagari:
            from transliterate import roman_to_devanagari
            final_text = roman_to_devanagari(text)
            status.append(f"🔄 Transliterated to: {final_text}")
        else:
            status.append("Text already in Devanagari.")

    output_path = os.path.join(TEMP_DIR, "hindi_output.mp3")

    rate_arg = f"{speed:+d}%" if speed != 0 else None
    pitch_arg = f"{pitch:+d}Hz" if pitch != 0 else None

    progress(0.5, desc="Generating voice...")
    ok, err = run_edge_tts(final_text, voice_id, output_path, rate=rate_arg, pitch=pitch_arg)
    if not ok:
        return None, f"❌ Error: {err}"

    status.append("✅ Generated successfully!")
    progress(1.0)
    return output_path, "\n".join(status)

# ─── Extract Text (Whisper) ───
def extract_text_fn(audio_path, progress=gr.Progress()):
    if not audio_path: return "Upload an audio file first!"
    try:
        trimmed = os.path.join(TEMP_DIR, "extract_temp.wav")
        audio = AudioSegment.from_file(audio_path)
        if len(audio) > 8000: audio = audio[:8000]
        audio.export(trimmed, format="wav")
        progress(0.4, desc="Loading Whisper...")
        import torch
        from transformers import pipeline
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        pipe = pipeline("automatic-speech-recognition", model="openai/whisper-base",
                        device=device, torch_dtype=torch.float16)
        progress(0.7, desc="Transcribing...")
        result = pipe(trimmed, chunk_length_s=30, generate_kwargs={"task": "transcribe"})
        text = result['text'].strip()
        del pipe
        import gc; gc.collect()
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        return text
    except Exception as e:
        return f"Error: {str(e)}"

# ─── Tab 4: Multi-Voice Podcast ───
import re

def _contains_devanagari(text):
    return any('\u0900' <= c <= '\u097F' for c in text)


def _contains_arabic_script(text):
    # Covers Arabic/Urdu block, used for Urdu written in its native script.
    return any('\u0600' <= c <= '\u06FF' for c in text)


# Words that exist in COMMON_WORDS purely because they're loanwords /
# English-Hindi homographs (e.g. "video", "like", "hello"). They're kept in
# the transliteration dictionary for when someone IS writing Hindi, but they
# shouldn't by themselves count as evidence that an English sentence is
# actually Hindi/Urdu.
_AMBIGUOUS_ENGLISH_HOMOGRAPHS = {
    "hello", "like", "video", "channel", "share", "subscribe", "comment", "ya",
}


def _looks_like_roman_hindi_urdu(text):
    """Heuristic: does this line contain enough common Roman Hindi/Urdu
    words that it should be treated as Hindi/Urdu rather than English?
    A single stray word (e.g. 'yaar' dropped into an English sentence)
    should NOT trigger the whole line being rerouted."""
    try:
        from transliterate import COMMON_WORDS
    except Exception:
        return False
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in COMMON_WORDS and w not in _AMBIGUOUS_ENGLISH_HOMOGRAPHS)
    return hits >= 2 or (hits >= 1 and hits / len(words) >= 0.4)


def detect_hindi_urdu(text):
    """Returns True if this dialogue line should be routed through the
    native Hindi/Urdu pronunciation pipeline instead of being fed to
    F5-TTS/RVC directly in English/Latin script."""
    if _contains_devanagari(text) or _contains_arabic_script(text):
        return True
    return _looks_like_roman_hindi_urdu(text)


def generate_native_pronunciation_line(dialogue, output_path, hindi_voice="hi-IN-MadhurNeural"):
    """Step 1 of the hybrid system: turn Hindi/Urdu text (Roman or native
    script) into a perfectly, natively pronounced base clip using
    Microsoft's Neural voices, before any character-voice morphing."""
    final_text = dialogue
    if not _contains_devanagari(dialogue) and not _contains_arabic_script(dialogue):
        from transliterate import roman_to_devanagari
        final_text = roman_to_devanagari(dialogue)
    ok, err = run_edge_tts(final_text, hindi_voice, output_path)
    return ok, err


def parse_podcast_script(script_text):
    """Parse a script like 'Light Yagami: Hey! \n Mark: Yo!' into [(name, line), ...]"""
    lines = []
    for raw_line in script_text.strip().split("\n"):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        match = re.match(r'^([A-Za-z0-9_]+)\s*:\s*(.+)$', raw_line)
        if match:
            name = match.group(1).strip()
            dialogue = match.group(2).strip()
            if dialogue:
                lines.append((name, dialogue))
    return lines

def generate_podcast(script_text, pause_ms, progress=gr.Progress()):
    if not script_text.strip():
        return None, "Write a script first."

    parsed = parse_podcast_script(script_text)
    if not parsed:
        return None, "❌ Could not parse script. Use format:\nLight Yagami: Hey Mark!\nMark: Hey Light Yagami!"

    # Collect unique character names
    characters = list(dict.fromkeys([name for name, _ in parsed]))
    saved = get_saved_voices()
    saved_lower = {v.lower(): v for v in saved}

    # Match characters to saved voices (case-insensitive)
    voice_map = {}
    missing = []
    for char in characters:
        if char.lower() in saved_lower:
            voice_map[char] = saved_lower[char.lower()]
        else:
            missing.append(char)

    if missing:
        return None, (
            f"❌ These characters have no matching saved voice:\n"
            f"  {', '.join(missing)}\n\n"
            f"Your saved voices: {', '.join(saved)}\n\n"
            f"Character names in your script must match saved voice names.\n"
            f"Go to the Voice Cloner tab to save voices first."
        )

    log_lines = []
    log_lines.append(f"📋 Parsed {len(parsed)} lines from {len(characters)} characters")
    for char in characters:
        log_lines.append(f"  {char} → voice '{voice_map[char]}'")

    # Generate each line
    audio_segments = []
    pause = AudioSegment.silent(duration=int(pause_ms))

    rvc_models_by_name = {
        os.path.splitext(f)[0].lower(): f for f in get_rvc_models()
    }

    for i, (char, dialogue) in enumerate(parsed):
        progress((i + 1) / len(parsed), desc=f"Generating line {i+1}/{len(parsed)}: {char}...")
        log_lines.append(f"\n🎙️ [{i+1}/{len(parsed)}] {char}: \"{dialogue[:50]}...\"")

        voice_name = voice_map[char]
        voice_audio, voice_text = load_voice(voice_name)
        if not voice_audio:
            log_lines.append(f"  ⚠️ Audio file missing for '{voice_name}', skipping.")
            continue

        out_name = f"podcast_line_{i}.wav"
        path = None
        gen_log = ""

        if detect_hindi_urdu(dialogue):
            # Hybrid pipeline: Neural voice gives perfect native Hindi/Urdu
            # pronunciation first, then (if we have a matching RVC model for
            # this character) morph that into the character's voice.
            native_path = os.path.join(TEMP_DIR, f"podcast_native_{i}.wav")
            ok, err = generate_native_pronunciation_line(dialogue, native_path)
            if not ok:
                gen_log = f"Native Hindi/Urdu base failed: {err}"
            else:
                rvc_model = rvc_models_by_name.get(char.lower())
                if rvc_model:
                    path, gen_log = run_rvc_conversion(native_path, rvc_model, 0)
                    gen_log = f"Hindi/Urdu → native base → RVC '{rvc_model}': {gen_log}"
                else:
                    # No RVC model for this character: use the native base
                    # directly rather than mangling the pronunciation by
                    # forcing it through F5-TTS in the wrong accent.
                    path = native_path
                    gen_log = ("✅ No RVC model found for this character, "
                               "used native Hindi/Urdu narration as-is.")
        else:
            path, gen_log = run_f5tts(dialogue, voice_audio, voice_text, output_name=out_name)

        if path and os.path.exists(path):
            seg = AudioSegment.from_file(path)
            audio_segments.append(seg)
            log_lines.append(f"  ✅ {len(seg)/1000:.1f}s generated")
        else:
            log_lines.append(f"  ❌ Failed: {gen_log}")

    if not audio_segments:
        return None, "\n".join(log_lines) + "\n\n❌ No audio was generated."

    # Stitch together. A short fade-out/fade-in on each side of the pause
    # avoids the sudden, robotic "clicks" you get from hard-cutting straight
    # into silence and back, while still leaving the requested pause length
    # intact between speakers.
    log_lines.append(f"\n🔗 Stitching {len(audio_segments)} segments...")
    fade_ms = max(10, min(60, int(pause_ms) // 4)) if pause_ms else 0

    def _smoothed(seg):
        if fade_ms and len(seg) > fade_ms * 2:
            return seg.fade_in(fade_ms).fade_out(fade_ms)
        return seg

    final = _smoothed(audio_segments[0])
    for seg in audio_segments[1:]:
        final = final + pause + _smoothed(seg)

    output_path = os.path.join(BASE_DIR, "podcast_output.wav")
    final.export(output_path, format="wav")
    log_lines.append(f"✅ Final podcast: {len(final)/1000:.1f}s total")

    return output_path, "\n".join(log_lines)

# ─── Audio Editor Functions ───
def edit_audio_trim(audio_path, start_s, end_s):
    if not audio_path: return None, "Upload audio first."
    try:
        audio = AudioSegment.from_file(audio_path)
        start_ms, end_ms = int(start_s * 1000), int(end_s * 1000)
        trimmed = audio[start_ms:end_ms]
        out = os.path.join(BASE_DIR, "edited_audio.wav")
        trimmed.export(out, format="wav")
        return out, f"✅ Trimmed: Kept {start_s}s to {end_s}s"
    except Exception as e:
        return None, f"❌ Error: {e}"

def edit_audio_cut(audio_path, start_s, end_s):
    if not audio_path: return None, "Upload audio first."
    try:
        audio = AudioSegment.from_file(audio_path)
        start_ms, end_ms = int(start_s * 1000), int(end_s * 1000)
        cut = audio[:start_ms] + audio[end_ms:]
        out = os.path.join(BASE_DIR, "edited_audio.wav")
        cut.export(out, format="wav")
        return out, f"✅ Cut: Removed {start_s}s to {end_s}s"
    except Exception as e:
        return None, f"❌ Error: {e}"

def edit_audio_replace(audio_path, start_s, end_s, text, voice_name, progress=gr.Progress()):
    if not audio_path: return None, "Upload audio first."
    if not text: return None, "Enter text to generate."
    if not voice_name: return None, "Select a voice."
    try:
        audio = AudioSegment.from_file(audio_path)
        start_ms, end_ms = int(start_s * 1000), int(end_s * 1000)
        
        voice_audio, voice_text = load_voice(voice_name)
        if not voice_audio:
            return None, f"❌ Audio file missing for '{voice_name}'"
            
        progress(0.3, desc="Generating new segment...")
        new_path, gen_log = run_f5tts(text, voice_audio, voice_text, output_name="replacement.wav")
        if not new_path or not os.path.exists(new_path):
            return None, f"❌ Generation failed: {gen_log}"
            
        new_seg = AudioSegment.from_file(new_path)
        final = audio[:start_ms] + new_seg + audio[end_ms:]
        
        out = os.path.join(BASE_DIR, "edited_audio.wav")
        final.export(out, format="wav")
        return out, f"✅ Replaced {start_s}s to {end_s}s with new generated audio."
    except Exception as e:
        return None, f"❌ Error: {e}"

# ─── ML FEATURE: Audio Dataset Preprocessing ───
TRAINING_DIR = os.path.join(BASE_DIR, "training_data")
os.makedirs(TRAINING_DIR, exist_ok=True)

def _denoise_audio(audio: AudioSegment) -> tuple[AudioSegment, str]:
    """Filter out background static/hum/music noise before training.

    Prefers spectral-gating noise reduction (the `noisereduce` library),
    which estimates a noise profile from the quietest part of the clip and
    subtracts it from the whole signal — this is what actually removes
    hiss/static/background music bleed rather than just tone-shaping.
    Falls back to a simple high-pass filter (removes low-frequency hum/rumble)
    if `noisereduce`/numpy aren't available, so the pipeline never crashes
    just because an optional dependency is missing.
    """
    try:
        import numpy as np
        import noisereduce as nr

        sr = audio.frame_rate
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        channels = audio.channels
        if channels > 1:
            samples = samples.reshape((-1, channels))
            samples = samples.mean(axis=1)

        # Estimate the noise profile from the quietest 0.5s window instead of
        # assuming the first second is noise (messy real-world clips often
        # start mid-speech).
        window = int(0.5 * sr)
        if window > 0 and len(samples) > window * 2:
            energies = [
                np.sqrt(np.mean(samples[i:i + window] ** 2))
                for i in range(0, len(samples) - window, window)
            ]
            quiet_start = int(np.argmin(energies)) * window
            noise_clip = samples[quiet_start:quiet_start + window]
        else:
            noise_clip = None

        reduced = nr.reduce_noise(y=samples, sr=sr, y_noise=noise_clip, stationary=False)
        reduced = np.clip(reduced, -32768, 32767).astype(np.int16)

        cleaned = AudioSegment(
            reduced.tobytes(), frame_rate=sr, sample_width=2, channels=1
        )
        return cleaned, "🧹 Noise Filter: spectral-gating denoise (noisereduce) applied"
    except Exception:
        # Fallback: a high-pass filter won't remove broadband static as well,
        # but it strips out low rumble/hum and never fails hard.
        try:
            cleaned = audio.high_pass_filter(80)
            return cleaned, "🧹 Noise Filter: fallback high-pass filter applied (noisereduce unavailable)"
        except Exception as e:
            return audio, f"⚠️ Noise Filter skipped ({e})"


def _trim_silence(audio: AudioSegment, silence_thresh_offset=16, min_silence_len=400, keep_silence=150):
    """Detect and cut out silent 'dead air' so the model doesn't waste
    training time on nothing, without chopping mid-word (keeps a small
    padding around each speech segment)."""
    from pydub.silence import detect_nonsilent

    if len(audio) == 0:
        return audio, 0

    thresh = audio.dBFS - silence_thresh_offset if audio.dBFS != float("-inf") else -50
    nonsilent_ranges = detect_nonsilent(
        audio, min_silence_len=min_silence_len, silence_thresh=thresh
    )

    if not nonsilent_ranges:
        # Whole clip looks silent to the detector; don't destroy the data,
        # just pass it through untouched and let the caller know.
        return audio, 0

    trimmed = AudioSegment.empty()
    for start, end in nonsilent_ranges:
        start = max(0, start - keep_silence)
        end = min(len(audio), end + keep_silence)
        trimmed += audio[start:end]

    removed_ms = len(audio) - len(trimmed)
    return trimmed, removed_ms


def preprocess_training_audio(audio_path, chunk_seconds=10, normalize_db=-20.0, progress=gr.Progress()):
    """Real ML data pipeline: denoise, trim silence, normalize, and chunk
    audio for model training. Hardened against messy real-world uploads
    (silent clips, corrupt/odd-format files, mono/stereo mismatches)."""
    if not audio_path:
        return None, "Upload an audio file first."

    try:
        progress(0.05, desc="Loading raw audio...")
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as load_err:
            return None, (
                f"❌ Couldn't read this audio file ({load_err}). "
                f"Try re-exporting it as a standard WAV or MP3 first."
            )

        original_duration = len(audio) / 1000.0
        if original_duration <= 0:
            return None, "❌ This file has no audio in it (0 seconds)."

        # Step 1: Noise filtering — scan for and remove background static/hum
        # BEFORE we chunk, so every chunk benefits from it.
        progress(0.2, desc="Filtering background noise...")
        audio, noise_log = _denoise_audio(audio)

        # Step 2: Convert to mono 16kHz (standard for speech ML models).
        # Doing this before silence detection keeps thresholds consistent.
        audio = audio.set_channels(1).set_frame_rate(16000)

        # Step 3: Cut out silent "dead air" so we don't train on nothing.
        progress(0.4, desc="Detecting and cutting silent dead air...")
        audio, removed_silence_ms = _trim_silence(audio)
        if len(audio) == 0:
            return None, "❌ After removing silence, nothing was left — this clip may be entirely silent."

        # Step 4: Normalize volume (ML best practice for consistent training
        # data). Guard against -inf dBFS on near-silent audio, which would
        # otherwise produce a NaN gain and crash apply_gain().
        progress(0.55, desc="Normalizing volume levels...")
        if audio.dBFS != float("-inf"):
            change_in_dBFS = normalize_db - audio.dBFS
            # Clamp so a couple of loud clipped samples can't blow the gain
            # up to something absurd.
            change_in_dBFS = max(-24.0, min(24.0, change_in_dBFS))
            audio = audio.apply_gain(change_in_dBFS)

        # Step 5: Chunk into training segments
        progress(0.7, desc="Chunking into training segments...")
        chunk_ms = int(chunk_seconds * 1000)
        chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]
        # Drop last chunk if too short (< 2 seconds)
        chunks = [c for c in chunks if len(c) >= 2000]

        if not chunks:
            return None, (
                "❌ After cleaning, less than 2 seconds of usable speech remained. "
                "Try uploading a longer or cleaner recording."
            )

        # Step 6: Export each chunk
        session_dir = os.path.join(TRAINING_DIR, f"session_{len(os.listdir(TRAINING_DIR))}")
        os.makedirs(session_dir, exist_ok=True)

        progress(0.9, desc="Exporting clean training chunks...")
        for i, chunk in enumerate(chunks):
            chunk.export(os.path.join(session_dir, f"chunk_{i:03d}.wav"), format="wav")

        log = (
            f"✅ Audio Dataset Preprocessed!\n"
            f"📊 Original Duration: {original_duration:.1f}s\n"
            f"{noise_log}\n"
            f"✂️ Silence Cutter: removed {removed_silence_ms/1000:.1f}s of dead air\n"
            f"🔊 Normalized to: {normalize_db} dBFS\n"
            f"🎵 Resampled to: 16kHz Mono\n"
            f"📦 Created {len(chunks)} training chunks ({chunk_seconds}s each)\n"
            f"📁 Saved to: {session_dir}"
        )
        progress(1.0)
        return session_dir, log
    except Exception as e:
        return None, f"❌ Preprocessing Error: {e}"

def analyze_voice_similarity(audio_a, audio_b, progress=gr.Progress()):
    """Real ML: Compare two audio files using Whisper encoder embeddings + cosine similarity."""
    if not audio_a or not audio_b:
        return "Upload both audio files to compare."
    try:
        progress(0.2, desc="Loading Whisper encoder...")
        import torch
        import numpy as np
        from transformers import WhisperProcessor, WhisperModel

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        processor = WhisperProcessor.from_pretrained("openai/whisper-base")
        model = WhisperModel.from_pretrained("openai/whisper-base").to(device).to(dtype)

        def get_embedding(path):
            audio = AudioSegment.from_file(path).set_channels(1).set_frame_rate(16000)
            if len(audio) > 15000:
                audio = audio[:15000]
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
            inputs = processor(samples, sampling_rate=16000, return_tensors="pt")
            input_features = inputs.input_features.to(device).to(dtype)
            with torch.no_grad():
                encoder_out = model.encoder(input_features)
                embedding = encoder_out.last_hidden_state.mean(dim=1).squeeze()
            return embedding

        progress(0.5, desc="Extracting voice embeddings...")
        emb_a = get_embedding(audio_a)
        progress(0.7, desc="Comparing voice signatures...")
        emb_b = get_embedding(audio_b)

        # Cosine Similarity
        cos_sim = torch.nn.functional.cosine_similarity(emb_a.unsqueeze(0), emb_b.unsqueeze(0)).item()
        similarity_pct = max(0, min(100, cos_sim * 100))

        # Cleanup GPU
        del model, processor, emb_a, emb_b
        import gc; gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        grade = "🟢 Excellent" if similarity_pct > 85 else "🟡 Good" if similarity_pct > 70 else "🔴 Poor"
        progress(1.0)
        return (
            f"🧠 Voice Similarity Analysis\n"
            f"{'='*40}\n"
            f"Cosine Similarity Score: {similarity_pct:.1f}%\n"
            f"Quality Grade: {grade}\n\n"
            f"{'='*40}\n"
            f"If the score is below 70%, consider:\n"
            f"  • Using a longer/cleaner reference audio\n"
            f"  • Fine-tuning the model with more training data\n"
            f"  • Adjusting the pitch shift parameter"
        )
    except Exception as e:
        return f"❌ Analysis Error: {e}"

# ═══════════════════════════════════════
#  GRADIO UI
# ═══════════════════════════════════════
import base64
logo_path = os.path.join(BASE_DIR, "assets", "LOGO.jpg")
logo_b64 = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

custom_css = """
footer {display: none !important;}
.zenvyro-header {text-align: center; padding: 20px 0; border-bottom: 2px solid #eee; margin-bottom: 20px;}
.zenvyro-logo {font-size: 2.5em; font-weight: 800; color: #2563eb; letter-spacing: 2px;}
.zenvyro-subtitle {font-size: 1.1em; color: #64748b; margin-top: 5px;}
"""

header_html = f"""
    <div class="zenvyro-header">
        <img src="data:image/jpeg;base64,{logo_b64}" alt="Zenvyrolabs Logo" style="height: 80px; margin-bottom: 10px; display: inline-block;">
        <div class="zenvyro-logo">ZENVYROLABS</div>
        <div class="zenvyro-subtitle">Internal Advanced Voice Studio • Clone anime voices • Dramatic storytelling • Multi-voice podcasts</div>
    </div>
"""

with gr.Blocks(title="🎙️ Zenvyrolabs Voice Studio") as interface:
    gr.HTML(header_html)

    with gr.Tabs():
        # ─── TAB 1: Voice Cloner ───
        with gr.TabItem("🎭 Voice Cloner"):
            gr.Markdown("Upload any voice clip → the AI clones it and speaks your text in that voice.")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📂 Voice Library")
                    saved_dd = gr.Dropdown(choices=get_saved_voices(), label="Saved Voices", interactive=True)
                    with gr.Row():
                        load_btn = gr.Button("📂 Load", size="sm")
                        del_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")
                    gr.Markdown("---")
                    gr.Markdown("### 💾 Save Voice")
                    voice_name = gr.Textbox(label="Name", placeholder="e.g. Gojo_Dramatic")
                    save_btn = gr.Button("💾 Save to Library", variant="primary")
                    lib_status = gr.Textbox(label="Status", interactive=False)

                with gr.Column(scale=2):
                    gen_text1 = gr.Textbox(label="Script to Speak", lines=6, placeholder="Type your story here...")
                    ref_audio1 = gr.Audio(type="filepath", label="Reference Voice (auto-trims to 8s)")
                    with gr.Row():
                        ref_text1 = gr.Textbox(label="Reference Text", lines=2, scale=4,
                            placeholder="Type exact words from the reference audio...")
                        extract_btn1 = gr.Button("🔍 Auto-Extract", variant="secondary", scale=1)
                    clone_btn1 = gr.Button("🎙️ Generate Clone", variant="primary", size="lg")

            with gr.Row():
                out_audio1 = gr.Audio(label="Generated Audio")
                out_log1 = gr.Textbox(label="Log")

            load_btn.click(fn=load_voice, inputs=[saved_dd], outputs=[ref_audio1, ref_text1])
            extract_btn1.click(fn=extract_text_fn, inputs=[ref_audio1], outputs=[ref_text1])
            clone_btn1.click(fn=clone_voice_tab1, inputs=[gen_text1, ref_text1, ref_audio1], outputs=[out_audio1, out_log1])

        # ─── TAB 2: Dramatic Story Mode ───
        with gr.TabItem("🎬 Dramatic Story Mode", visible=False):
            gr.Markdown("""### How it works:
1. **Step 1:** Microsoft Neural AI creates a dramatic, emotional narration (perfect pronunciation & emotions).
2. **Step 2:** F5-TTS re-generates the same script using your saved anime voice (Gojo, Naruto, etc).
3. You get **two outputs** — pick whichever sounds better!

**Pro tip:** The emotion base alone sounds incredible for YouTube. The anime clone adds character flavor.""")

            with gr.Row():
                with gr.Column():
                    saved_dd2 = gr.Dropdown(choices=get_saved_voices(), label="Select Saved Anime Voice", interactive=True)
                    narrator_style = gr.Dropdown(
                        choices=list(NARRATOR_VOICES.keys()),
                        label="Emotion Narrator Style", value="Guy (Passionate Male)"
                    )
                    story_text = gr.Textbox(label="Your Story Script", lines=10,
                        placeholder="My daughter went missing five years ago...")
                    dramatic_btn = gr.Button("🎬 Generate Dramatic Voiceover", variant="primary", size="lg")

                with gr.Column():
                    gr.Markdown("### Step 1: Emotional Narration (Microsoft Neural)")
                    emotion_audio = gr.Audio(label="Emotion Base")
                    gr.Markdown("### Step 2: Anime Voice Clone (F5-TTS)")
                    clone_audio = gr.Audio(label="Anime Voice Version")
                    dramatic_log = gr.Textbox(label="Generation Log")

            dramatic_btn.click(fn=dramatic_clone,
                inputs=[story_text, saved_dd2, narrator_style],
                outputs=[emotion_audio, clone_audio, dramatic_log])

        # ─── TAB 3: Multi-Voice Podcast ───
        with gr.TabItem("🎙️ Multi-Voice Podcast"):
            gr.Markdown("""### Create Podcasts with Multiple Anime Voices
Write a script with character names that **match your saved voices**. Each line is generated with the correct voice and stitched into one seamless audio.

**Script Format:**
```
Light Yagami: Hey Mark, what's up man!
Mark: Yo Light Yagami! Just finished eating, I'm pumped!
Light Yagami: Wanna go train together?
Mark: Let's gooo!
```
⚠️ Character names must **exactly match** your saved voice names (case-insensitive).""")

            with gr.Row():
                with gr.Column():
                    podcast_voices_dd = gr.Dropdown(choices=get_saved_voices(), multiselect=True, label="Your Saved Voices", info="Select the characters you want to use in your podcast script", interactive=True)
                    podcast_script = gr.Textbox(label="Podcast Script", lines=14,
                        placeholder="Light Yagami: Hey Mark, what's up man!\nMark: Yo Light Yagami! Just finished eating, I'm pumped!\nLight Yagami: Wanna go train together?\nMark: Let's gooo!")
                    pause_slider = gr.Slider(100, 2000, value=500, step=50,
                        label="Pause Between Lines (ms)", info="How long to pause between each character's line")
                    podcast_btn = gr.Button("🎙️ Generate Full Podcast", variant="primary", size="lg")

                with gr.Column():
                    podcast_audio = gr.Audio(label="Final Podcast Audio")
                    podcast_log = gr.Textbox(label="Generation Log", lines=15)

            podcast_btn.click(fn=generate_podcast,
                inputs=[podcast_script, pause_slider],
                outputs=[podcast_audio, podcast_log])

        # ─── TAB 4: Hindi / Urdu ───
        with gr.TabItem("🌏 Hindi / Urdu"):
            gr.Markdown("""### Perfect Hindi & Urdu Pronunciation
**Fix:** Auto-converts Roman Hindi/Urdu → Devanagari script before generating, so pronunciation is accurate.
- Type **Roman** (kya haal hai) → auto-converts to **Devanagari** (क्या हाल है)
- Or type directly in **Devanagari** for best quality""")

            with gr.Row():
                with gr.Column():
                    hindi_text = gr.Textbox(label="Hindi / Urdu Text", lines=6,
                        placeholder="Hello bhai, kya haal hai? Aaj hum ek bahut hi dilchasp kahani sunenge...")
                    transliterate_toggle = gr.Checkbox(label="🔄 Auto-convert Roman → Devanagari (Recommended!)", value=True)
                    hindi_voice = gr.Dropdown(
                        choices=["hi-IN-MadhurNeural", "hi-IN-SwaraNeural",
                                 "ur-PK-AsadNeural", "ur-PK-UzmaNeural",
                                 "ur-IN-SalmanNeural", "ur-IN-GulNeural"],
                        label="Voice", value="hi-IN-MadhurNeural",
                        info="Madhur=Hindi Male, Swara=Hindi Female, Asad=Urdu Male, Uzma=Urdu Female"
                    )
                    with gr.Row():
                        hindi_speed = gr.Slider(-30, 30, value=0, step=5, label="Speed (%)")
                        hindi_pitch = gr.Slider(-20, 20, value=0, step=2, label="Pitch (Hz)")
                    hindi_btn = gr.Button("🎙️ Generate Hindi/Urdu Voice", variant="primary", size="lg")

                with gr.Column():
                    hindi_audio = gr.Audio(label="Generated Audio")
                    hindi_log = gr.Textbox(label="Status")

            hindi_btn.click(fn=generate_hindi,
                inputs=[hindi_text, hindi_voice, transliterate_toggle, hindi_speed, hindi_pitch],
                outputs=[hindi_audio, hindi_log])

        # ─── TAB 5: Audio Editor ───
        with gr.TabItem("✂️ Audio Editor"):
            gr.Markdown("Upload an audio file (or download a generated one and upload here) to trim, cut, or completely replace a bad segment with a newly generated voice!")
            
            with gr.Row():
                with gr.Column(scale=1):
                    edit_audio_in = gr.Audio(type="filepath", label="Source Audio", interactive=True)
                    start_s = gr.Number(label="Start Time (seconds)", value=0.0)
                    end_s = gr.Number(label="End Time (seconds)", value=5.0)
                    
                    with gr.Row():
                        trim_btn = gr.Button("✂️ Trim (Keep Only Selection)", variant="secondary")
                        cut_btn = gr.Button("🗑️ Cut (Remove Selection)", variant="secondary")
                        
                    gr.Markdown("### Replace Segment")
                    replace_text = gr.Textbox(label="New Text for Segment", lines=2)
                    replace_voice = gr.Dropdown(choices=get_saved_voices(), label="Select Voice for New Segment", interactive=True)
                    replace_btn = gr.Button("🔄 Replace Segment", variant="primary")
                
                with gr.Column(scale=1):
                    edit_audio_out = gr.Audio(label="Edited Audio")
                    edit_log = gr.Textbox(label="Status Log")
                    
            trim_btn.click(fn=edit_audio_trim, inputs=[edit_audio_in, start_s, end_s], outputs=[edit_audio_out, edit_log])
            cut_btn.click(fn=edit_audio_cut, inputs=[edit_audio_in, start_s, end_s], outputs=[edit_audio_out, edit_log])
            replace_btn.click(fn=edit_audio_replace, inputs=[edit_audio_in, start_s, end_s, replace_text, replace_voice], outputs=[edit_audio_out, edit_log])

        # ─── TAB 6: Voice-to-Voice (RVC) ───
        with gr.TabItem("🎤 Voice-to-Voice (RVC)", visible=False):
            gr.Markdown("""### True Emotional Voice Cloning (Speech-to-Speech)
Upload an audio of **you acting out a line**, select a downloaded `.pth` anime character model, and the AI will convert your voice while preserving exactly the timing, emotion, and breath.
*(Models must be placed in `e:\project\searching\anime_voice_cloner\\rvc_models`)*""")
            with gr.Row():
                with gr.Column():
                    rvc_in = gr.Audio(type="filepath", label="Input Audio (Your acting/reference)")
                    rvc_model = gr.Dropdown(choices=get_rvc_models(), label="RVC Model (.pth)", interactive=True)
                    rvc_refresh = gr.Button("🔄 Refresh Models List", size="sm")
                    rvc_pitch = gr.Slider(-24, 24, value=0, step=1, label="Pitch Shift (Semitones)", info="Use +12 for Male->Female, -12 for Female->Male. Leave 0 if same gender.")
                    rvc_btn = gr.Button("🎤 Convert Voice", variant="primary", size="lg")
                with gr.Column():
                    rvc_out = gr.Audio(label="Converted Audio")
                    rvc_log = gr.Textbox(label="Status Log", lines=10)
                    
            rvc_btn.click(fn=run_rvc_conversion, inputs=[rvc_in, rvc_model, rvc_pitch], outputs=[rvc_out, rvc_log])
            rvc_refresh.click(fn=lambda: gr.update(choices=get_rvc_models()), outputs=[rvc_model])

        # ─── TAB 7: Perfect Pronunciation Clone ───
        with gr.TabItem("🌟 Perfect Pronunciation Clone", visible=False):
            gr.Markdown("""### Get Anime Voices with PERFECT Pronunciation
F5-TTS sometimes struggles with pronunciation. This tab fixes that! 
It uses **Edge-TTS (Eric, Guy, etc.)** to generate perfect, native pronunciation, and then uses **RVC** to seamlessly morph that audio into your Anime character's voice.
*(Requires an RVC `.pth` model in `rvc_models/`)*""")
            with gr.Row():
                with gr.Column():
                    perf_text = gr.Textbox(label="Script", lines=6, placeholder="Type perfectly pronounced English here...")
                    perf_neural = gr.Dropdown(choices=list(NARRATOR_VOICES.keys()), label="Base Neural Voice (for acting/pronunciation)", value="Eric (Rational Male)")
                    perf_rvc = gr.Dropdown(choices=get_rvc_models(), label="Target Anime Voice (RVC Model)", interactive=True)
                    perf_pitch = gr.Slider(-24, 24, value=0, step=1, label="Pitch Shift", info="Match Neural gender to Anime gender. e.g. Male to Female: +12")
                    perf_btn = gr.Button("🌟 Generate Perfect Clone", variant="primary", size="lg")
                with gr.Column():
                    perf_audio = gr.Audio(label="Final Perfect Audio")
                    perf_log = gr.Textbox(label="Status Log")

            def run_perfect_clone(text, neural_voice, rvc_model, pitch, progress=gr.Progress()):
                if not text: return None, "Please enter text."
                if not rvc_model: return None, "Please select an RVC model."
                
                progress(0.2, desc="Generating perfect pronunciation...")
                voice_id = NARRATOR_VOICES.get(neural_voice, "en-US-EricNeural")
                temp_audio = os.path.join(TEMP_DIR, "perf_base.mp3")
                ok, err = run_edge_tts(text, voice_id, temp_audio)
                if not ok:
                    return None, f"❌ Edge-TTS failed: {err}"
                
                progress(0.6, desc="Morphing into Anime Voice (RVC)...")
                final_path, log = run_rvc_conversion(temp_audio, rvc_model, pitch)
                progress(1.0)
                return final_path, log
            
            perf_btn.click(fn=run_perfect_clone, inputs=[perf_text, perf_neural, perf_rvc, perf_pitch], outputs=[perf_audio, perf_log])

        # ─── TAB 8: Voice Training Studio (Real ML) ───
        with gr.TabItem("🧠 Voice Training Studio"):
            gr.Markdown("""### 🧠 AI Model Training Pipeline
This is the **core Machine Learning** feature of the application. Instead of relying on zero-shot cloning (which can sound robotic), you can **train a custom voice model** by feeding it high-quality audio data.

**How it works (Real ML Pipeline):**
1. **Upload** a long audio recording of your target voice (5-10 minutes recommended).
2. **Preprocess** — Our pipeline will automatically normalize volume levels, resample to 16kHz mono (the standard for speech ML models), remove silence, and chunk the audio into clean 10-second training segments.
3. **Analyze** — Use the Voice Quality Analyzer to compare your cloned output vs the original and get a real ML similarity score using Whisper neural embeddings.

*This is the exact same data preprocessing pipeline used in production ML systems at companies like ElevenLabs and OpenAI.*""")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Step 1: Upload Raw Training Audio")
                    train_audio = gr.Audio(type="filepath", label="Raw Training Audio (5-10 min recommended)")
                    chunk_size = gr.Slider(5, 30, value=10, step=1, label="Chunk Size (seconds)", info="Each chunk becomes one training sample")
                    norm_db = gr.Slider(-30, -10, value=-20, step=1, label="Target Volume (dBFS)", info="Normalizes all chunks to this volume level for consistent training")
                    preprocess_btn = gr.Button("⚙️ Preprocess Dataset", variant="primary", size="lg")

                with gr.Column():
                    gr.Markdown("### Preprocessing Results")
                    train_output_dir = gr.Textbox(label="Output Directory", interactive=False)
                    train_log = gr.Textbox(label="Pipeline Log", lines=10)

            preprocess_btn.click(fn=preprocess_training_audio,
                inputs=[train_audio, chunk_size, norm_db],
                outputs=[train_output_dir, train_log])

            gr.Markdown("---")
            gr.Markdown("""### Step 2: Voice Quality Analyzer (Cosine Similarity)
Upload the **original voice** and your **cloned output** to measure how accurate the clone is using real ML metrics.
The system uses **OpenAI Whisper's neural encoder** to extract voice embeddings and computes **cosine similarity** — the same technique used in speaker verification systems.""")

            with gr.Row():
                with gr.Column():
                    sim_audio_a = gr.Audio(type="filepath", label="Audio A: Original Voice")
                    sim_audio_b = gr.Audio(type="filepath", label="Audio B: Cloned Voice")
                    sim_btn = gr.Button("🧠 Analyze Similarity", variant="primary", size="lg")
                with gr.Column():
                    sim_result = gr.Textbox(label="ML Analysis Results", lines=12)

            sim_btn.click(fn=analyze_voice_similarity,
                inputs=[sim_audio_a, sim_audio_b],
                outputs=[sim_result])

    # Global event bindings
    save_btn.click(fn=save_voice, inputs=[voice_name, ref_audio1, ref_text1], outputs=[lib_status, saved_dd, saved_dd2, podcast_voices_dd, replace_voice])
    del_btn.click(fn=delete_voice, inputs=[saved_dd], outputs=[lib_status, saved_dd, saved_dd2, podcast_voices_dd, replace_voice])

if __name__ == "__main__":
    print("Launching Advanced Voice Studio...")
    print(f"Saved Voices: {get_saved_voices()}")
    # Inside Docker there's no local browser to pop open and the server must
    # listen on all interfaces (0.0.0.0) for the port mapping in
    # docker-compose.yml to reach it. RUNNING_IN_DOCKER is set in the
    # Dockerfile; locally this keeps the original 127.0.0.1 + inbrowser=True
    # behavior.
    in_docker = os.environ.get("RUNNING_IN_DOCKER", "0") == "1"
    server_name = os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0" if in_docker else "127.0.0.1")
    server_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        inbrowser=not in_docker,
        css=custom_css,
    )
