from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import numpy as np
import librosa
import os
import subprocess

app = FastAPI(title="DIHTR Universal Forensic Core Engine")

# OPEN THE SYSTEM SECURITY GATES FOR DIRECT PROD CONNECTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# INTERNAL CALCULATION ENGINE LOGIC MATRIX
def process_audio_forensics(audio_path: str):
    y_raw, sr = librosa.load(audio_path, sr=22050)
    y_vocals = librosa.effects.harmonic(y_raw, margin=4.0)
    y_vocals = librosa.effects.preemphasis(y_vocals)
    
    rms = librosa.feature.rms(y=y_vocals)
    db_rms = librosa.amplitude_to_db(rms, ref=np.max)
    active_frames = db_rms > -28
    
    if not np.any(active_frames):
        return {"success": False, "error": "Vocal stream density mismatch."}

    f0, voiced_flag, voiced_probs = librosa.pyin(
        y_vocals, fmin=librosa.note_to_hz('F2'), fmax=librosa.note_to_hz('C6'), sr=sr
    )
    f0_clean = f0[~np.isnan(f0) & active_frames[:len(f0)]]
    
    if len(f0_clean) < 20:
        return {"success": False, "error": "Insufficient lead vocal tracking data."}

    pitch_velocity = np.abs(np.diff(f0_clean))
    clamped_snaps = np.sum(pitch_velocity > 30)
    total_transitions = len(pitch_velocity)
    
    harmonic_power = np.sum(librosa.feature.rms(y=y_vocals))
    noise_power = np.sum(librosa.feature.rms(y=y_raw - y_vocals))
    hnr = float(harmonic_power / max(0.001, noise_power))

    clamp_ratio = clamped_snaps / total_transitions
    base_score = 100 - (clamp_ratio * 260)
    
    if clamp_ratio < 0.035 and hnr > 0.75:
        base_score += 6
        
    final_score = int(max(42, min(97, base_score)))
    
    return {
        "success": True,
        "score": final_score,
        "velocity_map": f"{float(np.mean(pitch_velocity)):.2f} Hz note-glide velocity",
        "drift_index": f"{100 - (clamp_ratio * 100):.1f}% organic vocal flexibility",
        "trajectory": "Pure Fluid Biological Tracking" if clamp_ratio < 0.04 else "Quantized Box-Stepping Detected"
    }

# GATEWAY A: HANDLES STANDARD PHYSICAL AUDIO FILE UPLOADS
@app.post("/analyze-vocal")
async def analyze_vocal(
    file: Optional[UploadFile] = File(None),
    link: Optional[str] = Form(None)
):
    # DYNAMIC ROUTER: SEAMLESSLY DETECTS LINK PAYLOADS PASSED TO ENDPOINT
    if link or (file is None):
        target_url = link if link else ""
        if not target_url:
            return {"success": False, "error": "No valid input source detected."}
            
        out_template = "dl_stream_audio.%(ext)s"
        if os.path.exists("dl_stream_audio.mp3"):
            os.remove("dl_stream_audio.mp3")
            
        try:
            # INTEGRATED PAID-TIER LINUX DOWNLOAD TERMINAL ENGINE
            cmd = [
                "python3", "-m", "youtube_dl",
                "--extract-audio",
                "--audio-format", "mp3",
                "-o", out_template,
                target_url
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if not os.path.exists("dl_stream_audio.mp3"):
                return {"success": False, "error": "Streaming binary extraction failed."}
                
            metrics = process_audio_forensics("dl_stream_audio.mp3")
            os.remove("dl_stream_audio.mp3")
            return metrics
            
        except Exception as streaming_err:
            return {"success": False, "error": f"Extraction driver alert: {str(streaming_err)}"}

    # DEFAULT FALLBACK: SENDS UPLOADED FILES STRAIGHT TO MATRICES
    try:
        audio_bytes = await file.read()
        with open("temp_upload.file", "wb") as f:
            f.write(audio_bytes)
            
        metrics = process_audio_forensics("temp_upload.file")
        os.remove("temp_upload.file")
        return metrics
        
    except Exception as e:
        if os.path.exists("temp_upload.file"):
            os.remove("temp_upload.file")
        return {"success": False, "error": str(e)}
