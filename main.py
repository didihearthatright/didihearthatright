from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import librosa

app = FastAPI(title="DIHTR Universal Forensic Core Engine")

# BULLETPROOF SECURITY PASSTHROUGH RULES — OPENS THE DATA GATES FOR DIHTR.COM
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.post("/analyze-vocal")
async def analyze_vocal(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        y_raw, sr = librosa.load(librosa.util.buf_to_float(audio_bytes), sr=22050)
        
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
        
    except Exception as e:
        return {"success": False, "error": str(e)}
