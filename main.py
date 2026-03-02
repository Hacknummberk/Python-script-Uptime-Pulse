#!/usr/bin/env python3
"""
Server Health Monitor — Pulse (or whatever name you pick)
Modern responsive dashboard with live checks + settings modal

# Joke: Why do programmers prefer dark mode? 
#       Because light attracts bugs... and downtime is already scary enough! 🐛💀

DISCLAIMER (shown in footer):
This tool is provided "AS IS" without any warranties. 
Use at your own risk. The author takes NO responsibility 
for any damage, data loss, missed alerts, false positives, 
server explosions (metaphorical or literal), or hurt feelings.
Not liable for anything — ever. Happy monitoring!
"""

import time
import threading
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from pathlib import Path
import socket
import json

# ==================== CONFIG ====================
TEST_URLS = [
    "https://httpbin.org/get",
    "https://www.google.com",
    "https://api.github.com",
    "https://httpstat.us/200",
    "https://httpstat.us/503",
    # add your endpoints
]

DEFAULT_INTERVAL = 12
HTML_FILE = "server-pulse.html"
PORT = 8089
# ================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Server Pulse • Live Health</title>
  <meta http-equiv="refresh" content="{refresh}"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
  <style>
    :root {{
      --bg: #0f1217;
      --card: #161b22;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --border: #30363d;
      --green: #22c55e;
      --yellow: #f59e0b;
      --red: #ef4444;
      --accent: #60a5fa;
    }}
    [data-theme="light"] {{
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #1e293b;
      --muted: #64748b;
      --border: #e2e8f0;
    }}

    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, sans-serif;
      padding: 1.5rem 1rem;
      min-height: 100vh;
      transition: background 0.4s;
    }}

    header {{
      text-align: center;
      margin: 0 0 2rem;
    }}

    h1 {{
      font-size: clamp(1.6rem, 5vw, 2.2rem);
      font-weight: 700;
      color: var(--accent);
    }}

    .meta {{
      color: var(--muted);
      font-size: 0.95rem;
      margin-top: 0.4rem;
    }}

    .btn-settings {{
      position: fixed;
      top: 1rem;
      right: 1rem;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.6rem 1rem;
      border-radius: 8px;
      cursor: pointer;
      z-index: 100;
      font-weight: 500;
    }}

    .container {{
      max-width: 1280px;
      margin: 0 auto;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.25rem;
    }}

    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.4rem;
      box-shadow: 0 6px 12px rgba(0,0,0,0.15);
      opacity: 0;
      transform: translateY(15px);
      animation: fadeInUp 0.5s forwards;
      transition: transform 0.2s ease, box-shadow 0.2s;
    }}

    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }}

    @keyframes fadeInUp {{
      to {{ opacity:1; transform:translateY(0); }}
    }}

    .status-line {{
      display: flex;
      align-items: center;
      gap: 0.9rem;
      margin-bottom: 1rem;
    }}

    .status-dot {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      flex-shrink: 0;
      box-shadow: 0 0 0 rgba(34,197,94,0.4);
    }}

    .ok    .status-dot {{ 
      background: var(--green); 
      animation: pulse 2.5s infinite ease-in-out; 
    }}
    .warn  .status-dot {{ background: var(--yellow); }}
    .error .status-dot {{ background: var(--red);    }}

    @keyframes pulse {{
      0%,100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.5); }}
      50%     {{ box-shadow: 0 0 0 10px rgba(34,197,94,0); }}
    }}

    .status-text {{
      font-weight: 600;
      font-size: 1.15rem;
    }}

    .url {{
      font-family: ui-monospace, monospace;
      font-size: 0.94rem;
      color: var(--accent);
      word-break: break-all;
      margin-bottom: 1rem;
    }}

    .details {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.5rem 1.2rem;
      font-size: 0.92rem;
      color: var(--muted);
    }}

    .details dt {{ font-weight: 500; color: var(--text); }}

    .time {{
      margin-top: 1.2rem;
      font-size: 0.84rem;
      color: var(--muted);
      text-align: right;
      border-top: 1px solid var(--border);
      padding-top: 0.8rem;
    }}

    /* Modal */
    .modal {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.7);
      z-index: 200;
      align-items: center;
      justify-content: center;
    }}

    .modal-content {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.8rem;
      max-width: 420px;
      width: 90%;
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }}

    .modal h2 {{
      margin-bottom: 1.2rem;
      color: var(--accent);
    }}

    label {{
      display: block;
      margin: 1rem 0 0.4rem;
      font-weight: 500;
    }}

    select, input[type="checkbox"] {{
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.5rem;
      border-radius: 6px;
    }}

    .close-btn {{
      float: right;
      background: none;
      border: none;
      font-size: 1.4rem;
      cursor: pointer;
      color: var(--muted);
    }}

    footer {{
      margin-top: 3rem;
      text-align: center;
      font-size: 0.8rem;
      color: var(--muted);
      line-height: 1.6;
    }}

    @media (max-width: 600px) {{
      .grid {{ gap: 1rem; }}
      .card {{ padding: 1.2rem; }}
    }}
  </style>
