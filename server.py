import requests
from flask import Flask, render_template_string
from urllib.parse import urlparse
import threading
import time
import socket

VLESS_LIST_URL = "https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_lite.txt"
UPDATE_INTERVAL = 30  # секунд
PING_TIMEOUT = 2  # секунд
VLESS_PORT_DEFAULT = 443
MAX_PING = 500  # миллисекунд

app = Flask(__name__)
working_vless = []   # [(uri, ping_ms)]
lock = threading.Lock()

def check_vless_ping(vless_uri):
    try:
        # uri: vless://[uuid]@[host]:[port]?params
        parsed = urlparse(vless_uri)
        if parsed.scheme != 'vless':
            return None
        host = parsed.hostname
        port = parsed.port or VLESS_PORT_DEFAULT

        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(PING_TIMEOUT)
        res = sock.connect_ex((host, port))
        ping = int((time.time() - start) * 1000)
        sock.close()
        if res == 0:
            return ping
        return None
    except Exception:
        return None

def update_vless_list():
    global working_vless
    while True:
        try:
            r = requests.get(VLESS_LIST_URL)
            lines = [line.strip() for line in r.text.strip().split('\n') if line.strip()]
        except Exception:
            lines = []
        result = []
        for uri in lines:
            ping = check_vless_ping(uri)
            if ping is not None and ping <= MAX_PING:
                result.append((uri, ping))
        with lock:
            working_vless = result
        time.sleep(UPDATE_INTERVAL)

@app.route("/")
def index():
    with lock:
        vless_lines = [v[0] for v in working_vless]
    # Однострочные ключи, автообновление
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Working Vless List</title>
      <meta http-equiv="refresh" content="30">
      <style>
        body { font-family: monospace; background: #181F20; color: #B8C0C2; }
        pre { font-size: 16px; }
      </style>
    </head>
    <body>
      <h2>Рабочие Vless с низким пингом (&lt;500ms)</h2>
      <pre>
      {% for vless in vless_lines %}
{{ vless }}
      {% endfor %}
      </pre>
      <p>auto refresh / автообновление</p>
    </body>
    </html>
    """
    return render_template_string(html, vless_lines=vless_lines)

if __name__ == "__main__":
    threading.Thread(target=update_vless_list, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)