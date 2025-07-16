# === main.py ===
import os
import time
import uuid
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
from tkinter import ttk

from peer.discovery import PeerDiscovery
from peer.messaging import PeerMessenger
from peer.file_transfer import SecureFileReceiver, send_file
from auth.authentication import AuthManager
from ui.group_ui import GroupTab

os.makedirs("logs", exist_ok=True)
os.makedirs("received_files", exist_ok=True)

logging.basicConfig(
    filename='logs/p2p.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class P2PGUI:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.peer_id = str(uuid.uuid4())[:8]

        self.root.title(f"🚀 P2P LAN Messenger – {self.username}")
        self.root.geometry("900x600")
        center_window(self.root)

        self.discovery = PeerDiscovery(self.peer_id, self.username)
        self.messenger = PeerMessenger(self.peer_id, self)
        self.receiver = SecureFileReceiver(self)

        self.discovery.start()
        self.build_ui()
        self.messenger.start_server()
        self.receiver.start()

        self.refresh_peers_loop()
        logging.info(f"[SYSTEM] Peer {self.peer_id} ({self.username}) started with IP {self.discovery.ip}")

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        tk.Label(self.root, text="🚀 P2P LAN Messenger", font=("Segoe UI", 18, "bold"), fg="#234e70").pack(pady=(10, 0))
        tk.Label(self.root, text=f"User: {self.username} | Peer ID: {self.peer_id}", font=("Segoe UI", 11), fg="gray").pack(pady=(0, 8))

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill="both", padx=12, pady=5)

        peers_tab = ttk.Frame(notebook)
        self.peer_listbox = tk.Listbox(peers_tab, width=90, height=18, font=("Courier New", 10))
        self.peer_listbox.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(peers_tab)
        btn_frame.pack(pady=(0, 10))

        ttk.Button(btn_frame, text="✉️ Open Chat", command=self.open_chat_window).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="📁 Send File", command=self.send_file_gui).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_peers_gui).grid(row=0, column=2, padx=10)

        notebook.add(peers_tab, text="📡 Peers")

        logs_tab = ttk.Frame(notebook)
        self.log_area = scrolledtext.ScrolledText(logs_tab, height=20, width=95, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)
        notebook.add(logs_tab, text="📜 Logs")

        group_tab = ttk.Frame(notebook)
        self.group_tab = GroupTab(group_tab, self.peer_id, self.log)
        self.group_tab.refresh_groups()
        notebook.add(group_tab, text="📚 Groups")

        self.status_var = tk.StringVar()
        self.update_status()
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w', font=("Segoe UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self):
        peer_count = len(self.discovery.peers)
        self.status_var.set(f"🌐 IP: {self.discovery.ip}   |   Peers Online: {peer_count}")

    def log(self, text):
        timestamp = time.strftime('%H:%M:%S')
        message = f"{timestamp} - {text}"
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)
        logging.info(text)

    def refresh_peers_gui(self):
        self.peer_listbox.delete(0, tk.END)
        sorted_peers = sorted(self.discovery.peers.items(), key=lambda x: x[1].get('username', ''))
        for pid, info in sorted_peers:
            age = round(time.time() - info['last_seen'], 1)
            name = info.get('username', 'Unknown')
            self.peer_listbox.insert(tk.END, f"{name} ({pid}) @ {info['ip']} (seen {age}s ago)")
        self.update_status()

    def refresh_peers_loop(self):
        self.refresh_peers_gui()
        self.root.after(5000, self.refresh_peers_loop)

    def get_selected_peer_ip(self):
        selection = self.peer_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Peer Selected", "Please select a peer from the list.")
            return None
        selected = self.peer_listbox.get(selection[0])
        ip = selected.split('@')[1].split('(')[0].strip()
        return ip

    def open_chat_window(self):
        peer_ip = self.get_selected_peer_ip()
        if not peer_ip:
            return
        peer_name = self.get_peer_name(peer_ip)
        self.messenger.open_chat(peer_ip, peer_name)
        self.log(f"[CHAT] Opened chat with {peer_name} @ {peer_ip}")

    def get_peer_name(self, ip):
        for pid, info in self.discovery.peers.items():
            if info['ip'] == ip:
                return info.get('username', 'Unknown')
        return "Unknown"

    def send_file_gui(self):
        peer_ip = self.get_selected_peer_ip()
        if not peer_ip:
            return
        filepath = filedialog.askopenfilename(title="Select File to Send")
        if filepath:
            try:
                start_time = time.time()
                send_file(peer_ip, filepath, gui_app=self)
                duration = round(time.time() - start_time, 2)
                filename = os.path.basename(filepath)
                self.log(f"File '{filename}' sent to {peer_ip} in {duration}s.")
            except Exception as e:
                self.log(f"[ERROR] Failed to send file: {e}")
                messagebox.showerror("File Send Error", str(e))

    def prompt_file_accept(self, sender_ip, filename):
        return messagebox.askyesno("Incoming File", f"{sender_ip} wants to send you '{filename}'. Accept?")

def center_window(root):
    root.update_idletasks()
    width, height = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

def run_gui():
    auth = AuthManager()
    root = tk.Tk()
    username = None

    while not username:
        action = messagebox.askquestion("Login/Register", "Do you want to log in? (No = Register)")
        if action == "yes":
            u = simpledialog.askstring("Login", "Enter username:")
            p = simpledialog.askstring("Password", "Enter password:", show="*")
            if auth.login_user(u, p):
                username = u
                messagebox.showinfo("Login Successful", f"Welcome back, {u}!")
            else:
                messagebox.showerror("Login Failed", "Incorrect credentials or IP mismatch.")
        else:
            u = simpledialog.askstring("Register", "Choose a username:")
            p = simpledialog.askstring("Register", "Choose a password:", show="*")
            if auth.register_user(u, p):
                username = u
                messagebox.showinfo("Registration Complete", f"Welcome, {u}!")
            else:
                messagebox.showerror("Registration Error", "Username already exists.")

    app = P2PGUI(root, username)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(app, root))
    root.mainloop()

def on_close(app, root):
    logging.info("[SYSTEM] Peer shutting down.")
    app.discovery.stop()
    app.messenger.stop_server()
    app.receiver.stop()
    root.destroy()

if __name__ == "__main__":
    run_gui()
