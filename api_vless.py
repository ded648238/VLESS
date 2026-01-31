import requests
from urllib.parse import urlparse
import socket
import time

VLESS_LIST_URL = "https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_lite.txt"
MAX_PING_MS = 500
CHECK_SERVERS_LIMIT = 5     # Не более 5 серверов за один вызов - иначе timeout на Vercel
SOCKET_TIMEOUT = 0.5        # 500 мс

def check_tcp_ping(uri):
    try:
        parsed = urlparse(uri)
        host = parsed.hostname
        port = parsed.port or 443
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        result = sock.connect_ex((host, port))
        ping = int((time.time() - start) * 1000)
        sock.close()
        if result == 0 and ping <= MAX_PING_MS:
            return ping
    except Exception:
        return None
    return None

def handler(request, response):
    # Vercel Python API expects this function signature
    try:
        r = requests.get(VLESS_LIST_URL, timeout=3)
        vless_uris = [line.strip() for line in r.text.strip().split('\n') if line.startswith('vless://')]
        result = []
        for uri in vless_uris[:CHECK_SERVERS_LIMIT]:   # Проверяем только несколько, иначе timeout
            ping = check_tcp_ping(uri)
            if ping is not None:
                result.append(f"{uri}  # ping: {ping} ms")
        content = "\n".join(result)
        response.status_code = 200
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.body = content
    except Exception as e:
        response.status_code = 500
        response.body = f"FAIL: {str(e)}"