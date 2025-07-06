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

# ─────────────── Setup logs ───────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("received_files", exist_ok=True)

logging.basicConfig(
    filename='logs/p2p.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─────────────── GUI Application ───────────────
class P2PGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 P2P LAN Messenger")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        self.peer_id = str(uuid.uuid4())[:8]
        self.discovery = PeerDiscovery(self.peer_id)
        self.messenger = PeerMessenger(self.peer_id, self)
        self.receiver = SecureFileReceiver(self)

        self.discovery.start()
        self.build_ui()
        self.messenger.start_server()
        self.receiver.start()

        self.refresh_peers_loop()

        logging.info(f"[SYSTEM] Peer {self.peer_id} started with IP {self.discovery.ip}")

    def build_ui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)

        tk.Label(top_frame, text=f"Your Peer ID: {self.peer_id}", fg="blue", font=("Arial", 12, "bold")).pack()

        self.peer_listbox = tk.Listbox(self.root, width=80, height=10, font=("Courier", 10))
        self.peer_listbox.pack(padx=10, pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="✉️ Send Message", command=self.send_message_gui).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="📁 Send File", command=self.send_file_gui).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="🔄 Refresh Peers", command=self.refresh_peers_gui).grid(row=0, column=2, padx=10)

        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill='x', pady=10)

        tk.Label(self.root, text="📜 Logs", font=("Arial", 11, "bold")).pack()
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, width=85, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=5)

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
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                filename = os.path.basename(filepath)
                self.log(f"Sent file '{filename}' to {peer_ip} in {duration} seconds.")
            except Exception as e:
                self.log(f"[ERROR] Failed to send file: {e}")
                messagebox.showerror("File Send Error", str(e))


def run_gui():
    root = tk.Tk()
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
