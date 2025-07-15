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

# Setup directories and logs
os.makedirs("logs", exist_ok=True)
os.makedirs("received_files", exist_ok=True)

logging.basicConfig(
    filename='logs/p2p.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class P2PGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 P2P LAN Messenger")
        self.root.geometry("800x560")
        center_window(self.root)

        self.peer_id = str(uuid.uuid4())[:8]
        self.discovery = PeerDiscovery(self.peer_id)
        self.messenger = PeerMessenger(self.peer_id, self)
        self.receiver = SecureFileReceiver(self)

        self.discovery.start()
        self.build_ui()  # Build UI before any log calls
        self.messenger.start_server()
        self.receiver.start()

        self.refresh_peers_loop()
        logging.info(f"[SYSTEM] Peer {self.peer_id} started with IP {self.discovery.ip}")

    def build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Header
        header = tk.Label(self.root, text="🚀 P2P LAN Messenger", font=("Arial", 16, "bold"), fg="#24527a")
        header.pack(pady=(10, 2))

        subheader = tk.Label(self.root, text=f"Peer ID: {self.peer_id}", font=("Arial", 11), fg="gray")
        subheader.pack(pady=(0, 8))

        # Notebook Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # Peers Tab
        peers_tab = ttk.Frame(notebook)
        self.peer_listbox = tk.Listbox(peers_tab, width=90, height=15, font=("Courier", 10))
        self.peer_listbox.pack(padx=10, pady=10)

        btn_frame = tk.Frame(peers_tab)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="✉️ Send Message", command=self.send_message_gui).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="📁 Send File", command=self.send_file_gui).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_peers_gui).grid(row=0, column=2, padx=10)

        notebook.add(peers_tab, text="📡 Peers")

        # Logs Tab
        logs_tab = ttk.Frame(notebook)
        self.log_area = scrolledtext.ScrolledText(logs_tab, height=20, width=95, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=10)
        notebook.add(logs_tab, text="📜 Logs")

        # Status Bar
        self.status_var = tk.StringVar()
        self.update_status()
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self):
        peer_count = len(self.discovery.peers)
        self.status_var.set(f"🌐 Your IP: {self.discovery.ip}   |   Peers online: {peer_count}")

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
        for pid, info in self.discovery.peers.items():
            age = round(time.time() - info['last_seen'], 1)
            self.peer_listbox.insert(tk.END, f"{pid} @ {info['ip']} (seen {age}s ago)")
        self.update_status()

    def refresh_peers_loop(self):
        self.refresh_peers_gui()
        self.root.after(5000, self.refresh_peers_loop)

    def get_selected_peer_ip(self):
        selection = self.peer_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Peer", "Please select a peer.")
            return None
        selected = self.peer_listbox.get(selection[0])
        ip = selected.split('@')[1].split('(')[0].strip()
        return ip

    def send_message_gui(self):
        peer_ip = self.get_selected_peer_ip()
        if not peer_ip:
            return
        message = simpledialog.askstring("Send Message", "Enter your message:")
        if message:
            self.messenger.send_message(peer_ip, message)
            self.log(f"Sent message to {peer_ip}: {message}")

    def send_file_gui(self):
        peer_ip = self.get_selected_peer_ip()
        if not peer_ip:
            return
        filepath = filedialog.askopenfilename(title="Choose File to Send")
        if filepath:
            try:
                start_time = time.time()
                send_file(peer_ip, filepath)
                duration = round(time.time() - start_time, 2)
                filename = os.path.basename(filepath)
                self.log(f"Sent file '{filename}' to {peer_ip} in {duration} seconds.")
            except Exception as e:
                self.log(f"[ERROR] Failed to send file: {e}")
                messagebox.showerror("File Send Error", str(e))

# Utility to center the window
def center_window(root):
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

def run_gui():
    root = tk.Tk()
    # Optional: set custom icon
    # root.iconphoto(False, tk.PhotoImage(file='assets/icon.png'))
    app = P2PGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(app, root))
    root.mainloop()

def on_close(app, root):
    logging.info("[SYSTEM] Peer shutting down.")
    app.discovery.stop()
    app.messenger.stop_server()
    app.receiver.stop()
    root.destroy()

if __name__ == '__main__':
    run_gui()
