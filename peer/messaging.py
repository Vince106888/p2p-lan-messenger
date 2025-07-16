import socket
import threading
import time

from ui.chat_window import ChatWindow

PORT = 8888
BUFFER_SIZE = 1024

class PeerMessenger:
    def __init__(self, peer_id, app=None):
        self.peer_id = peer_id
        self.app = app
        self.running = False
        self.chat_windows = {}  # {ip: ChatWindow}
        self.message_queue = {}  # {ip: [(msg, tag)]}

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
                self.app.log(f"[MESSAGE ERROR] {e}")

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                return

            parts = data.decode().split("||")
            message, tag = parts[0], (parts[1] if len(parts) > 1 else None)

            ip = addr[0]
            sender = self.get_peer_name(ip)
            self.open_chat(ip, sender)
            self.chat_windows[ip].log_message(sender, message, tag)

            log_msg = f"[MESSAGE RECEIVED] From {sender} ({ip}): {message}"
            if tag:
                log_msg += f"  📎 {tag}"
            self.app.log(log_msg)

        except Exception as e:
            self.app.log(f"[MESSAGE ERROR] {e}")
        finally:
            conn.close()

    def send_message(self, ip, message, tag=None):
        try:
            payload = f"{message}||{tag or ''}"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, PORT))
                sock.sendall(payload.encode())
        except Exception as e:
            self.app.log(f"[SEND ERROR] Could not send to {ip}: {e}")
            self.queue_message(ip, message, tag)

    def queue_message(self, ip, message, tag=None):
        self.message_queue.setdefault(ip, []).append((message, tag))
        self.app.log(f"[QUEUE] Message queued for {ip} until they reconnect.")

    def deliver_queued_messages(self, ip):
        if ip in self.message_queue:
            for message, tag in self.message_queue[ip]:
                self.send_message(ip, message, tag)
            del self.message_queue[ip]
            self.app.log(f"[DELIVERED] Queued messages sent to {ip}")

    def open_chat(self, ip, name):
        if ip not in self.chat_windows:
            self.chat_windows[ip] = ChatWindow(
                master=self.app.root,
                peer_ip=ip,
                peer_name=name,
                send_callback=self.send_message
            )
        self.chat_windows[ip].focus()

    def get_peer_name(self, ip):
        for pid, info in self.app.discovery.peers.items():
            if info['ip'] == ip:
                return info.get('username', 'Unknown')
        return "Unknown"
