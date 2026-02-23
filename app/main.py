"""
Fall Detection API - Backend using FastAPI + Google Gemini
Supports: Video file upload + YouTube URL analysis
"""

import os
import re
import time
import tempfile
import subprocess
import traceback
from pathlib import Path

# ── Load .env FIRST before anything else ─────────────────────────────────────
from dotenv import load_dotenv

# Try multiple locations for .env file
_env_locations = [
    Path(__file__).parent / ".env",          # same folder as main.py
    Path(__file__).parent.parent / ".env",   # one level up
    Path.cwd() / ".env",                     # wherever you run from
]

_loaded = False
for _env_path in _env_locations:
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
        print(f"✅ Loaded .env from: {_env_path}")
        _loaded = True
        break

if not _loaded:
    print("⚠️  No .env file found. Checked:")
    for p in _env_locations:
        print(f"   - {p}")

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Debug: show what was found
print(f"🔑 GEMINI_API_KEY value: {'SET (' + GEMINI_API_KEY[:8] + '...)' if GEMINI_API_KEY else 'NOT SET / EMPTY'}")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "\n\n❌ GEMINI_API_KEY is missing!\n"
        "Create a .env file in the same folder as main.py with:\n"
        "GEMINI_API_KEY=your_actual_key_here\n"
        "(No quotes around the key)\n"
    )

MAX_DURATION_SECONDS = 30
ALLOWED_MIME_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/mpeg"}

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")
print("✅ Gemini model initialized: gemini-2.5-flash")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Fall Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"


# ── Models ────────────────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    fall_detected: bool
    confidence: int
    person_detected: bool
    explanation: str
    raw_response: str
    source: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_video_duration(file_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", file_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def is_youtube_url(url: str) -> bool:
    pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w\-]+"
    return bool(re.match(pattern, url.strip()))


def download_youtube_video(url: str, output_path: str) -> float:
    info_cmd = ["yt-dlp", "--no-playlist", "--print", "duration", url.strip()]
    try:
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        duration_str = info_result.stdout.strip()
        duration = float(duration_str) if duration_str else 0.0
    except Exception:
        duration = 0.0

    if duration > MAX_DURATION_SECONDS:
        raise ValueError(f"YouTube video is {duration:.0f}s long. Maximum allowed is {MAX_DURATION_SECONDS}s.")

    download_cmd = [
        "yt-dlp", "--no-playlist",
        "-f", "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", output_path,
        "--merge-output-format", "mp4",
        url.strip(),
    ]
    result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Could not download video: {result.stderr[:300]}")
    return duration


def parse_gemini_response(text: str) -> dict:
    text_lower = text.lower()

    fall_detected = any(
        phrase in text_lower
        for phrase in ["fall detected: yes", "fall: yes", "a fall occurred", "person has fallen",
                       "fall accident detected", "fallen down", "accidental fall"]
    )
    no_fall = any(
        phrase in text_lower
        for phrase in ["fall detected: no", "fall: no", "no fall", "no accidental fall",
                       "did not fall", "hasn't fallen"]
    )
    if no_fall:
        fall_detected = False

    person_detected = any(
        phrase in text_lower
        for phrase in ["person detected: yes", "person: yes", "a person", "human", "individual",
                       "someone", "a man", "a woman", "people"]
    )

    confidence = 75
    conf_match = re.search(r"confidence[:\s]+(\d+)\s*%", text_lower)
    if conf_match:
        confidence = int(conf_match.group(1))
    else:
        if any(w in text_lower for w in ["clearly", "definitely", "certainly", "obvious"]):
            confidence = 92
        elif any(w in text_lower for w in ["likely", "appears", "seems", "probably"]):
            confidence = 75
        elif any(w in text_lower for w in ["possibly", "might", "unclear", "uncertain"]):
            confidence = 55

    return {"fall_detected": fall_detected, "person_detected": person_detected, "confidence": confidence}


