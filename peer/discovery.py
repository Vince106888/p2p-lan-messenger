# peer/discovery.py

import struct
import socket
import threading
import json
import time
from .config import MULTICAST_GROUP, MULTICAST_PORT, DISCOVERY_INTERVAL, BUFFER_SIZE

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect
        s.connect(('10.255.255.255', 1))
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
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        while self.running:
            message = json.dumps({
                'type': 'HELLO',
                'peer_id': self.peer_id,
                'ip': self.ip
            })
            sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
            time.sleep(DISCOVERY_INTERVAL)

    def listen_for_peers(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MULTICAST_PORT))

        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton(self.ip)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while self.running:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                peer_data = json.loads(data.decode())
                if peer_data.get('type') == 'HELLO' and peer_data.get('peer_id') != self.peer_id:
                    print(f"[DISCOVERY] Found peer: {peer_data}")
            except Exception as e:
                print(f"[ERROR] {e}")
