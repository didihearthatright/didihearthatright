from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import numpy as np
import audioread
import os

app = FastAPI(title="DIHTR Universal Pure Forensic Core Engine")

# 🔥 ARMED CORS SECURITY MODULE: Explicitly forces Render to pass header authentication stamps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def process_audio_high_speed(audio_path: str):
    with audioread.audio_open(audio_path) as f:
        sr = f.samplerate
        channels = f.channels
        data_list = []
        
        max_samples = sr * channels * 15
        current_samples = 0
        for buf in f:
            chunk = np.frombuffer(buf, dtype=np.int16)
            data_list.append(chunk)
            current_samples += len(chunk)
            if current_samples >= max_samples:
                break
        
    if not data_list:
        return {"success": False, "error": "Empty audio stream buffer payload."}
        
    y_int = np.concatenate(data_list)
    if len(y_int) > (sr * channels * 15):
        y_int = y_int[:(sr * channels * 15)]
        
    y_raw = y_int.astype(np.float32) / 32768.0
    if channels > 1:
        y_raw = y_raw.reshape(-1, channels).mean(axis=1)
        
    frame_length = 1024
    hop_length = 512
    frames = [y_raw[i:i+frame_length] for i in range(0, len(y_raw)-frame_length, hop_length)]
    
    if len(frames) < 10:
        return {"success": False, "error": "Insufficient lead vocal tracking data length."}
        
    rms_vals = np.sqrt(np.mean(np.square(frames), axis=1))
    max_rms = max(0.001, np.max(rms_vals))
    active_mask = rms_vals > (max_rms * 0.08)
    
    pitch_trajectory = []
    for idx, frame in enumerate(frames):
        if not active_mask[idx]:
            continue
            
        fft_data = np.abs(np.fft.rfft(frame))
        fft_freqs = np.fft.rfftfreq(frame_length, d=1.0/sr)
        
        vocal_band = (fft_freqs >= 65.0) & (fft_freqs <= 1000.0)
        if not np.any(vocal_band):
            continue
            
        peak_idx = np.argmax(fft_data[vocal_band])
        fundamental_freq = fft_freqs[vocal_band][peak_idx]
        
        if fundamental_freq > 0:
            pitch_trajectory.append(fundamental_freq)
            
    pitch_clean = np.array(pitch_trajectory)
    if len(pitch_clean) < 10:
        return {"success": False, "error": "Vocal stream density mismatch."}
        
    pitch_velocity = np.abs(np.diff(pitch_clean))
    clamped_snaps = np.sum(pitch_velocity > 40)
    total_transitions = len(pitch_velocity)
    
    clamp_ratio = clamped_snaps / max(1, total_transitions)
    base_score = 100 - (clamp_ratio * 240)
    final_score = int(max(42, min(97, base_score)))
    
    return {
        "success": True,
        "score": final_score,
        "velocity_map": f"{float(np.mean(pitch_velocity)):.2f} Hz note-glide velocity",
        "drift_index": f"{100 - (clamp_ratio * 100):.1f}% organic vocal flexibility",
        "trajectory": "Pure Fluid Biological Tracking" if clamp_ratio < 0.05 else "Quantized Box-Stepping Detected"
    }

@app.post("/analyze-vocal/")
async def analyze_vocal(file: Optional[UploadFile] = File(None), link: Optional[str] = Form(None)):
    if file:
        try:
            audio_bytes = await file.read()
            with open("temp_up.mp3", "wb") as f:
                f.write(audio_bytes)
            metrics = process_audio_high_speed("temp_up.mp3")
            os.remove("temp_up.mp3")
            return metrics
        except Exception as e:
            if os.path.exists("temp_up.mp3"):
                os.remove("temp_up.mp3")
            return {"success": False, "error": str(e)}
            
    return {"success": False, "error": "No valid audio upload file payload identified."}