def run_gemini_analysis(tmp_path: str, mime_type: str = "video/mp4"):
    try:
        file_size = os.path.getsize(tmp_path)
        print(f"[GEMINI] Uploading: {tmp_path} | Size: {file_size} bytes | MIME: {mime_type}")

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes). Please try again.")

        gemini_file = genai.upload_file(tmp_path, mime_type=mime_type)
        print(f"[GEMINI] Uploaded: {gemini_file.name}, state: {gemini_file.state.name}")

        max_wait, waited = 60, 0
        while gemini_file.state.name == "PROCESSING" and waited < max_wait:
            print(f"[GEMINI] Processing... {waited}s elapsed")
            time.sleep(2)
            waited += 2
            gemini_file = genai.get_file(gemini_file.name)

        print(f"[GEMINI] Final state: {gemini_file.state.name}")

        if gemini_file.state.name != "ACTIVE":
            raise HTTPException(status_code=500, detail=f"Gemini file processing failed. State: {gemini_file.state.name}")

        prompt = """Analyze this video carefully for fall detection. Please answer the following:

1. PERSON DETECTED: Is there a human person visible in the video? (Yes/No)
2. FALL DETECTED: Did an accidental fall occur in this video? (Yes/No)
3. CONFIDENCE: What is your confidence percentage in this fall detection result? (0-100%)
4. EXPLANATION: Provide a 2-3 sentence explanation of what you observed.

Format your response EXACTLY like this:
Person Detected: Yes/No
Fall Detected: Yes/No
Confidence: XX%
Explanation: [your explanation here]"""

        print("[GEMINI] Sending to model...")
        response = model.generate_content([gemini_file, prompt])
        raw_text = response.text
        print(f"[GEMINI] Response:\n{raw_text}")

        try:
            genai.delete_file(gemini_file.name)
        except Exception:
            pass

        parsed = parse_gemini_response(raw_text)
        explanation = "Analysis complete."
        for line in raw_text.splitlines():
            if line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()
                break

        return parsed, explanation, raw_text

    except HTTPException:
        raise
    except Exception as e:
        print(f"[GEMINI ERROR]\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(str(INDEX_FILE))


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_video(
    video: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
):
    # ── YouTube URL ──────────────────────────────────────────────────────────
    if youtube_url and youtube_url.strip():
        if not is_youtube_url(youtube_url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp_path = tmp.name

        try:
            try:
                download_youtube_video(youtube_url, tmp_path)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except RuntimeError as e:
                raise HTTPException(status_code=500, detail=str(e))

            parsed, explanation, raw_text = run_gemini_analysis(tmp_path)
            return AnalysisResult(
                fall_detected=parsed["fall_detected"],
                confidence=parsed["confidence"],
                person_detected=parsed["person_detected"],
                explanation=explanation,
                raw_response=raw_text,
                source="youtube",
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── File Upload ──────────────────────────────────────────────────────────
    elif video:
        if video.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed: MP4, MOV, AVI, WebM.",
            )

        print(f"[UPLOAD] Reading: {video.filename}")
        content = await video.read()
        print(f"[UPLOAD] Read {len(content)} bytes")

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty. Please select a valid video.")

        suffix = Path(video.filename).suffix or ".mp4"
        tmp_path = tempfile.mktemp(suffix=suffix)

        with open(tmp_path, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        print(f"[UPLOAD] Saved: {tmp_path} | Size: {os.path.getsize(tmp_path)} bytes")

        try:
            duration = get_video_duration(tmp_path)
            if duration > MAX_DURATION_SECONDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Video is {duration:.1f}s long. Maximum is {MAX_DURATION_SECONDS}s.",
                )

            parsed, explanation, raw_text = run_gemini_analysis(tmp_path, video.content_type)
            return AnalysisResult(
                fall_detected=parsed["fall_detected"],
                confidence=parsed["confidence"],
                person_detected=parsed["person_detected"],
                explanation=explanation,
                raw_response=raw_text,
                source="upload",
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    else:
        raise HTTPException(status_code=400, detail="Please provide a video file or YouTube URL.")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "gemini-2.5-flash",
        "index_exists": INDEX_FILE.exists(),
        "api_key_set": bool(GEMINI_API_KEY),
        "env_file_found": _loaded,
    }