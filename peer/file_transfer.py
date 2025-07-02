import socket
import threading
import os
from peer.crypto_utils import (
    generate_private_key,
    generate_public_key,
    compute_shared_key,
    aes_encrypt,
    aes_decrypt
)

PORT = 9000
BUFFER_SIZE = 4096

class SecureFileReceiver:
    def __init__(self):
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.listen, daemon=True).start()

    def stop(self):
        self.running = False

    def listen(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', PORT))
        server.listen(1)
        print(f"[RECEIVER] Listening on port {PORT} for incoming encrypted file transfers...")

        while self.running:
            conn, addr = server.accept()
            print(f"[RECEIVER] Connection from {addr}")

            try:
                # 🔐 Step 1: Diffie-Hellman Key Exchange
                private_key = generate_private_key()
                public_key = generate_public_key(private_key)

                peer_pub_key = int(conn.recv(BUFFER_SIZE).decode())
                conn.send(str(public_key).encode())

                shared_key = compute_shared_key(peer_pub_key, private_key)

                # 📦 Step 2: Receive filename
                filename_size = int(conn.recv(4).decode())
                filename = conn.recv(filename_size).decode()

                # 📂 Step 3: Receive encrypted file
                encrypted_data = b''
                while True:
                    chunk = conn.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    encrypted_data += chunk

                plaintext = aes_decrypt(shared_key, encrypted_data)

                # 🗂️ Save to 'received_files/' folder
                save_dir = "received_files"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"received_{filename}")

                with open(save_path, 'wb') as f:
                    f.write(plaintext)

                print(f"[RECEIVER] File saved as: {save_path}")
            except Exception as e:
                print(f"[ERROR] Failed to receive file: {e}")
            finally:
                conn.close()


def send_file(peer_ip, filepath):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((peer_ip, PORT))
    print(f"[SENDER] Connected to {peer_ip}:{PORT}")

    try:
        # 🔐 Step 1: Diffie-Hellman Key Exchange
        private_key = generate_private_key()
        public_key = generate_public_key(private_key)

        sock.send(str(public_key).encode())
        peer_pub_key = int(sock.recv(BUFFER_SIZE).decode())

        shared_key = compute_shared_key(peer_pub_key, private_key)

        # 📦 Step 2: Send filename
        filename = os.path.basename(filepath)
        encoded_name = filename.encode()
        sock.send(str(len(encoded_name)).zfill(4).encode())  # 4-digit length
        sock.send(encoded_name)

        # 📂 Step 3: Encrypt and send file
        with open(filepath, 'rb') as f:
            data = f.read()

        encrypted = aes_encrypt(shared_key, data)
        sock.sendall(encrypted)

        print(f"[SENDER] File '{filename}' sent securely to {peer_ip}")
    except Exception as e:
        print(f"[ERROR] Failed to send file: {e}")
    finally:
        sock.close()
