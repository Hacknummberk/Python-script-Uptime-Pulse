# Uptime Pulse

**Live server health monitoring dashboard with a modern, responsive UI**

A lightweight Python tool that continuously checks your server endpoints / URLs, measures response time & status, and displays real-time results in a beautiful, auto-refreshing browser dashboard.

Features modern cards, status animations (breathing green dot on OK), theme switch (dark/light), settings modal, subtle fade-in effects, and a strong disclaimer to keep things legally chill.

Perfect for personal projects, homelab monitoring, small APIs, or just making sure your morning coffee server is still alive ☕→🟢

![Server Pulse screenshot](https://via.placeholder.com/800x500/161b22/60a5fa?text=Server+Pulse+Dashboard+Example)  
*(Replace with real screenshot later)*

## Features

- Periodic HTTP checks (GET) with timeout & redirect handling
- Color-coded status: green (200–399), yellow (redirects), red (errors/4xx/5xx/timeouts)
- Shows response time (ms), content size (KB), status code + reason
- Modern card-based UI with pulse animation on healthy endpoints
- Responsive design — looks good on desktop & mobile
- Settings modal: theme switch, refresh interval display, optional error beep
- Auto-refresh via `<meta refresh>` (simple & zero JS polling)
- Tiny built-in web server — access from any device on your network
- Keeps history of recent checks (last \~80 entries)
- Strong "AS IS" disclaimer in footer (no liability — monitor responsibly!)

## Requirements

- Python 3.8+
- Only one external package:

```bash
pip install requests
