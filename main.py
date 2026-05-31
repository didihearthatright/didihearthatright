from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import numpy as np
import scipy.io.wavfile as wav
import audioread
import os
import yt_dlp

app = FastAPI(title="DIHTR Universal Optimized Forensic Core Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def process_audio_pure_python(audio_path: str):
    # Dynamic decoder block handles mp3 streams into raw PCM arrays natively
    with audioread.audio_open(audio_path) as f:
        sr = f.samplerate
        channels = f.channels
        data_list = []
        
        # HIGH-PERFORMANCE TARGET OPTIMIZATION PASSTHROUGH
        # Limits the array ingestion window to approximately the first 30 seconds of audio data
        max_samples = sr * channels * 30
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
    # Truncate strictly to the 30-second boundary threshold
    if len(y_int) > (sr * channels * 30):
        y_int = y_int[:(sr * channels * 30)]
        
    y_raw = y_int.astype(np.float32) / 32768.0
    
    if channels > 1:
        y_raw = y_raw.reshape(-1, channels).mean(axis=1)
        
    hop_length = 512
    frame_length = 2048
    frames = [y_raw[i:i+frame_length] for i in range(0, len(y_raw)-frame_length, hop_length)]
    
    if len(frames) < 20:
        return {"success": False, "error": "Insufficient lead vocal tracking data length."}
        
    rms_vals = np.array([np.sqrt(np.mean(frame**2)) for frame in frames])
    max_rms = max(0.001, np.max(rms_vals))
    active_frames = rms_vals > (max_rms * 0.05)
    
    pitch_trajectory = []
    for idx, frame in enumerate(frames):
        if not active_frames[idx]:
            continue
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        
        dfr = np.diff(corr)
        start_search = np.where(dfr > 0)
        if len(start_search) == 0:
            continue
            
        peak = np.argmax(corr[start_search:]) + start_search
        if peak > 0:
            freq = sr / peak
            if 65.0 <= freq <= 1046.0:  # Bound directly inside human vocal tract thresholds (C2 to C6)
                pitch_trajectory.append(freq)
                
    pitch_clean = np.array(pitch_trajectory)
    if len(pitch_clean) < 20:
        return {"success": False, "error": "Vocal stream density mismatch."}
        
    pitch_velocity = np.abs(np.diff(pitch_clean))
    clamped_snaps = np.sum(pitch_velocity > 35)
    total_transitions = len(pitch_velocity)
    
    clamp_ratio = clamped_snaps / max(1, total_transitions)
    base_score = 100 - (clamp_ratio * 240)
    final_score = int(max(42, min(97, base_score)))
    
    return {
        "success": True,
        "score": final_score,
        "velocity_map": f"{float(np.mean(pitch_velocity)):.2f} Hz note-glide velocity",
        "drift_index": f"{100 - (clamp_ratio * 100):.1f}% organic vocal flexibility",
        "trajectory": "Pure Fluid Biological Tracking" if clamp_ratio < 0.04 else "Quantized Box-Stepping Detected"
    }

@app.post("/analyze-vocal")
async def analyze_vocal(file: Optional[UploadFile] = File(None), link: Optional[str] = Form(None)):
    if link and link.strip() != "":
        target_url = link.strip()
        if os.path.exists("dl_stream.mp3"):
            os.remove("dl_stream.mp3")
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'dl_stream.%(ext)s',
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target_url])
            if not os.path.exists("dl_stream.mp3"):
                return {"success": False, "error": "Streaming compilation extraction fault."}
            metrics = process_audio_pure_python("dl_stream.mp3")
            os.remove("dl_stream.mp3")
            return metrics
        except Exception as err:
            if os.path.exists("dl_stream.mp3"):
                os.remove("dl_stream.mp3")
            return {"success": False, "error": f"Cloud stream extractor block: {str(err)}"}

    if file:
        try:
            audio_bytes = await file.read()
            with open("temp_up.mp3", "wb") as f:
                f.write(audio_bytes)
            metrics = process_audio_pure_python("temp_up.mp3")
            os.remove("temp_up.mp3")
            return metrics
        except Exception as e:
            if os.path.exists("temp_up.mp3"):
                os.remove("temp_up.mp3")
            return {"success": False, "error": str(e)}
            
    return {"success": False, "error": "No valid audio track stream payload identified."}
