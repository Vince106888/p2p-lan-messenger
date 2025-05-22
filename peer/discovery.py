import socket
import threading
import json
import time

BROADCAST_IP = '255.255.255.255'
PORT = 9999
DISCOVERY_INTERVAL = 2
BUFFER_SIZE = 1024

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

class PeerDiscovery:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.ip = get_local_ip()
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.send_beacons, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def send_beacons(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            message = json.dumps({
                'type': 'HELLO',
                'peer_id': self.peer_id,
                'ip': self.ip
            })
            sock.sendto(message.encode(), (BROADCAST_IP, PORT))
            time.sleep(DISCOVERY_INTERVAL)

    def listen_for_peers(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', PORT))

        while self.running:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                peer_data = json.loads(data.decode())
                if peer_data.get('type') == 'HELLO' and peer_data.get('peer_id') != self.peer_id:
                    print(f"[DISCOVERY] Found peer: {peer_data}")
            except Exception as e:
                print(f"[ERROR] {e}")
