import socket
import threading
import json
import time

BROADCAST_IP = '255.255.255.255'
PORT = 9999
DISCOVERY_INTERVAL = 2
BUFFER_SIZE = 1024
STALE_TIMEOUT = 5  # Seconds

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
        self.peers = {}  # {peer_id: {'ip': ip, 'last_seen': timestamp}}

    def start(self):
        self.running = True
        threading.Thread(target=self.send_beacons, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
        threading.Thread(target=self.cleanup_peers, daemon=True).start()

    def stop(self):
        self.running = False

    def send_beacons(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            message = json.dumps({
                'type': 'HELLO',
                'peer_id': self.peer_id,
                'ip': self.ip
            })
            print(f"[BEACON] Broadcasting: {message}")
            sock.sendto(message.encode(), (BROADCAST_IP, PORT))
            time.sleep(DISCOVERY_INTERVAL)

    def listen_for_peers(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', PORT))
        sock.settimeout(1.0)

        while self.running:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                peer_data = json.loads(data.decode())
                if peer_data.get('type') == 'HELLO' and peer_data.get('peer_id') != self.peer_id:
                    peer_id = peer_data['peer_id']
                    self.peers[peer_id] = {
                        'ip': peer_data['ip'],
                        'last_seen': time.time()
                    }
                    print(f"[DISCOVERY] {peer_id} @ {peer_data['ip']}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] Listening error: {e}")

    def cleanup_peers(self):
        while self.running:
            now = time.time()
            stale = [pid for pid, info in self.peers.items()
                     if now - info['last_seen'] > STALE_TIMEOUT]
            for pid in stale:
                print(f"[TIMEOUT] Removing inactive peer: {pid}")
                del self.peers[pid]
            time.sleep(1)
