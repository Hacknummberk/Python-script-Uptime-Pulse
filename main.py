#!/usr/bin/env python3

# Server response tester → modern responsive HTML dashboard

import time
import threading
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from pathlib import Path
import socket

# ==================== CONFIG ====================
TEST_URLS = [
    "https://httpbin.org/get",
    "https://www.google.com",
    "https://api.github.com",
    "https://httpstat.us/200",
    "https://httpstat.us/503",
    # Add your real endpoints here
] 

INTERVAL_SECONDS = 12 
HTML_FILE = "server-monitor.html" # dude dont change this shit
PORT = 8089 # port
# ================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Server Health • Live Monitor</title>
  <meta http-equiv="refresh" content="{refresh}"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
  <style>
    :root {{
      --bg: #0f1217;
      --card: #161b22;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --border: #30363d;
      --green: #22c55e;
      --yellow: #f59e0b;
      --red: #ef4444;
      --gray: #6b7280;
    }}

    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, sans-serif;
      padding: 1.5rem;
      line-height: 1.5;
    }}

    header {{
      margin-bottom: 1.5rem;
      text-align: center;
    }}

    h1 {{
      font-size: 1.8rem;
      font-weight: 600;
      color: #60a5fa;
      margin-bottom: 0.5rem;
    }}

    .meta {{
      color: var(--text-muted);
      font-size: 0.9rem;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 1rem;
    }}

    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
      transition: transform 0.08s ease;
    }}

    .card:hover {{
      transform: translateY(-2px);
    }}

    .status-line {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }}

    .status-dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }}

    .ok    .status-dot {{ background: var(--green); }}
    .warn  .status-dot {{ background: var(--yellow); }}
    .error .status-dot {{ background: var(--red);   }}

    .status-text {{
      font-weight: 600;
      font-size: 1.1rem;
    }}

    .url {{
      font-family: ui-monospace, monospace;
      font-size: 0.92rem;
      color: #60a5fa;
      word-break: break-all;
      margin-bottom: 0.75rem;
    }}

    .details {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.4rem 1rem;
      font-size: 0.9rem;
      color: var(--text-muted);
    }}

    .details dt {{
      font-weight: 500;
      color: #cbd5e1;
    }}

    .time {{
      font-size: 0.82rem;
      color: var(--text-muted);
      text-align: right;
      margin-top: 1rem;
      border-top: 1px solid var(--border);
      padding-top: 0.75rem;
    }}

    @media (max-width: 600px) {{
      body {{ padding: 1rem; }}
      h1 {{ font-size: 1.5rem; }}
      .grid {{ grid-template-columns: 1fr; }}
      .card {{ padding: 1rem; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Server Health Monitor</h1>
    <div class="meta">
      Updated <strong id="clock">{now}</strong> • every {interval}s
    </div>
  </header>

  <div class="container">
    <div class="grid">
      {cards}
    </div>
  </div>

  <script>
    // Simple live clock update (cosmetic)
    function updateClock() {{
      const el = document.getElementById('clock');
      if (!el) return;
      const now = new Date();
      el.textContent = now.toLocaleString('en-GB', {{
        year:'numeric', month:'short', day:'2-digit',
        hour:'2-digit', minute:'2-digit', second:'2-digit'
      }}).replace(',', '');
    }}
    setInterval(updateClock, 1000);
    updateClock();
  </script>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="card {cls}">
  <div class="status-line">
    <div class="status-dot"></div>
    <span class="status-text">{status}</span>
  </div>
  <div class="url">{url}</div>
  <dl class="details">
    <dt>Response</dt><dd>{time_ms} ms</dd>
    <dt>Size</dt>   <dd>{size_kb} KB</dd>
    {note_line}
  </dl>
  <div class="time">{time}</div>
</div>
"""

def test_endpoint(url, timeout=10):
    t0 = time.time()
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        ms = round((time.time() - t0) * 1000)
        kb = len(r.content) // 1024 if r.content else 0
        cls = "ok" if r.ok else "error" if r.status_code >= 400 else "warn"
        status = f"{r.status_code} {r.reason}"
        note = "" if r.ok else r.reason or str(r.elapsed)
        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "status": status,
            "time_ms": ms,
            "size_kb": kb,
            "cls": cls,
            "note": note[:90]
        }
    except Exception as e:
        ms = round((time.time() - t0) * 1000, 1)
        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "status": "ERROR",
            "time_ms": ms,
            "size_kb": 0,
            "cls": "error",
            "note": str(e)[:90]
        }


def generate_html(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cards = []

    for res in results:
        note_line = f"<dt>Message</dt><dd>{res['note']}</dd>" if res['note'] else ""
        cards.append(CARD_TEMPLATE.format(
            cls=res["cls"],
            status=res["status"],
            url=res["url"],
            time_ms=res["time_ms"],
            size_kb=res["size_kb"],
            note_line=note_line,
            time=res["time"]
        ))

    html = HTML_TEMPLATE.format(
        refresh=INTERVAL_SECONDS + 2,
        now=now,
        interval=INTERVAL_SECONDS,
        cards="".join(cards)
    )

    Path(HTML_FILE).write_text(html, encoding="utf-8")


def tester_loop():
    history = []
    print("Starting monitor...")
    print(f" → Open:  http://localhost:{PORT}/{HTML_FILE}")
    print(f" → or     http://{get_local_ip()}:{PORT}/{HTML_FILE}\n")

    while True:
        for url in TEST_URLS:
            print(f"Testing {url} ... ", end="", flush=True)
            result = test_endpoint(url)
            history.append(result)
            print(f"{result['status']}  ({result['time_ms']} ms)")

        # Keep only last \~60–80 entries (adjust as needed)
        history = history[-80:]
        generate_html(history)
        time.sleep(INTERVAL_SECONDS)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    Path(HTML_FILE).write_text("Initializing...", encoding="utf-8")

    # Web server in background
    server = HTTPServer(('0.0.0.0', PORT), SilentHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"Web server → http://localhost:{PORT}")
    print("-" * 50)

    try:
        tester_loop()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()
# use it in right way if you hack and get caught i don't take any responsibility because it just open source 
# ask for permission to use this on other websites or you will end up getting arrested 
# dude i dont know
