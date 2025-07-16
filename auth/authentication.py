import os
import json
import bcrypt
import socket

AUTH_DB_FILE = "auth/users.json"

# Ensure storage directory exists
os.makedirs(os.path.dirname(AUTH_DB_FILE), exist_ok=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class AuthManager:
    def __init__(self):
        self.db_file = AUTH_DB_FILE
        self.ip = get_local_ip()
        self.load_users()

    def load_users(self):
        if not os.path.exists(self.db_file):
            self.users = {}
        else:
            with open(self.db_file, "r") as f:
                self.users = json.load(f)

    def save_users(self):
        with open(self.db_file, "w") as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def register_user(self, username: str, password: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = {
            "password": self.hash_password(password),
            "ip": self.ip
        }
        self.save_users()
        return True

    def login_user(self, username: str, password: str) -> bool:
        user = self.users.get(username)
        if not user:
            return False
        if user["ip"] != self.ip:
            return False
        return self.verify_password(password, user["password"])
