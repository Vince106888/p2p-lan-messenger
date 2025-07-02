import socket
import threading

PORT = 8888
BUFFER_SIZE = 1024

class PeerMessenger:
    def __init__(self, peer_id, app=None):
        self.peer_id = peer_id
        self.app = app
        self.running = False

    def start_server(self):
        self.running = True
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        if self.app:
            self.app.log("[MESSENGER] Message server started on port 8888")
        else:
            print("[MESSENGER] Message server started on port 8888")

    def stop_server(self):
        self.running = False

    def listen_for_messages(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", PORT))
        sock.listen(5)

        while self.running:
            try:
                conn, addr = sock.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.app:
                    self.app.log(f"[MESSAGE ERROR] {e}")
                else:
                    print(f"[MESSAGE ERROR] {e}")

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(BUFFER_SIZE)
            message = data.decode()
            msg = f"[MESSAGE RECEIVED] From {addr[0]}: {message}"
            if self.app:
                self.app.log(msg)
            else:
                print(msg)
        except Exception as e:
            if self.app:
                self.app.log(f"[MESSAGE ERROR] {e}")
            else:
                print(f"[MESSAGE ERROR] {e}")
        finally:
            conn.close()

    def send_message(self, ip, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, PORT))
                sock.sendall(message.encode())
        except Exception as e:
            if self.app:
                self.app.log(f"[SEND ERROR] Could not send message to {ip}: {e}")
            else:
                print(f"[SEND ERROR] Could not send message to {ip}: {e}")