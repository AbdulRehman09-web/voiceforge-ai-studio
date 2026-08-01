# 🎙️ VoiceForge AI Studio

<div align="center">

### 🧠 AI Voice Cloning • 🎭 Character Voices • 🎬 Storytelling • 🎙️ Multi-Voice Podcasts • 🌏 Hindi/Urdu • ✂️ Audio Editing • 🧪 Voice Analysis

**A local, Gradio-based AI voice studio that combines F5-TTS, Microsoft Edge-TTS, Whisper, RVC support, audio preprocessing, and voice-quality analysis into one application.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](#-requirements)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange?logo=gradio&logoColor=white)](#-application-features)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](#-requirements)
[![F5--TTS](https://img.shields.io/badge/TTS-F5--TTS-purple)](#-voice-cloning)
[![Whisper](https://img.shields.io/badge/ASR-Whisper-412991)](#-voice-quality-analysis)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)](#-docker-installation)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)](#-requirements)

</div>

---

## 📌 Overview

**VoiceForge AI Studio** is an all-in-one local AI audio application for experimenting with voice cloning, character-style voices, multilingual speech generation, multi-speaker podcasts, audio editing, dataset preparation, and voice similarity analysis.

The project provides a browser-based **Gradio interface** instead of requiring users to operate several command-line AI tools independently.

The application currently integrates:

- 🎭 **F5-TTS** for zero-shot text-to-speech voice cloning
- 🗣️ **Microsoft Edge-TTS** for high-quality neural narration and native Hindi/Urdu pronunciation
- 🧠 **Whisper** for reference-audio transcription and neural audio embeddings
- 🎤 **RVC integration** for optional speech-to-speech voice conversion
- 🧹 **Noise reduction** and silence trimming for training-data preparation
- 📦 **Automatic audio chunking** for ML dataset preparation
- 📊 **Cosine similarity analysis** using Whisper encoder embeddings
- 🎙️ **Multi-character podcast generation**
- 🌏 **Roman Hindi/Urdu → Devanagari transliteration**
- ✂️ **Audio trimming, cutting, and segment replacement**
- 🐳 **Docker deployment** with persistent model/data volumes

> **Important:** This repository provides an AI audio experimentation and production-style engineering environment. Only clone or transform voices when you have the necessary rights, consent, or authorization to use the source voice and model.

---

## ✨ Why This Project?

Traditional AI voice workflows often require separate tools for:

1. Preparing reference audio
2. Transcribing reference speech
3. Running a voice-cloning model
4. Generating narration
5. Converting voices
6. Creating multi-speaker content
7. Cleaning audio
8. Evaluating output quality

VoiceForge AI Studio brings these workflows together behind a single interface.

### 🎯 Project Goal

> **Turn a collection of AI speech and audio-processing tools into one practical local voice-production studio.**

---

# 🚀 Application Features

## 🎭 1. Voice Cloner

The main voice-cloning workflow uses **F5-TTS**.

### Workflow

```text
Reference Voice
      │
      ▼
Reference Audio Preparation
      │
      ▼
Reference Text
      │
      ▼
F5-TTS
      │
      ▼
Generated Speech
```

### What you can do

- Upload a reference voice
- Enter the exact reference transcript
- Automatically transcribe the reference with Whisper
- Enter new text
- Generate speech using the reference speaker characteristics
- Save the reference voice to the local Voice Library
- Reload saved voices later
- Delete saved voices

### Recommended reference audio

For better results:

- Use clean speech
- Avoid music and heavy background noise
- Prefer a single speaker
- Avoid overlapping speakers
- Use clear pronunciation
- Keep the reference reasonably short and focused

The application automatically limits the reference clip used by F5-TTS to approximately **8 seconds**.

---

# 🎬 2. Dramatic Story Mode

Dramatic Story Mode uses a two-stage workflow.

```text
Your Story
    │
    ├──────────────► Microsoft Neural Voice
    │                     │
    │                     ▼
    │              Emotional Narration
    │
    └──────────────► F5-TTS + Saved Voice
                          │
                          ▼
                    Character Version
```

### Output

You receive two versions:

1. 🎙️ Emotional neural narration
2. 🎭 Saved-character voice version

This makes it easy to compare natural narration against character-style voice generation.

---

# 🎙️ 3. Multi-Voice Podcast

Create a complete podcast using multiple saved voices.

### Example script

```text
NARUTO: Hey Luffy, what's going on?

LUFFY: Hey Naruto! I just had the best meal ever!

NARUTO: Sounds great. Want to go training?

LUFFY: Absolutely! Let's go!
```

Each character name must correspond to a saved voice.

### Processing pipeline

```text
Podcast Script
      │
      ▼
Script Parser
      │
      ▼
Character → Saved Voice Mapping
      │
      ▼
Generate Each Dialogue Line
      │
      ▼
Add Line Transitions / Pauses
      │
      ▼
Combine Audio Segments
      │
      ▼
Final Podcast
```

### Character matching

Matching is case-insensitive.

For example:

```text
NARUTO
Naruto
naruto
```

can all map to the same saved voice.

### Hindi/Urdu support

Podcast lines containing:

- Devanagari
- Arabic/Urdu script
- recognizable Roman Hindi/Urdu patterns

are routed through a native-pronunciation pipeline instead of being blindly sent to an English-oriented generation path.

---

# 🌏 4. Hindi / Urdu Voice Generation

The Hindi/Urdu module is designed to improve pronunciation when users write South Asian languages in Roman script.

### Example

Input:

```text
Hello bhai, kya haal hai?
```

The application can convert the Roman text into Devanagari before speech generation.

Example:

```text
Hello bhai, kya haal hai?
            ↓
हेलो भाई, क्या हाल है?
```

### Available neural voices

The current application includes options such as:

| Voice | Language | Style |
|---|---|---|
| `hi-IN-MadhurNeural` | Hindi | Male |
| `hi-IN-SwaraNeural` | Hindi | Female |
| `ur-PK-AsadNeural` | Urdu | Male |
| `ur-PK-UzmaNeural` | Urdu | Female |
| `ur-IN-SalmanNeural` | Urdu | Male |
| `ur-IN-GulNeural` | Urdu | Female |

### Controls

- 🔄 Roman → Devanagari conversion
- 🎚️ Speech speed
- 🎚️ Pitch adjustment
- 🎙️ Hindi/Urdu voice selection

---

# ✂️ 5. Audio Editor

The built-in audio editor supports basic non-destructive-style editing workflows.

### Available operations

#### Trim

Keep only the selected region.

```text
Original Audio
████████████████████

        SELECT
        ████████

Output
        ████████
```

#### Cut

Remove the selected region.

```text
Original
███████ [REMOVE] ███████

Output
███████             ███████
```

#### Replace Segment

A selected part of an audio file can be replaced with newly generated speech using a saved voice.

### Example

```text
Original:
"Welcome to the podcast. Today we discuss AI."

Selected:
"the podcast"

Replacement:
"our AI studio"

Final:
"Welcome to our AI studio. Today we discuss AI."
```

---

# 🎤 6. Voice-to-Voice / RVC Support

The project contains an optional RVC inference integration.

RVC can be used for speech-to-speech conversion:

```text
Your Acting / Source Audio
          │
          ▼
       RVC Model
          │
          ▼
 Converted Voice
```

### Supported controls

- `.pth` RVC model
- Optional `.index` file
- Pitch shift
- RMVPE F0 method

### Model directory

Place RVC models in:

```text
rvc_models/
```

Example:

```text
rvc_models/
├── Character.pth
└── Character.index
```

The application automatically searches for a matching `.index` file when available.

> **Note:** RVC support is optional in the current repository. The RVC Python package is not installed by the default `requirements.txt` because of compatibility concerns with the F5-TTS environment. See the RVC section below before enabling it.

---

# 🌟 7. Perfect Pronunciation Clone

This optional workflow combines:

```text
Text
 │
 ▼
Microsoft Neural TTS
 │
 │  Natural pronunciation
 ▼
Base Speech
 │
 ▼
RVC
 │
 ▼
Target Character Voice
```

This is useful when pronunciation quality from a direct voice-cloning workflow is not sufficient.

The base neural voice handles pronunciation while RVC performs the voice transformation.

---

# 🧠 8. Voice Training Studio

The Voice Training Studio is a **real audio/ML preprocessing and evaluation pipeline**.

> **Important:** The current implementation prepares training data and evaluates voice similarity. It does **not** automatically fine-tune an F5-TTS model from the generated chunks.

### Pipeline

```text
Raw Audio
   │
   ▼
Noise Reduction
   │
   ▼
Convert to Mono
   │
   ▼
Resample to 16 kHz
   │
   ▼
Silence Detection
   │
   ▼
Silence Removal
   │
   ▼
Volume Normalization
   │
   ▼
Audio Chunking
   │
   ▼
Training Dataset
```

### Audio cleaning

The preprocessing pipeline includes:

- Spectral-gating noise reduction using `noisereduce`
- High-pass fallback when needed
- Silence detection
- Silence removal
- Small silence padding around speech
- Mono conversion
- 16 kHz resampling
- Volume normalization
- Gain clamping
- Minimum usable-duration checks
- Clean WAV export

### Default settings

| Setting | Default |
|---|---:|
| Chunk size | 10 seconds |
| Target volume | -20 dBFS |
| Sample rate | 16 kHz |
| Channels | Mono |
| Minimum final chunk | 2 seconds |

### Output

Processed datasets are stored under:

```text
training_data/
```

with session folders such as:

```text
training_data/
└── session_0/
    ├── chunk_000.wav
    ├── chunk_001.wav
    ├── chunk_002.wav
    └── ...
```

---

# 📊 9. Voice Quality Analyzer

The Voice Quality Analyzer compares two audio files using embeddings from the **OpenAI Whisper encoder**.

### Pipeline

```text
Audio A ──► Whisper Encoder ──► Embedding A
                                      │
                                      ▼
                                Cosine Similarity
                                      ▲
                                      │
Audio B ──► Whisper Encoder ──► Embedding B
```

### Metric

The system calculates:

```text
Cosine Similarity
```

and converts the result into a percentage-style score.

### Current grading

| Score | Grade |
|---:|---|
| > 85% | 🟢 Excellent |
| > 70% | 🟡 Good |
| ≤ 70% | 🔴 Poor |

### Important interpretation note

This score should be treated as an **engineering similarity indicator**, not as a certified speaker-verification metric.

Whisper is primarily a speech recognition model. Its embeddings can be useful for experimental similarity analysis, but the score should not be interpreted as proof of speaker identity or biometric equivalence.

---

# 🧠 10. Whisper Reference Transcription

If you do not know the exact text spoken in the reference audio, the application can use:

```text
openai/whisper-base
```

to transcribe the reference.

Workflow:

```text
Reference Audio
      │
      ▼
Whisper
      │
      ▼
Reference Transcript
      │
      ▼
F5-TTS
```

This is especially useful when working with longer recordings where manually typing the transcript would be inconvenient.

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────┐
│                  Gradio Web Interface                │
├──────────────────────────────────────────────────────┤
│ Voice Cloner │ Story │ Podcast │ Hindi/Urdu         │
│ Audio Editor │ RVC   │ Perfect Clone │ Training     │
├──────────────────────────────────────────────────────┤
│                    app.py                             │
├───────────────┬───────────────┬──────────────────────┤
│ F5-TTS        │ Edge-TTS      │ Whisper              │
│ Voice Clone   │ Neural TTS    │ ASR + Embeddings     │
├───────────────┴───────────────┴──────────────────────┤
│                Audio Processing Layer                 │
│        pydub • FFmpeg • noisereduce • soundfile      │
├──────────────────────────────────────────────────────┤
│                 Optional RVC Layer                    │
│                    rvc_infer.py                       │
├──────────────────────────────────────────────────────┤
│              Local Storage / Model Cache              │
│ saved_voices • rvc_models • training_data • hf_cache  │
└──────────────────────────────────────────────────────┘
```

---

# 📁 Project Structure

```text
voiceforge-ai-studio/
│
├── app.py
│
├── rvc_infer.py
├── transliterate.py
│
├── inference_config.toml
├── requirements.txt
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
│
├── setup.bat
├── run_all.bat
│
├── demo.html
├── CHANGES.md
├── README.md
│
├── assets/
│   └── LOGO.jpg
│
├── saved_voices/
│   ├── ARIA/
│   │   ├── audio.wav
│   │   └── text.txt
│   └── real/
│       ├── audio.wav
│       └── text.txt
│
├── rvc_models/
│   ├── Character.pth
│   └── Character.index
│
├── training_data/
│   └── session_*/
│       ├── chunk_000.wav
│       └── ...
│
├── temp/
│
└── hf_cache/
```

---

# ⚙️ Requirements

## Minimum recommended environment

### Software

- Python **3.11**
- FFmpeg
- Git
- pip
- Internet connection for first-time model/dependency downloads

### Hardware

The application can run on CPU, but AI speech generation can be significantly slower.

Recommended for serious experimentation:

- NVIDIA GPU
- CUDA-compatible PyTorch installation
- 8 GB+ VRAM preferred for heavier workflows
- SSD storage

### Storage

Model downloads can consume several gigabytes.

The Docker configuration uses:

```text
hf_cache/
```

as a persistent Hugging Face cache so downloaded model weights do not need to be downloaded again after every container recreation.

---

# 🪟 Installation on Windows

## Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/voiceforge-ai-studio.git
cd voiceforge-ai-studio
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bat
venv\Scripts\activate
```

---

## Step 3 — Install PyTorch

For an NVIDIA CUDA 12.1 environment:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

For CPU-only usage, install a compatible CPU build of PyTorch instead.

Always verify your PyTorch/CUDA combination against the official PyTorch installation instructions for your system.

---

## Step 4 — Install project dependencies

```bash
pip install -r requirements.txt
```

---

## Step 5 — Start the application

```bash
python app.py
```

Then open the local Gradio URL shown in the terminal, normally:

```text
http://127.0.0.1:7860
```

---

# ⚡ Windows Quick Setup

The repository includes:

```text
setup.bat
```

You can run:

```bat
setup.bat
```

This creates a virtual environment, installs the CUDA 12.1 PyTorch packages, and installs the remaining project dependencies.

After setup:

```bat
venv\Scripts\activate
python app.py
```

---

# 🐳 Docker Installation

Docker is the recommended way to get a more reproducible Linux-based environment.

## Requirements

Install:

- Docker Desktop on Windows/macOS
- Docker Engine + Docker Compose on Linux

---

## Build and start

From the project directory:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:7860
```

### Run in detached mode

```bash
docker compose up --build -d
```

### View logs

```bash
docker compose logs -f voice-studio
```

### Stop the application

```bash
docker compose down
```

---

# 💾 Docker Persistence

The Docker Compose configuration persists important application data.

### Bind-mounted directories

```text
saved_voices/
rvc_models/
training_data/
```

### Persistent model cache

```text
hf_cache
```

This means deleting/recreating the container does not automatically delete your saved voice library, RVC models, training datasets, or cached Hugging Face model files.

---

# 🧪 Running the Application

Once the application is running:

1. Open the Gradio interface.
2. Choose a workflow from the tabs.
3. Upload your reference audio where required.
4. Enter your script.
5. Select the appropriate voice/model.
6. Run generation.
7. Listen to the generated output.
8. Save or further process the audio.

---

# 🎭 How to Use the Voice Cloner

## Step 1 — Save a voice

Open:

```text
🎭 Voice Cloner
```

Upload:

```text
Reference Voice
```

Enter:

```text
Reference Text
```

or use:

```text
🔍 Auto-Extract
```

Give the voice a name, for example:

```text
MyCharacter
```

Click:

```text
💾 Save to Library
```

---

## Step 2 — Generate speech

Enter your new script:

```text
Welcome everyone. Today we are exploring the future of artificial intelligence.
```

Select your reference voice and click:

```text
🎙️ Generate Clone
```

Wait for F5-TTS to complete.

---

# 🎙️ How to Create a Multi-Voice Podcast

## Step 1

Create and save multiple voices.

Example:

```text
Host
Guest
Narrator
```

## Step 2

Open:

```text
🎙️ Multi-Voice Podcast
```

## Step 3

Write:

```text
Host: Welcome to today's AI podcast.

Guest: Thanks for having me.

Host: What do you think about local AI models?

Guest: They are becoming more capable every year.
```

## Step 4

Click:

```text
🎙️ Generate Full Podcast
```

The application generates the individual lines and combines them into one audio file.

---

# 🌏 How to Generate Hindi/Urdu Speech

Open:

```text
🌏 Hindi / Urdu
```

Enter Roman Hindi/Urdu:

```text
Aaj hum artificial intelligence ke bare mein baat karenge.
```

Enable:

```text
🔄 Auto-convert Roman → Devanagari
```

Select a voice such as:

```text
hi-IN-MadhurNeural
```

Then click:

```text
🎙️ Generate Hindi/Urdu Voice
```

You can also enter native-script text directly when appropriate.

---

# 🧠 How to Prepare a Training Dataset

Open:

```text
🧠 Voice Training Studio
```

## Step 1 — Upload raw audio

Prefer approximately:

```text
5–10 minutes
```

of clean single-speaker speech.

## Step 2 — Configure

Example:

```text
Chunk Size: 10 seconds
Target Volume: -20 dBFS
```

## Step 3 — Preprocess

Click:

```text
⚙️ Preprocess Dataset
```

The pipeline:

```text
Load
 ↓
Denoise
 ↓
Mono
 ↓
16 kHz
 ↓
Silence Detection
 ↓
Silence Removal
 ↓
Normalize
 ↓
Chunk
 ↓
Export WAV
```

## Step 4 — Inspect output

Look inside:

```text
training_data/session_X/
```

for generated chunks.

---

# 📊 How to Compare Two Voices

Open:

```text
🧠 Voice Training Studio
```

Under:

```text
Voice Quality Analyzer
```

upload:

```text
Audio A: Original Voice
Audio B: Generated/Cloned Voice
```

Click:

```text
🧠 Analyze Similarity
```

The application extracts Whisper encoder representations and computes cosine similarity.

Use the score as a comparative development metric rather than a definitive identity-verification result.

---

# ✂️ How to Edit Audio

Open:

```text
✂️ Audio Editor
```

Upload the source audio.

Set:

```text
Start Time
End Time
```

Then choose:

```text
✂️ Trim
```

or:

```text
🗑️ Cut
```

For replacement:

1. Select a time range.
2. Enter replacement text.
3. Select a saved voice.
4. Click:
   ```text
   🔄 Replace Segment
   ```

---

# 🎤 How to Use RVC

RVC is optional.

Place your model in:

```text
rvc_models/
```

Example:

```text
rvc_models/
├── MyCharacter.pth
└── MyCharacter.index
```

If your environment has a compatible `rvc-python` installation, the RVC workflow can be enabled and used from the application.

The command-line backend is also available directly:

```bash
python rvc_infer.py ^
  --model rvc_models/MyCharacter.pth ^
  --index rvc_models/MyCharacter.index ^
  --input input.wav ^
  --output output.wav ^
  --pitch 0 ^
  --method rmvpe
```

On Linux/macOS, use `\` instead of `^` for multiline commands, or place the command on one line.

---

# 🔧 Environment Variables

The application supports executable overrides.

### F5-TTS

```text
F5_TTS_EXE
```

### Edge-TTS

```text
EDGE_TTS_EXE
```

### RVC Python

```text
RVC_PYTHON_EXE
```

This allows the same application code to work with:

- Windows virtual environments
- Linux environments
- Docker
- Custom executable paths

The application first checks the environment variable, then local virtual-environment paths, then the system `PATH`.

---

# 🧰 Troubleshooting

## ❌ FFmpeg not found

Install FFmpeg and make sure it is available in `PATH`.

Check:

```bash
ffmpeg -version
```

Docker already installs FFmpeg inside the image.

---

## ❌ Torch / Torchaudio ABI error

A common cause is installing incompatible Torch and Torchaudio builds.

The Dockerfile intentionally installs:

```text
torch
torchaudio
```

together from the same PyTorch index and then locks their versions with a constraints file.

For local installation, make sure the two packages are compatible.

---

## ❌ F5-TTS command not found

Check:

```bash
f5-tts_infer-cli --help
```

If necessary, set:

```text
F5_TTS_EXE
```

to the correct executable.

On Windows it may be located under:

```text
venv\Scripts\
```

---

## ❌ Edge-TTS command not found

Check:

```bash
edge-tts --help
```

If required, set:

```text
EDGE_TTS_EXE
```

to the correct executable.

---

## ❌ Voice generation is extremely slow

Possible causes:

- Running on CPU
- Large model downloads
- Slow disk
- Insufficient RAM
- Low GPU VRAM
- Model initialization on every operation

For faster experimentation, use a compatible NVIDIA GPU and keep the Hugging Face cache persistent.

---

## ❌ Generated audio is silent

Try:

- A cleaner reference
- A clearer speaker recording
- A more accurate reference transcript
- A different reference voice
- A longer or more natural speech sample

The application also checks generated audio for extremely low variance and reports silent output.

---

## ❌ Docker cannot resolve external services

The Compose configuration includes:

```text
8.8.8.8
1.1.1.1
```

as DNS servers to reduce Docker DNS forwarding problems.

If your corporate network, VPN, firewall, or ISP blocks external DNS, you may need to adjust the Docker networking configuration.

---

## ❌ Model downloads repeatedly

Use the included Docker Compose setup.

The application stores Hugging Face cache data in:

```text
hf_cache
```

and Docker persists it using the named volume:

```text
hf_cache
```

---

# 🔐 Privacy

Voice data can be highly sensitive.

When running locally:

- Reference audio is processed by your local application workflow.
- Saved voices are stored in:
  ```text
  saved_voices/
  ```
- Training data is stored in:
  ```text
  training_data/
  ```
- Model caches are stored locally in:
  ```text
  hf_cache/
  ```

However, some integrated services may communicate with external services.

For example, **Edge-TTS requires network access** to generate neural speech.

Before using sensitive recordings, review the policies and terms of the services/models you use.

---

# ⚖️ Responsible Voice-Cloning Policy

This project should be used responsibly.

### ✅ Appropriate uses

- Your own voice
- Voices for which you have explicit permission
- Fictional voices/models you are legally allowed to use
- Research and experimentation
- Accessibility applications
- Authorized media production
- Character voices when the relevant rights permit the use

### ❌ Avoid

- Impersonating real people without permission
- Fraud or scams
- Identity deception
- Unauthorized celebrity voice cloning
- Creating misleading evidence
- Bypassing authentication
- Using copyrighted or proprietary voice datasets without permission

When publishing generated content, consider clearly disclosing that AI-generated or AI-transformed speech was used.

---

# 🧪 Development Notes

The application was hardened against several real-world audio-processing problems.

### Dataset preprocessing protections

- Corrupt audio files are handled gracefully.
- Zero-duration audio is rejected.
- Fully silent audio does not cause normalization failures.
- Gain is limited to ±24 dB.
- Very short cleaned datasets are rejected.
- Silence detection includes padding to reduce accidental word clipping.
- Audio is standardized to mono 16 kHz before ML preprocessing.

### Cross-platform executable discovery

The application does not depend exclusively on hard-coded Windows paths.

It can resolve executables from:

```text
1. Environment variable
2. Windows virtual environment
3. POSIX virtual environment
4. System PATH
```

This is important for Docker/Linux deployment.

---

# 🐳 Docker Architecture

The Docker image is based on:

```text
python:3.11-slim
```

and installs:

```text
FFmpeg
Git
build-essential
curl
DNS utilities
PyTorch
Torchaudio
Python dependencies
```

### Health check

Docker periodically checks:

```text
http://127.0.0.1:7860/
```

to verify that the Gradio application is responding.

### GPU

The Compose file contains an optional NVIDIA GPU configuration.

If your host has:

- NVIDIA GPU
- NVIDIA driver
- NVIDIA Container Toolkit

you can enable the GPU reservation section in:

```text
docker-compose.yml
```

The default configuration is CPU-oriented for portability.

---

# 📦 Main Dependencies

| Dependency | Purpose |
|---|---|
| Gradio | Web UI |
| PyTorch | Deep-learning runtime |
| Torchaudio | Audio + PyTorch integration |
| Transformers | Whisper and ML models |
| F5-TTS | Voice cloning / TTS |
| Edge-TTS | Neural TTS |
| Pydub | Audio manipulation |
| FFmpeg | Audio decoding/encoding |
| SoundFile | WAV/audio I/O |
| NumPy | Numerical processing |
| noisereduce | Noise reduction |
| yt-dlp | Optional media/audio retrieval workflows |
| tomli-w | F5-TTS configuration generation |

---

# 🧩 Technology Stack

```text
Frontend
└── Gradio

Backend
└── Python

AI / ML
├── F5-TTS
├── Whisper
├── PyTorch
├── Transformers
└── Optional RVC

Audio
├── FFmpeg
├── Pydub
├── SoundFile
└── noisereduce

Language
└── Custom Roman Hindi/Urdu transliteration

Deployment
├── Docker
└── Docker Compose
```

---

# 🔄 End-to-End Workflow

```text
                 ┌───────────────────┐
                 │   User / Script   │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │   Gradio UI       │
                 └─────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   Voice Clone        Story Mode         Podcast
        │                  │                  │
        ▼                  ▼                  ▼
     F5-TTS         Edge-TTS + F5-TTS   Multi-line TTS
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Audio Processing  │
                 └─────────┬─────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
             WAV         RVC         Analysis
              │            │            │
              └────────────┼────────────┘
                           ▼
                 ┌───────────────────┐
                 │ Generated Audio   │
                 └───────────────────┘
```

---

# 📈 Future Roadmap

Potential future improvements include:

- [ ] Full F5-TTS fine-tuning pipeline
- [ ] Dataset quality scoring before training
- [ ] Automatic speaker diarization
- [ ] Multi-speaker dataset separation
- [ ] Better Urdu transliteration
- [ ] More robust Roman Urdu language detection
- [ ] Automatic loudness/LUFS normalization
- [ ] Audio waveform visualization
- [ ] Batch generation
- [ ] Queue management
- [ ] Background job processing
- [ ] User authentication
- [ ] Project/workspace management
- [ ] Model version management
- [ ] Experiment tracking
- [ ] Voice-quality dashboard
- [ ] Automatic pronunciation evaluation
- [ ] REST API
- [ ] WebSocket generation progress
- [ ] Cloud deployment
- [ ] GPU-aware job scheduling
- [ ] Better RVC dependency isolation
- [ ] Automated tests and CI/CD

---

# 🧑‍💻 Development

Run the application directly:

```bash
python app.py
```

For development, keep generated files out of Git where appropriate.

Recommended `.gitignore` entries include:

```gitignore
venv/
rvc_venv/
__pycache__/
*.pyc
temp/
training_data/
hf_cache/
*.wav
*.mp3
*.pth
*.index
```

Be careful when committing audio or model files because they can be very large and may contain sensitive or copyrighted material.

---

# 📜 License

Add an appropriate license before publicly distributing this repository.

For example, if you want a permissive open-source license, you may choose MIT, Apache-2.0, or another license that matches your intended use.

Also review the licenses and terms of the third-party models, libraries, voices, and datasets used by the project. A project license does not automatically grant rights to third-party models or voice data.

---

# 🙌 Acknowledgements

This project builds on the work of the open-source and research communities around:

- F5-TTS
- OpenAI Whisper
- PyTorch
- Hugging Face Transformers
- Gradio
- Pydub
- FFmpeg
- noisereduce
- RVC ecosystem
- Microsoft Edge-TTS ecosystem

Please review the respective projects and model licenses before commercial redistribution.

---

# ⭐ GitHub Repository

If this project is useful for your research, portfolio, or AI audio experimentation:

```text
⭐ Star the repository
🍴 Fork it
🐛 Report reproducible bugs
💡 Suggest improvements
🔧 Submit pull requests
```

---

# 👨‍💻 Author

***Abdul Rehman***

Built as an AI audio engineering project combining:

```text
Artificial Intelligence
+
Machine Learning
+
Speech Processing
+
Generative AI
+
Audio Engineering
+
Docker
+
Python
```

---

<div align="center">

### 🎙️ Build. Clone. Transform. Analyze.

**VoiceForge AI Studio**

</div>
