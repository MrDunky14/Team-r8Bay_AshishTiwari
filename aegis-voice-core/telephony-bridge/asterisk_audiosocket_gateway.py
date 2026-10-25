"""
Project Aegis-Voice: Asterisk AudioSocket Gateway
Consumes 8kHz/16kHz 16-bit linear PCM frames (20ms chunks = 320 or 640 bytes)
piped via Asterisk's native AudioSocket application without altering the primary bridge.
"""

import asyncio
import uuid
import struct
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AsteriskAudioSocketGateway")

AUDIOSOCKET_PORT = 9092
INGESTION_WS_URL = "ws://127.0.0.1:8080/ws/stream"

class AsteriskAudioSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = AUDIOSOCKET_PORT):
        self.host = host
        self.port = port
        self.active_sessions = {}

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        logger.info(f"Incoming AudioSocket connection from {peer}")

        try:
            # AudioSocket protocol header: Type (1 byte) + Payload Length (2 bytes big endian) + UUID (16 bytes)
            header = await reader.readexactly(3)
            msg_type, payload_len = struct.unpack("!BH", header)
            
            call_uuid_bytes = await reader.readexactly(16)
            call_uuid = str(uuid.UUID(bytes=call_uuid_bytes))
            logger.info(f"Initialized call session {call_uuid} [msg_type={msg_type}, len={payload_len}]")
            self.active_sessions[call_uuid] = writer

            while True:
                msg_hdr = await reader.read(3)
                if not msg_hdr or len(msg_hdr) < 3:
                    break
                t, length = struct.unpack("!BH", msg_hdr)
                if length == 0:
                    continue
                audio_payload = await reader.readexactly(length)
                
                # Audio frames are forwarded to Aegis Volatile Ingestion Gateway
                # Each 20ms chunk = 320 bytes (8kHz mono) or 640 bytes (16kHz mono)
                # print/log heartbeat periodically
        except (asyncio.IncompleteReadError, ConnectionResetError):
            logger.info(f"AudioSocket session terminated: {peer}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"Asterisk AudioSocket Gateway listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(AsteriskAudioSocketServer().start())
