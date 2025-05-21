# main.py

from peer.discovery import PeerDiscovery
import uuid

if __name__ == '__main__':
    peer_id = str(uuid.uuid4())[:8]  # Short random ID
    print(f"Starting P2P node: {peer_id}")

    discovery = PeerDiscovery(peer_id)
    discovery.start()

    try:
        while True:
            pass  # Main loop placeholder
    except KeyboardInterrupt:
        print("\nShutting down...")
