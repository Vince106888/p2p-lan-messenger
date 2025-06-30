import socket
import threading
import os
from peer.crypto_utils import (
    generate_private_key, generate_public_key, compute_shared_key,
    aes_encrypt, aes_decrypt
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
        print(f"[RECEIVER] Listening for secure file transfers on port {PORT}")

        while self.running:
            conn, addr = server.accept()
            print(f"[RECEIVER] Connection from {addr}")

            # Step 1: Perform Diffie-Hellman
            private_key = generate_private_key()
            public_key = generate_public_key(private_key)

            peer_pub_key = int(conn.recv(BUFFER_SIZE).decode())
            conn.send(str(public_key).encode())

            shared_key = compute_shared_key(peer_pub_key, private_key)

            # Step 2: Receive file name
            filename_size = int(conn.recv(4).decode())
            filename = conn.recv(filename_size).decode()

            # Step 3: Receive encrypted file data
            encrypted_data = b''
            while True:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                encrypted_data += chunk

            plaintext = aes_decrypt(shared_key, encrypted_data)
            with open("received_" + filename, 'wb') as f:
                f.write(plaintext)

            print(f"[RECEIVER] File received: received_{filename}")

            conn.close()

def send_file(peer_ip, filepath):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((peer_ip, PORT))
    print(f"[SENDER] Connected to {peer_ip}:{PORT}")

    # 🔐 Step 1: Perform DH key exchange
    private_key = generate_private_key()
    public_key = generate_public_key(private_key)

    sock.send(str(public_key).encode())
    peer_pub_key = int(sock.recv(BUFFER_SIZE).decode())
    shared_key = compute_shared_key(peer_pub_key, private_key)

    # 📦 Step 2: Send filename
    filename = os.path.basename(filepath)
    encoded_name = filename.encode()
    sock.send(str(len(encoded_name)).zfill(4).encode())  # Send 4-digit length (e.g. 0012)
    sock.send(encoded_name)

    # 📂 Step 3: Encrypt and send file
    with open(filepath, 'rb') as f:
        data = f.read()

    encrypted = aes_encrypt(shared_key, data)
    sock.sendall(encrypted)
    sock.close()

    print(f"[SENDER] File '{filename}' sent securely to {peer_ip}")
