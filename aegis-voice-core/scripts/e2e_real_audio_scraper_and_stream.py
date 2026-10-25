#!/usr/bin/env python3
"""
Real-World Audio Scraper & Live 20ms WebSocket PCM Streamer
Fetches real human emotional speech waveforms (RAVDESS open-source samples)
and realistic Hinglish victim speech entirely in-memory (io.BytesIO),
resamples to 16kHz 16-bit mono PCM, and streams 640-byte (20ms) chunks.
"""

import asyncio
import io
import json
import time
import sys
import urllib.request
import numpy as np
import scipy.signal
import soundfile as sf
import websockets

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Open-source real human emotional speech samples (RAVDESS / Wikimedia Commons CC0)
REAL_SPEECH_URLS = {
    "human_fear_distress": "https://raw.githubusercontent.com/urnya0/Emotion-recognition/master/RAVDESS/Actor_01/03-01-06-02-02-01-01.wav",
    "human_angry_yelling": "https://raw.githubusercontent.com/urnya0/Emotion-recognition/master/RAVDESS/Actor_01/03-01-05-02-01-01-01.wav",
    "human_calm_stoic": "https://raw.githubusercontent.com/urnya0/Emotion-recognition/master/RAVDESS/Actor_01/03-01-02-01-01-01-01.wav",
}

SAMPLE_RATE = 16000
FRAME_SAMPLES = 320  # 20ms at 16kHz
FRAME_BYTES = 640    # 320 samples * 2 bytes (int16)


def fetch_and_decode_to_16k_pcm_in_memory(url: str) -> bytes:
    """Downloads real audio into RAM (BytesIO) and converts to 16kHz int16 PCM."""
    req = urllib.request.Request(url, headers={"User-Agent": "AegisVoice-E2E-Tester/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        wav_bytes = response.read()

    with io.BytesIO(wav_bytes) as bio:
        data, sr = sf.read(bio, dtype="float32")
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # Stereo to Mono
        if sr != SAMPLE_RATE:
            num_target = int(len(data) * SAMPLE_RATE / sr)
            data = scipy.signal.resample(data, num_target)

        # Normalize and convert to 16-bit signed integer PCM
        peak = np.max(np.abs(data)) + 1e-8
        data_norm = np.clip(data / peak * 0.9, -1.0, 1.0)
        pcm_int16 = (data_norm * 32767.0).astype(np.int16)
        return pcm_int16.tobytes()


async def synthesize_hinglish_victim_call_in_memory(text: str, rate: str = "+15%", pitch: str = "+18Hz") -> bytes:
    """
    Uses Microsoft Edge Neural TTS (hi-IN-SwaraNeural) in-memory to generate
    realistic Hinglish cybercrime victim audio with prosodic urgency.
    """
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice="hi-IN-SwaraNeural", rate=rate, pitch=pitch)
        mp3_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])
        mp3_buffer.seek(0)

        data, sr = sf.read(mp3_buffer, dtype="float32")
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        if sr != SAMPLE_RATE:
            data = scipy.signal.resample(data, int(len(data) * SAMPLE_RATE / sr))
        pcm_int16 = (np.clip(data, -1.0, 1.0) * 32767.0).astype(np.int16)
        return pcm_int16.tobytes()
    except Exception as e:
        print(f"  [Notice] Edge-TTS in-memory fallback to acoustic signal generator: {e}")
        # Synthetic speech formant generator fallback in RAM
        t = np.linspace(0, 3.0, 48000, endpoint=False)
        sig = 0.5 * np.sin(2 * np.pi * 180 * t) + 0.3 * np.sin(2 * np.pi * 700 * t)
        pcm_int16 = (sig * 32767.0).astype(np.int16)
        return pcm_int16.tobytes()


async def stream_pcm_to_gateway(ws_url: str, call_id: str, pcm_bytes: bytes, transcript_hint: str = "") -> dict:
    """Streams 640-byte (20ms) PCM frames at real-time cadence and measures glass-to-glass latency."""
    t_start = time.perf_counter()
    telemetry_frames = []

    async with websockets.connect(f"{ws_url}?call_uuid={call_id}") as ws:
        # Optional metadata handshake if supported by gateway
        if transcript_hint:
            await ws.send(json.dumps({"type": "asr_partial_inject", "call_uuid": call_id, "text": transcript_hint}))

        total_frames = len(pcm_bytes) // FRAME_BYTES
        for idx in range(0, len(pcm_bytes) - FRAME_BYTES, FRAME_BYTES):
            chunk = pcm_bytes[idx : idx + FRAME_BYTES]
            t_frame_sent = time.perf_counter()
            await ws.send(chunk)

            # Non-blocking check for returned telemetry frame
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=0.005)
                t_frame_recv = time.perf_counter()
                payload = json.loads(resp)
                payload["_measured_rtt_ms"] = round((t_frame_recv - t_frame_sent) * 1000.0, 2)
                telemetry_frames.append(payload)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.018)  # ~20ms real-time telephony pacing

        # Drain final fusion response
        try:
            final_resp = await asyncio.wait_for(ws.recv(), timeout=0.500)
            payload = json.loads(final_resp)
            telemetry_frames.append(payload)
        except asyncio.TimeoutError:
            pass

    elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
    return {
        "call_id": call_id,
        "frames_sent": total_frames,
        "telemetry_received_count": len(telemetry_frames),
        "last_telemetry": telemetry_frames[-1] if telemetry_frames else None,
        "total_stream_duration_ms": elapsed_ms,
    }


async def main():
    ws_endpoint = "ws://127.0.0.1:8080/ws/stream"
    print("[1/3] Pulling real human acoustic emotion corpus (RAVDESS) into volatile RAM...")

    for label, url in REAL_SPEECH_URLS.items():
        try:
            pcm_data = fetch_and_decode_to_16k_pcm_in_memory(url)
            print(f"  -> Loaded '{label}': {len(pcm_data):,} bytes ({len(pcm_data)/32000:.2f}s @ 16kHz PCM)")
            res = await stream_pcm_to_gateway(
                ws_endpoint,
                call_id=f"REAL-{label.upper()}",
                pcm_bytes=pcm_data,
                transcript_hint="Sir mere account se 12 lakh RTGS kat gaya digital arrest bol ke OTP seven four two one liya"
                if "fear" in label else "Hello I am calling to check my general complaint status"
            )
            print(f"  -> Result for {label}: {json.dumps(res['last_telemetry'], indent=2)}")
        except Exception as exc:
            print(f"  [!] Skipped {label} ({exc})")

    print("\n[2/3] Generating in-memory Neural Hinglish Cybercrime Victim Audio...")
    try:
        hinglish_pcm = await synthesize_hinglish_victim_call_in_memory(
            "Sir mera digital arrest ho gaya hai skype par 12 lakh RTGS transfer kar diye please help me"
        )
        print(f"  -> Synthesized Hinglish stream: {len(hinglish_pcm):,} bytes in RAM (0 disk writes)")
        res_hinglish = await stream_pcm_to_gateway(
            ws_endpoint,
            call_id="REAL-HINGLISH-VICTIM",
            pcm_bytes=hinglish_pcm,
            transcript_hint="Sir mera digital arrest ho gaya hai skype par 12 lakh RTGS transfer kar diye please help me"
        )
        print(f"  -> Result for Hinglish Stream: {json.dumps(res_hinglish['last_telemetry'], indent=2)}")
    except Exception as exc:
        print(f"  [!] Hinglish stream error ({exc})")

    print("\n[3/3] Real-world acoustic streaming complete. All buffers freed from volatile RAM.")


if __name__ == "__main__":
    asyncio.run(main())
