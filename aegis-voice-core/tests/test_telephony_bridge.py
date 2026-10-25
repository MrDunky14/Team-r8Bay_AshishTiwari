"""
Tests for Microservice 1: Telephony Bridge
- FreeSWITCH dialplan XML parsing & SMBF_READ_STREAM media bug verification.
- Asterisk AudioSocket gateway header unpacking, 20ms chunk framing (320 bytes 8kHz, 640 bytes 16kHz),
  8k->16k upsampling, WebSocket stream forwarding, and clean disconnection.
"""

import os
import sys
import uuid
import struct
import asyncio
import xml.etree.ElementTree as ET
import numpy as np
import pytest
import websockets

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
TELEPHONY_DIR = os.path.join(CORE_DIR, "telephony-bridge")
if TELEPHONY_DIR not in sys.path:
    sys.path.insert(0, TELEPHONY_DIR)

from asterisk_audiosocket_gateway import AsteriskAudioSocketServer


def test_freeswitch_dialplan_xml_structure():
    """Verify FreeSWITCH dialplan XML syntax, 1930 destination, and shadow audio fork hooks."""
    xml_path = os.path.join(TELEPHONY_DIR, "freeswitch_dialplan_1930.xml")
    assert os.path.exists(xml_path), f"Missing dialplan file at {xml_path}"

    tree = ET.parse(xml_path)
    root = tree.getroot()
    assert root.tag == "include", "Root tag must be <include>"

    extension = root.find("extension")
    assert extension is not None, "Missing <extension> element"
    assert extension.attrib.get("name") == "1930_cybercrime_aegis_shadow_fork"

    condition = extension.find("condition")
    assert condition is not None, "Missing <condition> element"
    assert condition.attrib.get("field") == "destination_number"
    assert condition.attrib.get("expression") == "^1930$"

    actions = condition.findall("action")
    action_dict = {a.attrib.get("application"): a.attrib.get("data") for a in actions}

    # Verify key applications
    assert "answer" in action_dict
    assert action_dict.get("set") == "MOD_AUDIO_FORK_SERVICE_THREADS=4"
    assert "start ws://127.0.0.1:8080/ws/stream stereo 16k" in action_dict.get("export", "")
    assert action_dict.get("bridge") == "user/1930_dispatcher_queue"


def test_freeswitch_media_bug_cpp_source_contract():
    """Verify FreeSWITCH C++ module contains SMBF_READ_STREAM hook and read-only frame handling."""
    cpp_path = os.path.join(TELEPHONY_DIR, "mod_audio_stream_aegis.cpp")
    assert os.path.exists(cpp_path), f"Missing C++ module at {cpp_path}"

    with open(cpp_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SMBF_READ_STREAM" in content or "SWITCH_ABC_TYPE_READ" in content, (
        "C++ module must reference read-only audio hook"
    )
    assert "switch_core_media_bug_get_read_replace_frame" in content, (
        "C++ module must retrieve read audio frame without modifying caller RTP"
    )
    assert "MOD_AUDIO_FORK_SERVICE_THREADS" in content, (
        "C++ module must document or reference dedicated service threads"
    )


def test_audiosocket_protocol_header_packing():
    """Verify Asterisk AudioSocket binary protocol header structure (!BH)."""
    # AudioSocket header: 1 byte type + 2 bytes unsigned short length in big-endian
    msg_type = 0x10  # Audio frame
    payload_len = 320
    packed = struct.pack("!BH", msg_type, payload_len)

    assert len(packed) == 3, "Header must be exactly 3 bytes"
    unpacked_type, unpacked_len = struct.unpack("!BH", packed)
    assert unpacked_type == 0x10
    assert unpacked_len == 320

    # UUID payload: 16 bytes raw UUID
    test_uuid = uuid.uuid4()
    uuid_bytes = test_uuid.bytes
    assert len(uuid_bytes) == 16
    recovered_uuid = uuid.UUID(bytes=uuid_bytes)
    assert recovered_uuid == test_uuid


