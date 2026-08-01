# Engineering Handbook — Implementation Notes

## Task 1: Dockerization & Deployment Architecture
- Added `Dockerfile` (Python 3.11-slim + ffmpeg + build-essential, all deps
  from `requirements.txt`).
- Added `docker-compose.yml` with bind-mounted volumes for `saved_voices/`,
  `rvc_models/`, and `training_data/` (survive container recreation), plus a
  named volume `hf_cache` for downloaded model weights so you don't
  re-download ~2.4GB every rebuild. Commented-out GPU passthrough block
  included for machines with the NVIDIA Container Toolkit.
- Added `.dockerignore` to keep the build context small.
- `app.py` previously hardcoded Windows-only paths
  (`venv\Scripts\edge-tts.exe`, etc.) for every subprocess call, which would
  fail immediately inside a Linux container. Replaced with `_resolve_exe()`,
  which checks an env var override → local venv (Windows or POSIX) → `PATH`,
  so the same file runs unmodified on Windows or in Docker.
- `interface.launch()` now binds to `0.0.0.0` inside the container (via
  `RUNNING_IN_DOCKER=1`) so the `7860:7860` port mapping actually works, while
  keeping the original `127.0.0.1` + auto-open-browser behavior for local use.

**Run it:**
```bash
docker compose up --build
# then open http://localhost:7860
```

## Task 2: Podcast Text & Pronunciation
- The regex-based script parser (`^([A-Za-z0-9_]+)\s*:\s*(.+)$`) already
  tolerated arbitrary spacing around the colon and skipped unparseable lines
  instead of crashing; verified this with `NAME:`, `NAME :`, `NAME : `, and
  multi-space variants — all parse correctly, and lines with no colon are
  silently dropped rather than raising.
- Unknown character names already produced a polite warning
  (`generate_podcast` lists the missing names + available saved voices)
  instead of crashing.
- **New:** added `detect_hindi_urdu()` / `generate_native_pronunciation_line()`
  and wired them into `generate_podcast()`. Any podcast line containing
  Devanagari, Arabic/Urdu script, or enough common Roman-Hindi/Urdu words is
  now routed through the hybrid pipeline described in the README: Microsoft
  Neural voice generates a perfectly-pronounced native base clip, which is
  then morphed through an RVC model matching the character's name (if one
  exists in `rvc_models/`) instead of being fed directly into F5-TTS in the
  wrong accent.
- **New:** line-to-line transitions in the stitched podcast now get a short
  fade-in/fade-out (scaled to the configured pause length) instead of a hard
  cut into silence, removing the "sudden robotic silence" effect.

## Task 3: AI Audio Training Pipeline
- **Noise Filter:** `_denoise_audio()` uses spectral-gating noise reduction
  (`noisereduce`), estimating the noise profile from the quietest window of
  the clip rather than assuming the first second is clean. Falls back to a
  high-pass filter if `noisereduce`/numpy aren't available, so a missing
  optional dependency never crashes the pipeline.
- **Silence Cutter:** `_trim_silence()` uses `pydub.silence.detect_nonsilent`
  to find and remove dead air, keeping a small padding around each speech
  segment so words aren't chopped.
- **Hardening against messy audio:**
  - Corrupt/unreadable files return a clear error instead of an unhandled
    exception.
  - Zero-duration files are rejected early.
  - Fully-silent clips (`dBFS == -inf`) no longer crash `apply_gain()` with a
    NaN gain — normalization is skipped safely.
  - Gain is clamped to ±24 dB so a couple of clipped/loud samples can't send
    the whole clip to an absurd volume.
  - If cleaning leaves less than 2 seconds of audio, the pipeline reports
    this clearly instead of silently producing zero training chunks.

## Task 4
Not something I can do on your behalf — it needs you to actually pick 2
characters, download/train their audio, and record yourself using the app.
Happy to help debug anything that comes up while you do that, though.
