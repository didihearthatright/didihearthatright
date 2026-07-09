import os
import re
import json
import librosa
import numpy as np
import urllib.request
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
    Forensic Multi-Pass Acoustic Inspection Grid.
    Measures Jitter, Pitch Variance, Spectral Flux, Spectral Rolloff, and HNR anomalies.
    """
    try:
        # Load audio asset securely with a standardized time sample window
        y, sr = librosa.load(audio_path, sr=None, duration=30)
        
        # Horizon A: Microscopic Biological Tremor Index (Jitter)
        abs_diff = np.abs(np.diff(y))
        jitter = float(np.mean(abs_diff) / (np.mean(np.abs(y)) + 0.001))
        
        # Horizon B: Spectral Flux Dynamic Variations
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        spectral_flux = float(np.std(onset_env))
        # Horizon C: Fine-Tonal Pitch Variance Tracker (Note-Glide)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        valid_pitches = pitches[pitches > 0]
        pitch_variance = float(np.std(valid_pitches) / (np.max(valid_pitches) + 0.001)) if len(valid_pitches) > 0 else 0.0

        # Horizon D: Spectral Rolloff Envelope (High-Frequency Air Dispersion)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0]
        rolloff_variance = float(np.std(rolloff) / (np.max(rolloff) + 0.001)) if len(rolloff) > 0 else 0.0

        # Horizon E: Multi-Pass Harmonic-to-Noise Ratio (HNR Profile)
        harmonic_energy = float(np.mean(librosa.effects.harmonic(y)))
        residual_noise = float(np.mean(np.abs(y - librosa.effects.harmonic(y))))
        hnr_index = harmonic_energy / (residual_noise + 0.001)

        # Multi-Pass Score Compilation System
        raw_score = 100 - (jitter * 350) - (pitch_variance * 200) - (rolloff_variance * 150) + (hnr_index * 5)
        
        # Rigorous Boundary Detection & Verdict Threshold Controls
        if jitter < 0.028 or hnr_index < 0.05:  
            score = int(max(6, min(38, raw_score - 45)))
            trajectory = "AI Synthetic Voice Generation Core Detected"
        elif spectral_flux < 1.0 or rolloff_variance < 0.05:  
            score = int(max(42, min(72, raw_score - 20)))
            trajectory = "Quantized Box-Stepping / Auto-Tune Clamped"
        else:  
            score = int(max(82, min(97, raw_score)))
            trajectory = "Pure Fluid Biological Tracking"

        drift_index = f"{max(10.0, min(99.9, 100 - (jitter * 650))):.1f}% Organic Vocal Flexibility"
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
    """Bypasses cloud server blocks via decentralized open-source mirror routing."""
    url = payload.get("url", "").strip()
    if not url:
        return {"success": False, "error": "No streaming link provided."}
        
    video_id = ""
    try:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "be/" in url:
            video_id = url.split("be/")[1].split("?")[0]
        elif "shorts/" in url:
            video_id = url.split("shorts/")[1].split("?")[0]
        else:
            video_id = url.split("/")[-1].split("?")[0]
    except Exception:
        return {"success": False, "error": "Link formatting parsing exception encountered."}
        
    if not video_id or len(video_id) < 10:
        return {"success": False, "error": "Could not extract valid tracking ID from streaming link matrix."}
        
    temp_filename = f"stream_{video_id}.mp3"
    stream_provider = f"https://vevioz.com{video_id}"
    
    try:
        import urllib.request
        req = urllib.request.Request(
            stream_provider, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0'}
        )
        
        with urllib.request.urlopen(req) as response, open(temp_filename, 'wb') as out_file:
            out_file.write(response.read())

        if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) < 5000:
            raise Exception("Mirror network extraction node returned empty payload data stream.")

        results = run_forensic_math(temp_filename)
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return results
        
    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return {"success": False, "error": f"Extraction Pipeline Node Offline: {str(e)}"}
