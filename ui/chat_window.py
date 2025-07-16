import tkinter as tk
from tkinter import scrolledtext, simpledialog
import time

class ChatWindow:
    def __init__(self, master, peer_ip, peer_name, send_callback):
        self.peer_ip = peer_ip
        self.peer_name = peer_name
        self.send_callback = send_callback

        self.window = tk.Toplevel(master)
        self.window.title(f"Chat with {peer_name} ({peer_ip})")
        self.window.geometry("450x400")

        self.chat_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state='disabled')
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')

        self.entry = tk.Entry(self.window)
        self.entry.pack(side=tk.LEFT, padx=(10, 5), pady=(0, 10), fill='x', expand=True)

        self.send_button = tk.Button(self.window, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(5, 10), pady=(0, 10))

        self.entry.bind('<Return>', lambda e: self.send_message())

    def log_message(self, sender, message, tag=None):
        timestamp = time.strftime('%H:%M')
        formatted = f"[{timestamp}] {sender}: {message}"
        if tag:
            formatted += f"   📎 {tag}"
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, formatted + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

    def send_message(self):
        message = self.entry.get().strip()
        if not message:
            return
        tag = simpledialog.askstring("Tag (Optional)", "Enter a context tag (e.g., Assignment, Notes):", parent=self.window)
        self.send_callback(self.peer_ip, message, tag)
        self.log_message("You", message, tag)
        self.entry.delete(0, tk.END)

    def focus(self):
        self.window.deiconify()
        self.window.lift()
        self.entry.focus()
