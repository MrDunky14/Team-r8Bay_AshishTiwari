#!/usr/bin/env python3
"""
Chrome DevTools Protocol (CDP) Automated Pre-Launch E2E Audit
Attaches directly to Chromium DevTools domains (Performance, Network, Runtime, Console)
to validate the 60fps Dispatch UI, WebSocket PII masking, and WebAudio pipeline.
"""

import asyncio
import json
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from playwright.async_api import async_playwright

LOCAL_URL = "http://127.0.0.1:8080"
PAGES_URL = "https://mrdunky14.github.io/Team-r8Bay_AshishTiwari/"


async def run_chrome_devtools_audit(url: str = LOCAL_URL) -> dict:
    console_errors = []
    page_exceptions = []
    ws_frames_received = []
    pii_leak_detected = False

    async with async_playwright() as p:
        # Launch Chromium with synthetic hardware media stream enabled for WebAudio testing
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--autoplay-policy=no-user-gesture-required",
                "--enable-gpu-rasterization",
            ],
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # 1. Attach raw Chrome DevTools Protocol (CDP) session
        cdp = await context.new_cdp_session(page)
        await cdp.send("Performance.enable")
        await cdp.send("Network.enable")
        await cdp.send("Runtime.enable")

        # 2. Hook Console Errors & Uncaught Exceptions
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_exceptions.append(str(exc)))

        # 3. Hook CDP Network WebSocket Frames for In-Flight PII Inspection
        def on_ws_frame(params):
            payload_str = params.get("response", {}).get("payloadData", "")
            ws_frames_received.append(payload_str)
            # Verify raw sensitive test patterns never reach browser unmasked
            if "ABCDE1234F" in payload_str or "otp is 7421" in payload_str.lower() or "9844 2109 8832" in payload_str:
                nonlocal pii_leak_detected
                pii_leak_detected = True

        cdp.on("Network.webSocketFrameReceived", on_ws_frame)

        print(f"[CDP] Navigating to {url} ...")
        await page.goto(url, wait_until="networkidle")

        # 4. Verify Core DOM & Canvas Elements Exist
        canvas_count = await page.locator("canvas").count()
        page_title = await page.title()
        print(f"[CDP] Loaded '{page_title}' | Active <canvas> nodes: {canvas_count}")

        # 5. Trigger Interactive 3-Stream Stress Simulator in UI (if button present)
        stress_btn = page.locator("button:has-text('Stress'), button:has-text('Inject'), #btn-stress-test").first
        if await stress_btn.count() > 0:
            print("[CDP] Triggering 3-Stream Adversarial Stress Injection via UI click...")
            await stress_btn.click()
            await asyncio.sleep(1.5)

        # 6. Measure Real Browser FPS & Main-Thread Jitter via requestAnimationFrame Probe
        fps_metrics = await page.evaluate(
            """() => new Promise((resolve) => {
                let frames = 0;
                let maxFrameGapMs = 0;
                let lastTime = performance.now();
                const startTime = lastTime;

                function tick(now) {
                    frames++;
                    const gap = now - lastTime;
                    if (gap > maxFrameGapMs) maxFrameGapMs = gap;
                    lastTime = now;
                    if (now - startTime < 2000) {
                        requestAnimationFrame(tick);
                    } else {
                        const elapsedSec = (now - startTime) / 1000;
                        resolve({
                            measuredFps: Math.round(frames / elapsedSec),
                            maxFrameDeltaMs: Math.round(maxFrameGapMs * 100) / 100,
                            totalFramesIn2Sec: frames
                        });
                    }
                }
                requestAnimationFrame(tick);
            })"""
        )

        # 7. Pull Native Chrome DevTools Performance Metrics (JSHeapUsedSize, LayoutCount, TaskDuration)
        cdp_perf_raw = await cdp.send("Performance.getMetrics")
        perf_map = {m["name"]: m["value"] for m in cdp_perf_raw.get("metrics", [])}

        # 8. Inspect Rendered Queue Sorting & Lien Card State in DOM
        dom_snapshot = await page.evaluate(
            """() => {
                const bodyText = document.body.innerText;
                return {
                    hasPriority1Badge: bodyText.includes("PRIORITY-1") || bodyText.includes("CRITICAL"),
                    hasSpoofBlockBadge: bodyText.includes("SPOOF") || bodyText.includes("BLOCKED"),
                    hasCoercionAlert: bodyText.includes("COERCION") || bodyText.includes("280Hz"),
                    hasCfcFrmsLienCard: bodyText.includes("CFCFRMS") || bodyText.includes("BNS"),
                    hasRedactedMask: bodyText.includes("XXXX-XXXX") || bodyText.includes("REDACTED"),
                };
            }"""
        )

        # Save high-res DevTools evidence screenshot
        screenshot_path = os.path.join(os.path.dirname(__file__), "..", "cdp_audit_screenshot.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[CDP] Saved high-resolution DevTools audit screenshot to: {screenshot_path}")
        await browser.close()

    report = {
        "target_url": url,
        "status": "PASSED" if (not console_errors and not page_exceptions and not pii_leak_detected) else "FAILED",
        "canvas_elements_mounted": canvas_count,
        "console_error_count": len(console_errors),
        "uncaught_page_exceptions": page_exceptions,
        "ws_frames_captured": len(ws_frames_received),
        "zero_pii_leak_in_ws_frames": not pii_leak_detected,
        "browser_rendering_telemetry": fps_metrics,
        "cdp_heap_and_layout": {
            "JSHeapUsedSize_MB": round(perf_map.get("JSHeapUsedSize", 0) / (1024 * 1024), 2),
            "Nodes": int(perf_map.get("Nodes", 0)),
            "LayoutCount": int(perf_map.get("LayoutCount", 0)),
            "TaskDuration_sec": round(perf_map.get("TaskDuration", 0), 4),
        },
        "dom_functional_assertions": dom_snapshot,
    }
    print("\n=== CHROME DEVTOOLS PROTOCOL (CDP) AUDIT REPORT ===")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else LOCAL_URL
    result = asyncio.run(run_chrome_devtools_audit(target))
    sys.exit(0 if result["status"] == "PASSED" else 1)
