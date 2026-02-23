# 🎯 Fall Detection AI — Python + Google Gemini

A web application that uses **Google Gemini 2.5 Flash** to analyze uploaded videos and detect whether a person has experienced an accidental fall.

---

## 🗂 Project Structure

```
app/
├── main.py        # FastAPI backend + Gemini integration
├── index.html     # Frontend UI (HTML + JavaScript)
└── .env           # Your API key (create this manually)
```

---

## ✅ Features

- Upload videos up to 30 seconds (MP4, MOV, AVI, WebM)
- Paste a YouTube / YouTube Shorts URL for analysis
- Live video preview with duration validation
- **Google Gemini 2.5 Flash** AI analysis
- Displays:
  - 🚨 / ✅ Fall Detected: Yes or No
  - Confidence % with animated progress bar
  - Person detected indicator
  - Short explanation from Gemini
  - Raw Gemini response (expandable)
- Drag-and-drop video upload support
- API key loaded securely from `.env` file
- Full error handling for all edge cases

---

## ⚙️ Setup Instructions

### 1. Get a Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the key

---

### 2. Install Dependencies

Make sure Python 3.8+ is installed, then run:

```bash
pip install fastapi uvicorn python-multipart google-generativeai python-dotenv yt-dlp
```

---

### 3. Create Your `.env` File

In the **same folder as `main.py`**, create a file named `.env`:

```
GEMINI_API_KEY=AIzaSy...your_full_key_here
```

> ⚠️ No quotes. No spaces around `=`. Just the key directly.

Your folder should look like this:

```
app/
├── main.py
├── index.html
└── .env        ← create this file
```

---

### 4. Run the Application

Open terminal, go to the `app` folder, and run:

```bash
cd path/to/app
python -m uvicorn main:app --reload --port 8000
```

You should see:

```
✅ Loaded .env from: .../app/.env
🔑 GEMINI_API_KEY value: SET (AIzaSyAJ...)
✅ Gemini model initialized: gemini-2.5-flash
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### 5. Open in Browser

```
http://127.0.0.1:8000
```

---

## 🔌 Gemini API Integration

| Detail | Value |
|--------|-------|
| Model | `gemini-2.5-flash` |
| SDK | `google-generativeai` |
| File Upload | Gemini File API (`genai.upload_file`) |
| Input | Raw video file (up to 30s) |
| Output | Structured text parsed for fall/confidence |

### Prompt sent to Gemini:

```
Analyze this video carefully for fall detection:

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

## 🎬 How to Use

### Option A — Upload a Video File

1. Click **Upload Video** tab
2. Drag & drop or click to select a video (MP4, MOV, AVI, WebM)
3. Max duration: **30 seconds**
4. Click **Analyze Video**
5. View results

### Option B — YouTube URL

1. Click **YouTube URL** tab
2. Paste any YouTube or YouTube Shorts link
3. Must be **under 30 seconds** (Shorts recommended)
4. Click **Analyze Video**
5. View results

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve frontend UI |
| POST | `/analyze` | Analyze video (file or YouTube URL) |
| GET | `/health` | Health check |

### POST `/analyze` — Request

- Content-Type: `multipart/form-data`
- Field `video`: video file (optional)
- Field `youtube_url`: YouTube URL string (optional)

### POST `/analyze` — Response

```json
{
  "fall_detected": true,
  "confidence": 87,
  "person_detected": true,
  "explanation": "A person is clearly visible falling backwards.",
  "raw_response": "Person Detected: Yes\nFall Detected: Yes\n...",
  "source": "upload"
}
```

---

## ⚠️ Assumptions & Limitations

- Duration check is done on the frontend (browser) for uploads and via `yt-dlp` for YouTube
- If `ffprobe` is not installed, backend duration validation is skipped (frontend still validates)
- `yt-dlp` must be installed for YouTube URL support
- Gemini 2.5 Flash is used — free tier allows 5 requests/minute and 20 requests/day
- This is a demonstration tool — not a certified safety or medical device
- Uploaded videos are deleted from Gemini servers immediately after analysis

---

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| `GEMINI_API_KEY not found` | Check `.env` file exists in same folder as `main.py` |
| `500 Internal Server Error` | Check terminal for `[GEMINI ERROR]` details |
| `File size: 0 bytes` | Re-upload the video — browser stream issue |
| YouTube download fails | Install `yt-dlp`: `pip install yt-dlp` |
| Model not found error | Make sure you're using `gemini-2.5-flash` |
| Page not loading | Run from `app/` folder, open `http://127.0.0.1:8000` |

---

## 📦 Dependencies

```
fastapi           — Web framework
uvicorn           — ASGI server
python-multipart  — File upload parsing
google-generativeai — Gemini AI SDK
python-dotenv     — Load .env file
yt-dlp            — YouTube video downloader
```

Install all at once:

```bash
pip install fastapi uvicorn python-multipart google-generativeai python-dotenv yt-dlp
```

---

## 🔐 Security Notes

- Never commit your `.env` file to GitHub
- Add `.env` to `.gitignore`:

```
.env
__pycache__/
*.pyc
```

---

## 👤 Author

Built as an assessment project demonstrating AI-powered video analysis using Google Gemini.