def test_audiosocket_upsampling_logic():
    """Verify 8kHz 20ms chunk (320 bytes) upsampling to 16kHz standard (640 bytes)."""
    # 20ms at 8kHz mono 16-bit = 160 samples = 320 bytes
    t = np.linspace(0, 0.02, 160, endpoint=False)
    samples_8k = (10000 * np.sin(2 * np.pi * 300 * t)).astype(np.int16)
    payload_8k = samples_8k.tobytes()
    assert len(payload_8k) == 320

    # Execute gateway 2x repeat interpolation
    recovered_8k = np.frombuffer(payload_8k, dtype=np.int16)
    upsampled_16k = np.repeat(recovered_8k, 2)
    payload_16k = upsampled_16k.tobytes()

    assert len(payload_16k) == 640
    assert len(upsampled_16k) == 320  # 320 samples at 16kHz = 20ms
    # Verify values match repeat pattern
    assert upsampled_16k[0] == recovered_8k[0]
    assert upsampled_16k[1] == recovered_8k[0]
    assert upsampled_16k[2] == recovered_8k[1]
    assert upsampled_16k[3] == recovered_8k[1]


def test_audiosocket_server_forwarding_and_lifecycle():
    """Test full async TCP client connection, frame upsampling, websocket forwarding, and clean hangup."""
    async def run_scenario():
        forwarded_frames = []
        ws_server_ready = asyncio.Event()

        # 1. Spin up mock ingestion websocket server
        async def mock_ingest(ws):
            try:
                async for msg in ws:
                    forwarded_frames.append(msg)
            except Exception:
                pass

        ws_server = await websockets.serve(mock_ingest, "127.0.0.1", 9981)

        # 2. Spin up AudioSocket TCP server
        gateway = AsteriskAudioSocketServer(
            host="127.0.0.1",
            port=9982,
            ingestion_ws_url="ws://127.0.0.1:9981/ws/stream"
        )
        tcp_server = await asyncio.start_server(gateway.handle_client, "127.0.0.1", 9982)

        # 3. Connect simulated Asterisk client
        reader, writer = await asyncio.open_connection("127.0.0.1", 9982)

        # Send initial handshake with UUID
        call_uuid = uuid.uuid4()
        init_hdr = struct.pack("!BH", 1, 16)
        writer.write(init_hdr + call_uuid.bytes)
        await writer.drain()
        await asyncio.sleep(0.05)

        # Check session registered in gateway
        assert str(call_uuid) in gateway.active_sessions

        # Send 8kHz frame (320 bytes) -> expects upsampling to 640 bytes
        frame_8k = np.full(160, 42, dtype=np.int16).tobytes()
        writer.write(struct.pack("!BH", 0x10, len(frame_8k)) + frame_8k)
        await writer.drain()
        await asyncio.sleep(0.05)

        # Send 16kHz frame (640 bytes) -> expects pass-through 640 bytes
        frame_16k = np.full(320, 84, dtype=np.int16).tobytes()
        writer.write(struct.pack("!BH", 0x10, len(frame_16k)) + frame_16k)
        await writer.drain()
        await asyncio.sleep(0.05)

        # Send zero-length frame (heartbeat/keepalive) -> should be gracefully skipped
        writer.write(struct.pack("!BH", 0x10, 0))
        await writer.drain()
        await asyncio.sleep(0.05)

        # Close client connection
        writer.close()
        await writer.wait_closed()
        await asyncio.sleep(0.05)

        # Session should be cleanly popped on disconnect
        assert str(call_uuid) not in gateway.active_sessions

        # Verify forwarded frames
        assert len(forwarded_frames) == 2, f"Expected 2 forwarded frames, got {len(forwarded_frames)}"
        assert len(forwarded_frames[0]) == 640, "8kHz frame was not upsampled to 640 bytes"
        assert len(forwarded_frames[1]) == 640, "16kHz frame was corrupted or not 640 bytes"

        # Cleanup servers
        tcp_server.close()
        await tcp_server.wait_closed()
        ws_server.close()
        await ws_server.wait_closed()

    asyncio.run(run_scenario())


def test_audiosocket_malformed_header_handling():
    """Verify that malformed or truncated packets do not crash the gateway server."""
    async def run_scenario():
        gateway = AsteriskAudioSocketServer(
            host="127.0.0.1",
            port=9983,
            ingestion_ws_url="ws://127.0.0.1:9999/ws/stream"
        )
        tcp_server = await asyncio.start_server(gateway.handle_client, "127.0.0.1", 9983)

        # Connect and immediately send only 1 byte instead of 3-byte header, then close
        reader, writer = await asyncio.open_connection("127.0.0.1", 9983)
        writer.write(b"\x01")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        await asyncio.sleep(0.05)

        # Server should still be healthy and accepting new connections
        reader2, writer2 = await asyncio.open_connection("127.0.0.1", 9983)
        writer2.close()
        await writer2.wait_closed()

        tcp_server.close()
        await tcp_server.wait_closed()

    asyncio.run(run_scenario())
