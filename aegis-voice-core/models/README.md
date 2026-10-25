# Project Aegis-Voice: Open-Weight Checkpoints & Hardware Sizing

This directory documents the open-weight model checkpoints, precision targets, and execution backends utilized across the Aegis-Voice microservice architecture.

## Pinned Model Checkpoints

| Subsystem | Model / Repository | Weights & Quantization | Target Runtime | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **VAD** | `snakers4/silero-vad` | `silero_vad.onnx` (v5, 2.32 MB) | ONNX Runtime CPU | 1.4ms Voice Activity Detection & silence gating |
| **Primary SER** | `iic/emotion2vec_plus_large` | 300M parameters, FP16 TensorRT | NVIDIA L4 / T4 GPU | Continuous 3D [Valence, Arousal, Dominance] + F0 |
| **CPU Fallback SER** | `pankotaro/emotion2vec-plus-base-onnx` | Base ONNX + OpenSMILE eGeMAPS | x86_64 CPU (AVX-512) | 9.5ms fallback for air-gapped rural PSAPs |
| **Anti-Spoofing** | `SpeechAntiSpoofingBenchmarks/AASIST-L` | 85k parameters, graph attention | PyTorch / ONNX | Real-time synthetic voice / deepfake detection |
| **Indic ASR** | `ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large` | CTC Head, ONNX FP16 | NVIDIA L4 GPU | 115ms streaming transcription for 22 Indian languages |
| **Multilingual ASR** | `deepdml/faster-whisper-large-v3-turbo-ct2` | `int8_float16` CTranslate2 | NVIDIA L4 GPU | High-accuracy multilingual speech-to-text |

## Hardware Requirements

- **Production Node (50 Concurrent Dual-Stream Calls):**
  - GPU: 1x NVIDIA L4 (24 GB VRAM, 72W TDP) or 1x NVIDIA T4 (16 GB VRAM)
  - CPU: 16-Core AMD EPYC or Intel Xeon Silver
  - RAM: 32 GB DDR4/DDR5
  - Shared Memory: Mount 2GB `tmpfs` at `/dev/shm/aegis_ring` (Zero-Disk Persistence)

- **Air-Gapped Rural PSAP Fallback (No GPU):**
  - CPU: Commodity 8-core / 16-core CPU with AVX-512 support
  - RAM: 16 GB DDR4
  - Pipeline: OpenSMILE eGeMAPS (88-dim) + LightGBM + whisper.cpp (q8_0)
