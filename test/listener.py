# listener.py
import socket
import json
from datetime import datetime

PORT = 9999
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', PORT))

print(f"Listening for UDP packets on port {PORT}...\n")

try:
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            payload = json.loads(data.decode())
            print(f"[{timestamp}] {addr[0]}:{addr[1]} →\n{json.dumps(payload, indent=2)}\n")
        except json.JSONDecodeError:
            print(f"[{timestamp}] {addr[0]}:{addr[1]} → {data.decode()}")
except KeyboardInterrupt:
    print("\nListener terminated.")
    sock.close()
