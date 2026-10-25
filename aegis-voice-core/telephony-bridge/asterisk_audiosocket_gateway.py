"""
Project Aegis-Voice: Asterisk AudioSocket Gateway
Consumes 8kHz/16kHz 16-bit linear PCM frames (20ms chunks = 320 or 640 bytes)
piped via Asterisk's native AudioSocket application without altering the primary bridge.
"""

import asyncio
import uuid
import struct
import logging
import numpy as np
import websockets
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AsteriskAudioSocketGateway")

AUDIOSOCKET_PORT = 9092
INGESTION_WS_URL = "ws://127.0.0.1:8080/ws/stream"

class AsteriskAudioSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = AUDIOSOCKET_PORT, ingestion_ws_url: str = INGESTION_WS_URL):
        self.host = host
        self.port = port
        self.ingestion_ws_url = ingestion_ws_url
        self.active_sessions: Dict[str, asyncio.StreamWriter] = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info(f"Incoming AudioSocket connection from {peer}")
        call_uuid: Optional[str] = None
        ws_client = None

        try:
            # AudioSocket protocol header: Type (1 byte) + Payload Length (2 bytes big endian) + UUID (16 bytes)
            header = await reader.readexactly(3)
            msg_type, payload_len = struct.unpack("!BH", header)
            
            call_uuid_bytes = await reader.readexactly(16)
            call_uuid = str(uuid.UUID(bytes=call_uuid_bytes))
            logger.info(f"Initialized call session {call_uuid} [msg_type={msg_type}, len={payload_len}]")
            self.active_sessions[call_uuid] = writer

            # Connect to Ingestion Gateway WebSocket for live stream forwarding
            ws_url = f"{self.ingestion_ws_url}?uuid={call_uuid}"
            try:
                ws_client = await websockets.connect(ws_url)
                logger.info(f"Connected to Ingestion Gateway at {ws_url}")
            except Exception as e:
                logger.warning(f"Could not connect to Ingestion Gateway at {ws_url}: {e}")

            while True:
                msg_hdr = await reader.read(3)
                if not msg_hdr or len(msg_hdr) < 3:
                    break
                t, length = struct.unpack("!BH", msg_hdr)
                if length == 0:
                    continue
                audio_payload = await reader.readexactly(length)
                
                # Each 20ms chunk = 320 bytes (8kHz mono) or 640 bytes (16kHz mono)
                # If PSTN switch delivers 8kHz audio, upsample to 16kHz standard for Aegis workers
                if len(audio_payload) == 320:
                    samples_8k = np.frombuffer(audio_payload, dtype=np.int16)
                    samples_16k = np.repeat(samples_8k, 2)
                    audio_payload = samples_16k.tobytes()

                # Forward 20ms frame to Ingestion Gateway
                if ws_client is not None:
                    try:
                        await ws_client.send(audio_payload)
                    except Exception as e:
                        logger.warning(f"Failed to forward audio frame to {ws_url}: {e}")
                        ws_client = None
                else:
                    # Attempt reconnect
                    try:
                        ws_client = await websockets.connect(ws_url)
                        await ws_client.send(audio_payload)
                    except Exception:
                        pass
        except (asyncio.IncompleteReadError, ConnectionResetError):
            logger.info(f"AudioSocket session terminated: {peer}")
        finally:
            if ws_client is not None:
                try:
                    await ws_client.close()
                except Exception:
                    pass
            if call_uuid:
                self.active_sessions.pop(call_uuid, None)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"Asterisk AudioSocket Gateway listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(AsteriskAudioSocketServer().start())
