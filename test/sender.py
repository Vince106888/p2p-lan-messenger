# sender.py
import socket
import json
from datetime import datetime

BROADCAST_IP = '255.255.255.255'
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

message = {
    "type": "HELLO",
    "peer_id": "test_peer",
    "ip": "192.168.1.123"  # Simulated/fake IP
}

payload = json.dumps(message)
timestamp = datetime.now().strftime("%H:%M:%S")
print(f"[{timestamp}] Broadcasting test peer to {BROADCAST_IP}:{PORT}")
print(json.dumps(message, indent=2))

sock.sendto(payload.encode(), (BROADCAST_IP, PORT))
sock.close()
