from fastapi import FastAPI, UploadFile, File
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
import io
import numpy as np
import librosa

app = FastAPI(title="DIHTR Universal Forensic Core Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dihtr.com", "https://dihtr.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-vocal")
async def analyze_vocal(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        y_raw, sr = librosa.load(io.BytesIO(audio_bytes), sr=22050)
        
        y_vocals = librosa.effects.harmonic(y_raw, margin=4.0)
        y_vocals = librosa.effects.preemphasis(y_vocals)
        
        rms = librosa.feature.rms(y=y_vocals)
        db_rms = librosa.amplitude_to_db(rms, ref=np.max)
        active_singing = db_rms > -28
        
        if not np.any(active_singing):
            return {"success": False, "error": "Vocal stream density too faint."}

        f0, voiced_flag, voiced_probs = librosa.pyin(
            y_vocals, fmin=librosa.note_to_hz('F2'), fmax=librosa.note_to_hz('C6'), sr=sr
        )
        if f0.ndim > 1:
            f0_clean = f0[~np.isnan(f0) & active_singing[:len(f0)]]
        else:
            f0_clean = f0[~np.isnan(f0)]
        
        if len(f0_clean) < 20:
            return {"success": False, "error": "Insufficient pitch data resolved."}

        pitch_velocity = np.abs(np.diff(f0_clean))
        clamped_snaps = np.sum(pitch_velocity > 30)
        total_transitions = len(pitch_velocity)
        
        harmonic_p = np.sum(librosa.feature.rms(y=y_vocals))
        noise_p = np.sum(librosa.feature.rms(y=y_raw - y_vocals))
        hnr = float(harmonic_p / max(0.001, noise_p))

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
    except Exception as e:
        return {"success": False, "error": str(e)}
