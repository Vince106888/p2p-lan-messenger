import os
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from secrets import randbelow

# Simple Diffie-Hellman params
PRIME = 2**127 - 1  # Use a large safe prime
GENERATOR = 2

def generate_private_key():
    return randbelow(PRIME)

def generate_public_key(private_key):
    return pow(GENERATOR, private_key, PRIME)

def compute_shared_key(peer_pub_key, private_key):
    shared_secret = pow(peer_pub_key, private_key, PRIME)
    # Derive AES key (256-bit) using SHA256
    return hashlib.sha256(str(shared_secret).encode()).digest()

def aes_encrypt(key, plaintext):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    return iv + ciphertext  # Prepend IV

def aes_decrypt(key, data):
    iv = data[:16]
    ciphertext = data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)
