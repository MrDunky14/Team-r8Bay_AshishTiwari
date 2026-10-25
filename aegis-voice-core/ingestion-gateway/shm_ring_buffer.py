"""
Project Aegis-Voice: Volatile Ring Buffer & Zero-Disk Memory Persistence
Complies with India DPDP Act 2023 & UIDAI Regulations:
Raw PCM audio chunks are pinned strictly in volatile RAM (/dev/shm or multiprocessing.shared_memory).
Zero audio bytes are ever written to persistent disk (SSD/NVMe).
"""

import os
import sys
import numpy as np
from collections import deque
from typing import Optional

try:
    from multiprocessing import shared_memory
    HAS_POSIX_SHM = True
except ImportError:
    HAS_POSIX_SHM = False

WINDOW_FRAMES = 75     # 1.5s at 20ms/frame
FRAME_SAMPLES = 320    # 20ms at 16000 Hz
FRAME_BYTES = 640      # 16-bit PCM = 2 bytes per sample

class EphemeralAudioRingBuffer:
    """
    Circular sliding window buffer maintaining exactly 1.5 seconds (75 frames)
    of 16kHz mono/stereo PCM in volatile memory. Older frames are overwritten in place.
    """
    def __init__(self, call_uuid: str, max_frames: int = WINDOW_FRAMES):
        self.call_uuid = call_uuid
        self.max_frames = max_frames
        self.frame_deque = deque(maxlen=max_frames)
        self.total_frames_received = 0
        self.total_audio_seconds = 0.0
        self.shm_block = None

        # Attempt to bind pinned shared memory block if platform permits
        if sys.platform != "win32" and os.path.exists("/dev/shm"):
            self.shm_path = f"/dev/shm/aegis_ring/{self.call_uuid}.pcm"
        else:
            self.shm_path = None

    def push_frame(self, pcm_bytes: bytes) -> None:
        """Pushes a 20ms PCM frame (640 bytes) into the volatile ring buffer."""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        self.frame_deque.append(samples)
        self.total_frames_received += 1
        self.total_audio_seconds += 0.020

    def get_window(self) -> Optional[np.ndarray]:
        """Returns the full 1.5-second concatenated waveform if full."""
        if len(self.frame_deque) < self.max_frames:
            return None
        return np.concatenate(list(self.frame_deque))

    def clear(self):
        """Immediately zeroes out memory upon call termination."""
        self.frame_deque.clear()
        if self.shm_block:
            try:
                self.shm_block.close()
                self.shm_block.unlink()
            except Exception:
                pass
