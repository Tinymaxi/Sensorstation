#!/usr/bin/env python3
"""Inject drag-to-scroll JS into Grafana via Chrome DevTools Protocol."""

import json
import asyncio
import websockets
import urllib.request
import time

JS_CODE = '''(function() {
    var sv = document.querySelectorAll(".scrollbar-view");
    var scrollEl = null;
    for (var i = 0; i < sv.length; i++) {
        if (sv[i].scrollHeight > 1000) { scrollEl = sv[i]; break; }
    }
    if (!scrollEl) return "no scroll element";
    var startY, startScroll, dragging = false;
    scrollEl.addEventListener("mousedown", function(e) {
        dragging = true;
        startY = e.clientY;
        startScroll = scrollEl.scrollTop;
    });
    document.addEventListener("mousemove", function(e) {
        if (!dragging) return;
        scrollEl.scrollTop = startScroll + (startY - e.clientY);
        e.preventDefault();
    });
    document.addEventListener("mouseup", function() {
        dragging = false;
    });
    return "OK scrollH=" + scrollEl.scrollHeight;
})()'''


async def inject(ws_url):
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": JS_CODE}
        }))
        resp = json.loads(await ws.recv())
        result = resp.get("result", {}).get("result", {}).get("value", "error")
        print("inject-touch-scroll: {}".format(result))


# Retry a few times in case page is still loading
for attempt in range(5):
    try:
        data = urllib.request.urlopen("http://localhost:9222/json").read()
        pages = json.loads(data)
        ws_url = pages[0]["webSocketDebuggerUrl"]
        asyncio.get_event_loop().run_until_complete(inject(ws_url))
        break
    except Exception as e:
        print("inject-touch-scroll: attempt {} failed: {}".format(attempt + 1, e))
        time.sleep(5)
