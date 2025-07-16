import socket
import threading
import json
import time

PORT = 9999
DISCOVERY_INTERVAL = 2
BUFFER_SIZE = 1024

def get_local_ip():
    """
    Returns the local IP address of the current machine.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use a dummy connection to Google's DNS to get our IP
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

def get_broadcast_ip():
    """
    Returns the broadcast address based on the current subnet.
    Example: for 192.168.1.5 → returns 192.168.1.255
    """
    ip = get_local_ip()
    parts = ip.split('.')
    parts[-1] = '255'
    return '.'.join(parts)

class PeerDiscovery:
    def __init__(self, peer_id, username):  # ✅ Updated to accept username
        self.peer_id = peer_id
        self.username = username
        self.ip = get_local_ip()
        self.broadcast_ip = get_broadcast_ip()
        self.running = False
        self.peers = {}  # {peer_id: {"ip": ..., "last_seen": ..., "username": ...}}

    def start(self):
        self.running = True
        threading.Thread(target=self.send_beacons, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def stop(self):
        self.running = False

    def send_beacons(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            message = json.dumps({
                'type': 'HELLO',
                'peer_id': self.peer_id,
                'ip': self.ip,
                'username': self.username  # ✅ Include username
            })

            try:
                sock.sendto(message.encode(), (self.broadcast_ip, PORT))
                print(f"[BEACON] Sent → {self.broadcast_ip}:{PORT} | {message}")
            except Exception as e:
                print(f"[ERROR] Failed to send beacon: {e}")

            time.sleep(DISCOVERY_INTERVAL)

    def listen_for_peers(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', PORT))

        print(f"[LISTENING] UDP {PORT} for peer broadcasts...")

        while self.running:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                peer_data = json.loads(data.decode())

                if (
                    peer_data.get('type') == 'HELLO'
                    and peer_data.get('peer_id') != self.peer_id
                ):
                    peer_id = peer_data['peer_id']
                    peer_ip = peer_data['ip']
                    username = peer_data.get('username', 'Unknown')

                    # Update or add peer
                    self.peers[peer_id] = {
                        'ip': peer_ip,
                        'last_seen': time.time(),
                        'username': username
                    }

                    print(f"[DISCOVERY] Found peer: {username} ({peer_id}) @ {peer_ip}")
            except Exception as e:
                print(f"[ERROR] Discovery receive failed: {e}")
