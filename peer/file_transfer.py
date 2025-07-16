import socket
import threading
import os
import time

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

PORT = 9998
BUFFER_SIZE = 4096

class SecureFileReceiver:
    def __init__(self, app=None):
        self.running = False
        self.app = app

    def start(self):
        self.running = True
        threading.Thread(target=self.listen_for_files, daemon=True).start()
        self._log("[RECEIVER] Secure file receiver started on port 9998")

    def stop(self):
        self.running = False

    def listen_for_files(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", PORT))
        sock.listen(5)

        while self.running:
            try:
                conn, addr = sock.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                self._log(f"[RECEIVER ERROR] {e}")

    def handle_connection(self, conn, addr):
        try:
            filename_len = int.from_bytes(conn.recv(2), 'big')
            filename = conn.recv(filename_len).decode()

            key = conn.recv(32)
            iv = conn.recv(16)

            if self.app:
                confirm = self.app.prompt_file_accept(addr[0], filename)
                if not confirm:
                    self._log(f"[REJECTED] File '{filename}' from {addr[0]} was rejected.")
                    conn.close()
                    return

            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted_data = b""

            while True:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                encrypted_data += chunk

            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

            os.makedirs("received_files", exist_ok=True)
            save_path = os.path.join("received_files", filename)
            with open(save_path, 'wb') as f:
                f.write(decrypted_data)

            self._log(f"[RECEIVED] '{filename}' saved from {addr[0]} ➜ 'received_files/'")
            conn.send(b"RECEIVED")

        except Exception as e:
            self._log(f"[RECEIVER ERROR] {e}")
        finally:
            conn.close()

    def _log(self, text):
        if self.app:
            self.app.log(text)
        else:
            print(text)

def send_file(ip, filepath, gui_app=None):
    try:
        filename = os.path.basename(filepath)
        key = get_random_bytes(32)
        iv = get_random_bytes(16)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        with open(filepath, 'rb') as f:
            plaintext = f.read()
        encrypted_data = cipher.encrypt(pad(plaintext, AES.block_size))
        total_size = len(encrypted_data)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, PORT))

            sock.send(len(filename.encode()).to_bytes(2, 'big'))
            sock.send(filename.encode())
            sock.send(key)
            sock.send(iv)

            sent = 0
            while sent < total_size:
                chunk = encrypted_data[sent:sent + BUFFER_SIZE]
                sock.send(chunk)
                sent += len(chunk)

                if gui_app:
                    progress = round((sent / total_size) * 100, 1)
                    gui_app.status_var.set(f"🚀 Sending '{filename}' to {ip}... {progress}%")
                    gui_app.root.update_idletasks()

            ack = sock.recv(10).decode()
            if ack == "RECEIVED":
                if gui_app:
                    gui_app.log(f"[ACK] {ip} confirmed file delivery of '{filename}'")
            else:
                if gui_app:
                    gui_app.log(f"[WARN] No confirmation received for '{filename}'")

            if gui_app:
                gui_app.status_var.set("✅ Idle")

    except Exception as e:
        if gui_app:
            gui_app.log(f"[FILE SEND ERROR] {e}")
            gui_app.status_var.set("❌ File send failed")
        raise e
