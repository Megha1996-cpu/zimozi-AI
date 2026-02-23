# 🎯 Fall Detection AI — Python + Google Gemini

A web application that uses **Google Gemini AI** to analyze uploaded videos and detect whether a person has experienced an accidental fall.

---

## 🗂 Project Structure

```
fall-detection/
├── backend/
│   ├── main.py              # FastAPI server + Gemini integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Single-page UI (HTML + vanilla JS)
└── README.md
```

---

## ✅ Features

- Upload videos up to 30 seconds (MP4, MOV, AVI, WebM)
- Live video preview with duration validation in the browser
- Sends video to **Google Gemini 1.5 Flash** for AI analysis
- Displays:
  - ✅ / 🚨 Fall Detected: Yes or No
  - Confidence % with animated bar
  - Person detected indicator
  - Short explanation from Gemini
  - Raw Gemini response (expandable)
- Drag-and-drop support
- Full error handling (wrong type, too long, API errors)

---

## ⚙️ Setup Instructions

### 1. Get a Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a new API key (free tier works)
3. Copy the key

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/fall-detection.git
cd fall-detection
```

### 3. Set Up Python Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Your API Key

**Option A – Environment variable (recommended):**
```bash
# Mac/Linux
export GEMINI_API_KEY="your_key_here"

# Windows (Command Prompt)
set GEMINI_API_KEY=your_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_key_here"
```

**Option B – Edit main.py directly (for quick testing):**
```python
GEMINI_API_KEY = "your_key_here"   # line 13 in main.py
```

### 5. (Optional) Install ffprobe for Duration Validation

```bash
# Mac
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows: download from https://ffmpeg.org/download.html
```

> Without ffprobe, duration is only validated on the frontend. This is fine for demos.

### 6. Run the Application

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at: **http://localhost:8000**

---

## 🔌 Gemini API Integration

| Detail         | Value                    |
|----------------|--------------------------|
| Model          | `gemini-1.5-flash`       |
| API version    | `google-generativeai` SDK v0.7.x |
| File upload    | Gemini File API (`genai.upload_file`) |
| Input          | Raw video file (up to 30s) |
| Output         | Text response parsed for fall/confidence data |

### What the prompt asks Gemini:

```
Analyze this video carefully for fall detection. Please answer:
1. PERSON DETECTED: Is there a human person visible? (Yes/No)
2. FALL DETECTED: Did an accidental fall occur? (Yes/No)
3. CONFIDENCE: Confidence percentage (0-100%)
4. EXPLANATION: 2-3 sentence explanation

Format:
Person Detected: Yes/No
Fall Detected: Yes/No
Confidence: XX%
Explanation: ...
```

---

## ⚠️ Assumptions & Limitations

- **Video duration** is enforced on the frontend using the browser's `video.duration` and on the backend (if ffprobe is available).
- **Gemini 1.5 Flash** supports video natively via the File API. Videos are uploaded, analyzed, then deleted.
- Gemini may take 5–30 seconds to process depending on video length and server load.
- Confidence scores are extracted from Gemini's text response; if absent, they are inferred from language cues (e.g., "clearly" → 92%).
- The model is not a certified medical or safety device — this is a demonstration only.
- Maximum supported video size by Gemini File API: **2 GB**.

---

## 🚀 API Endpoints

| Method | Endpoint   | Description               |
|--------|------------|---------------------------|
| GET    | `/`        | Serve frontend HTML page  |
| POST   | `/analyze` | Analyze uploaded video     |
| GET    | `/health`  | Health check               |

### POST `/analyze` — Request
- Content-Type: `multipart/form-data`
- Field: `video` (file)

### POST `/analyze` — Response
```json
{
  "fall_detected": true,
  "confidence": 87,
  "person_detected": true,
  "explanation": "A person is clearly visible falling backwards in the hallway.",
  "raw_response": "Person Detected: Yes\nFall Detected: Yes\nConfidence: 87%\nExplanation: ..."
}
```

---

## 🧪 Testing the App

1. Find or record a short video (under 30s)
2. Try videos with: someone falling, someone walking normally, empty room
3. Upload and click **Analyze Video**
4. Observe the result card

---

## 📦 Dependencies

```
fastapi          — Web framework
uvicorn          — ASGI server
python-multipart — File upload parsing
google-generativeai — Gemini AI SDK
pydantic         — Data validation
ffprobe (optional) — Video duration check
```
