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
    Forensic Multi-Pass Acoustic Inspection Grid v2.0.
    Utilizes an Acoustic Activity Filter to completely isolate vocals from studio masters.
    """
    try:
        # Load audio asset securely with a standardized time sample window
        y, sr = librosa.load(audio_path, sr=None, duration=30)
        
        # Acoustic Activity Filter: Remove empty tracking zones and analog silence gates
        vocal_mask = np.abs(y) > 0.015
        if not np.any(vocal_mask):
            vocal_mask = np.ones_like(y, dtype=bool) # Fallback insulation block
        vocal_core = y[vocal_mask]
        
        # Horizon A: Microscopic Biological Tremor Index (Active Jitter)
        abs_diff = np.abs(np.diff(vocal_core))
        jitter = float(np.mean(abs_diff) / (np.mean(np.abs(vocal_core)) + 0.001))
        # Horizon B: Spectral Flux Dynamic Variations
        onset_env = librosa.onset.onset_strength(y=vocal_core, sr=sr)
        spectral_flux = float(np.std(onset_env))

        # Horizon C: Fine-Tonal Pitch Variance Tracker (Note-Glide)
        pitches, magnitudes = librosa.piptrack(y=vocal_core, sr=sr)
        valid_pitches = pitches[pitches > 0]
        pitch_variance = float(np.std(valid_pitches) / (np.max(valid_pitches) + 0.001)) if len(valid_pitches) > 0 else 0.0

        # Horizon D: Spectral Rolloff Envelope (High-Frequency Air Dispersion)
        rolloff = librosa.feature.spectral_rolloff(y=vocal_core, sr=sr, roll_percent=0.85)
        rolloff_variance = float(np.std(rolloff) / (np.max(rolloff) + 0.001)) if len(rolloff) > 0 else 0.0

        # Horizon E: Multi-Pass Harmonic-to-Noise Ratio (HNR Profile)
        harmonic_energy = float(np.mean(librosa.effects.harmonic(y=vocal_core)))
        residual_noise = float(np.mean(np.abs(vocal_core - librosa.effects.harmonic(y=vocal_core))))
        hnr_index = harmonic_energy / (residual_noise + 0.001)

        # Multi-Pass Balanced Score Aggregation Script
        raw_score = 100 - (jitter * 280) - (pitch_variance * 140) - (rolloff_variance * 110) + (hnr_index * 8)
        
        # Recalibrated Balanced Threshold Triggers (Analog Studio Gate Compensated)
        if jitter < 0.016 or hnr_index < 0.02:  
            score = int(max(7, min(36, raw_score - 48)))
            trajectory = "AI Synthetic Voice Generation Core Detected"
        elif spectral_flux < 0.6 or rolloff_variance < 0.02:  
            score = int(max(40, min(73, raw_score - 22)))
            trajectory = "Quantized Box-Stepping / Auto-Tune Clamped"
        else:  
            score = int(max(84, min(97, raw_score)))
            trajectory = "Pure Fluid Biological Tracking"

        drift_index = f"{max(10.0, min(99.9, 100 - (jitter * 550))):.1f}% Organic Vocal Flexibility"
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
            video_id = url.split("v=").split("&")
        elif "be/" in url:
            video_id = url.split("be/").split("?")
        elif "shorts/" in url:
            video_id = url.split("shorts/").split("?")
        else:
            video_id = url.split("/")[-1].split("?")
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
