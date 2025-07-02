import socket
import threading
import os

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

PORT = 9998
BUFFER_SIZE = 4096

class SecureFileReceiver:
    def __init__(self, app=None):
        self.running = False
        self.app = app  # Reference to GUI app for logging

    def start(self):
        self.running = True
        threading.Thread(target=self.listen_for_files, daemon=True).start()
        if self.app:
            self.app.log("[RECEIVER] Secure file receiver started on port 9998")
        else:
            print("[RECEIVER] Secure file receiver started on port 9998")

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
                if self.app:
                    self.app.log(f"[RECEIVER ERROR] {e}")
                else:
                    print(f"[RECEIVER ERROR] {e}")

    def handle_connection(self, conn, addr):
        try:
            # Receive filename length, then filename
            filename_len = int.from_bytes(conn.recv(2), 'big')
            filename = conn.recv(filename_len).decode()

            # Receive encrypted key and IV
            key = conn.recv(32)  # AES-256 key
            iv = conn.recv(16)

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

            msg = f"[RECEIVED] File '{filename}' from {addr[0]} saved to 'received_files/'"
            if self.app:
                self.app.log(msg)
            else:
                print(msg)

        except Exception as e:
            if self.app:
                self.app.log(f"[RECEIVER ERROR] {e}")
            else:
                print(f"[RECEIVER ERROR] {e}")
        finally:
            conn.close()


def send_file(ip, filepath):
    try:
        filename = os.path.basename(filepath)
        key = get_random_bytes(32)
        iv = get_random_bytes(16)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        with open(filepath, 'rb') as f:
            plaintext = f.read()
        encrypted_data = cipher.encrypt(pad(plaintext, AES.block_size))

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, PORT))
            sock.send(len(filename.encode()).to_bytes(2, 'big'))
            sock.send(filename.encode())
            sock.send(key)
            sock.send(iv)
            sock.sendall(encrypted_data)

    except Exception as e:
        raise e
