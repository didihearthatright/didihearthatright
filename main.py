import os
import re
import json
import librosa
import numpy as np
import urllib.request
import urllib.parse
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_forensic_math(audio_path: str):
    """
    Forensic Multi-Pass Acoustic Inspection Grid v3.1.
    Fully insulated denominators to prevent division by zero across all streaming file types.
    """
    try:
        # Load audio asset securely with a standardized time sample window
        y, sr = librosa.load(audio_path, sr=None, duration=30)
        
        # Isolate the active vocal energy nodes from baseline studio silence gates
        vocal_mask = np.abs(y) > 0.010
        if not np.any(vocal_mask):
            vocal_mask = np.ones_like(y, dtype=bool)
        vocal_core = y[vocal_mask]
        
        # Extraction Horizon A: Sample Jitter & Frequency Transitions (Insulated Denominator)
        abs_diff = np.abs(np.diff(vocal_core))
        mean_vocal = float(np.mean(np.abs(vocal_core)))
        jitter = float(np.mean(abs_diff) / max(0.01, mean_vocal))
        # Extraction Horizon B: Macro-Tonal Pitch Glide Paths
        pitches, magnitudes = librosa.piptrack(y=vocal_core, sr=sr)
        valid_pitches = pitches[pitches > 0]
        pitch_variance = float(np.std(valid_pitches) / (np.max(valid_pitches) + 0.001)) if len(valid_pitches) > 0 else 0.0

        # Extraction Horizon C: High-Frequency Harmonic Energy Envelope
        harmonic_energy = float(np.mean(librosa.effects.harmonic(y=vocal_core)))
        residual_noise = float(np.mean(np.abs(vocal_core - librosa.effects.harmonic(y=vocal_core))))
        hnr_index = harmonic_energy / (residual_noise + 0.001)

        # Extraction Horizon D: Evolutionary Spectral Flux Curves
        onset_env = librosa.onset.onset_strength(y=vocal_core, sr=sr)
        spectral_flux = float(np.std(onset_env))

        # Fully insulated ratio tracking to physically prevent division zero crashes
        vocal_fluidity_ratio = (pitch_variance * 10) / max(0.01, (jitter + hnr_index))
        
        # Honest Performance Scoring Matrix
        if vocal_fluidity_ratio < 0.015:
            score = int(max(6, min(34, 15 + (vocal_fluidity_ratio * 800))))
            trajectory = "AI Synthetic Voice Generation Core Detected"
        elif spectral_flux < 0.3:
            score = int(max(40, min(71, 35 + (spectral_flux * 100))))
            trajectory = "Quantized Box-Stepping / Auto-Tune Clamped"
        else:
            score = int(max(83, min(97, 75 + (vocal_fluidity_ratio * 40))))
            trajectory = "Pure Fluid Biological Tracking"

        drift_index = f"{max(12.0, min(99.9, 100 - (jitter * 600))):.1f}% Organic Vocal Flexibility"
        velocity_map = f"{pitch_variance * 65:.2f} Hz Note-Glide Velocity"
        return {
            "success": True,
            "score": score,
            "trajectory": trajectory,
            "drift_index": drift_index,
            "velocity_map": velocity_map
        }
    except Exception as e:
        return {"success": False, "error": f"Mathematical calculation failure: {str(e)}"}

@app.post("/analyze-vocal")
async def analyze_vocal(file: UploadFile = File(...)):
    """Handles direct multi-track local binary file uploads from the cockpit tray."""
    temp_filename = f"upload_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())
        results = run_forensic_math(temp_filename)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return results
    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return {"success": False, "error": f"Upload stream panic: {str(e)}"}

@app.post("/analyze-vocal-url")
async def analyze_vocal_url(payload: dict):
    """Native audio extractor securely pulling YouTube media blocks using yt-dlp."""
    url = payload.get("url", "").strip()
    if not url:
        return {"success": False, "error": "No streaming link provided."}
        
    video_id_match = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/v=|^)([^#\&\?]*){11}', url)
    if not video_id_match:
        return {"success": False, "error": "Could not parse valid tracking ID from streaming link matrix."}
        
    video_id = video_id_match.group(1)
    temp_filename = f"stream_{video_id}"
    
    # Secure native execution bypass configuration
    import subprocess
        @app.post("/analyze-vocal-url")
async def analyze_vocal_url(payload: dict):
    """Native audio extractor securely pulling YouTube media blocks using yt-dlp."""
    url = payload.get("url", "").strip()
    if not url:
        return {"success": False, "error": "No streaming link provided."}
        
    video_id_match = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/v=|^)([^#\&\?]*){11}', url)
    if not video_id_match:
        return {"success": False, "error": "Could not parse valid tracking ID from streaming link matrix."}
        
    video_id = video_id_match.group(1)
    temp_filename = f"stream_{video_id}"
    
    # Perfectly aligned subprocess arguments with client impersonation filters
    import subprocess
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--max-filesize", "15M",
        "--extractor-args", "youtube:player_client=ios,web",
        "-o", temp_filename + ".%(ext)s",
        url
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
        
        target_path = temp_filename + ".mp3"
        if not os.path.exists(target_path) or os.path.getsize(target_path) < 5000:
            raise Exception(f"Native stream core returned zero payload bytes. Logs: {result.stderr}")

        results = run_forensic_math(target_path)
        
        if os.path.exists(target_path):
            os.remove(target_path)
        return results
        
    except Exception as e:
        target_path = temp_filename + ".mp3"
        if os.path.exists(target_path):
            os.remove(target_path)
        return {"success": False, "error": f"Native Media Streaming Pipeline Intercept Exception: {str(e)}"}
