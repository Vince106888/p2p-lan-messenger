import socket
import threading

PORT = 8888  # Chat/message port
BUFFER_SIZE = 1024

class PeerMessenger:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.running = False

    def start_server(self):
        self.running = True
        thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        thread.start()

    def stop_server(self):
        self.running = False

    def listen_for_messages(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('', PORT))
        server_sock.listen(5)

        print(f"[MESSENGER] Listening for incoming messages on port {PORT}...")

        while self.running:
            try:
                client_sock, addr = server_sock.accept()
                data = client_sock.recv(BUFFER_SIZE).decode()
                print(f"\n[MESSAGE] From {addr[0]} → {data}")
                client_sock.close()
            except Exception as e:
                print(f"[ERROR] Message receive error: {e}")

    def send_message(self, peer_ip, message):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((peer_ip, PORT))
            full_msg = f"{self.peer_id}: {message}"
            sock.sendall(full_msg.encode())
            sock.close()
            print(f"[SENT] Message sent to {peer_ip}")
        except Exception as e:
            print(f"[ERROR] Could not send message to {peer_ip}: {e}")