</head>
<body>

  <button class="btn-settings" onclick="openSettings()"><i class="fas fa-cog"></i> Settings</button>

  <header>
    <h1>Server Pulse</h1>
    <div class="meta">
      Last check: <strong id="clock">{now}</strong> • every <span id="interval-display">{interval}</span>s
    </div>
  </header>

  <div class="container">
    <div class="grid" id="grid">
      {cards}
    </div>
  </div>

  <!-- Settings Modal -->
  <div class="modal" id="settingsModal">
    <div class="modal-content">
      <button class="close-btn" onclick="closeSettings()">×</button>
      <h2>Settings</h2>

      <label>Theme</label>
      <select id="themeSelect" onchange="changeTheme(this.value)">
        <option value="dark">Dark (default)</option>
        <option value="light">Light</option>
      </select>

      <label>Refresh Interval</label>
      <select id="intervalSelect" onchange="updateInterval(this.value)">
        <option value="8">8 seconds (fast)</option>
        <option value="12" selected>12 seconds</option>
        <option value="20">20 seconds</option>
        <option value="60">60 seconds (chill)</option>
      </select>

      <label>
        <input type="checkbox" id="alertSound" onchange="toggleAlert(this.checked)">
        Play beep on error (needs first click permission)
      </label>

      <p style="margin-top:1.5rem; font-size:0.9rem; color:var(--muted);">
        Changes apply after next refresh or page reload.
      </p>
    </div>
  </div>

  <footer>
    <p><strong>DISCLAIMER:</strong> This tool is provided "AS IS" without any warranties, express or implied.<br>
    Use at your own risk. The author takes NO responsibility and is NOT LIABLE for any damage,<br>
    data loss, missed alerts, false readings, server issues, financial loss, emotional distress,<br>
    or any other consequence — direct, indirect, incidental, or otherwise.<br>
    Monitor responsibly. Servers will still go down sometimes. ¯\\_(ツ)_/¯</p>
  </footer>

  <script>
    // Clock
    function updateClock() {{
      document.getElementById('clock').textContent = new Date().toLocaleString('en-GB', {{
        year:'numeric', month:'short', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit'
      }}).replace(',','');
    }}
    setInterval(updateClock, 1000);
    updateClock();

    // Modal
    function openSettings() {{ document.getElementById('settingsModal').style.display = 'flex'; }}
    function closeSettings() {{ document.getElementById('settingsModal').style.display = 'none'; }}

    // Theme
    function changeTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    }}

    // Fake interval display (real refresh still meta refresh)
    function updateInterval(val) {{
      document.getElementById('interval-display').textContent = val;
      localStorage.setItem('interval', val);
    }}

    // Sound (very basic beep — needs user gesture first time)
    let audioCtx = null;
    function toggleAlert(enabled) {{
      if (enabled && !audioCtx) {{
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }}
      localStorage.setItem('alertSound', enabled);
    }}

    function playErrorBeep() {{
      if (localStorage.getItem('alertSound') !== 'true' || !audioCtx) return;
      const osc = audioCtx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(400, audioCtx.currentTime);
      osc.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.15);
    }}

    // Auto-load saved settings
    window.addEventListener('load', () => {{
      const savedTheme = localStorage.getItem('theme') || 'dark';
      document.documentElement.setAttribute('data-theme', savedTheme);
      document.getElementById('themeSelect').value = savedTheme;

      const savedInterval = localStorage.getItem('interval') || '{interval}';
      document.getElementById('intervalSelect').value = savedInterval;
      document.getElementById('interval-display').textContent = savedInterval;

      const savedAlert = localStorage.getItem('alertSound') === 'true';
      document.getElementById('alertSound').checked = savedAlert;
      if (savedAlert) toggleAlert(true);
    }});

    // If you want sound on error you could call playErrorBeep() after checking new results,
    // but since we use meta refresh it's tricky — left as optional exercise :)
  </script>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="card {cls}" style="animation-delay: {delay}s;">
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
        note = "" if r.ok else (r.reason or str(r.elapsed))[:100]
        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "status": status,
            "time_ms": ms,
            "size_kb": kb,
            "cls": cls,
            "note": note
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
            "note": str(e)[:100]
        }


def generate_html(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cards = []

    for i, res in enumerate(results):
        note_line = f"<dt>Message</dt><dd>{res['note']}</dd>" if res['note'] else ""
        delay = min(i * 0.08, 1.0)  # stagger fade-in
        cards.append(CARD_TEMPLATE.format(
            cls=res["cls"],
            status=res["status"],
            url=res["url"],
            time_ms=res["time_ms"],
            size_kb=res["size_kb"],
            note_line=note_line,
            time=res["time"],
            delay=delay
        ))

    html = HTML_TEMPLATE.format(
        refresh=DEFAULT_INTERVAL + 2,
        now=now,
        interval=DEFAULT_INTERVAL,
        cards="".join(cards)
    )
    Path(HTML_FILE).write_text(html, encoding="utf-8")


def tester_loop():
    history = []
    print("Server Pulse started...")
    print(f" → Dashboard: http://localhost:{PORT}/{HTML_FILE}")
    print(f" → Network : http://{get_local_ip()}:{PORT}/{HTML_FILE}\n")

    while True:
        new_results = []
        for url in TEST_URLS:
            print(f"→ {url} ... ", end="", flush=True)
            res = test_endpoint(url)
            new_results.append(res)
            print(f"{res['status']} ({res['time_ms']} ms)")

        history.extend(new_results)
        history = history[-80:]           # keep recent ones
        generate_html(history)
        time.sleep(DEFAULT_INTERVAL)


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
    Path(HTML_FILE).write_text("Starting Server Pulse...", encoding="utf-8")

    server = HTTPServer(('0.0.0.0', PORT), SilentHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print(f"Web server → http://localhost:{PORT}")
    print("-" * 60)

    try:
        tester_loop()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        server.shutdown()
