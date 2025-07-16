# group_ui.py
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, scrolledtext
from peer.group_collaboration import GroupManager, ThreadManager, AttachmentStore

class GroupTab:
    def __init__(self, root, peer_id, logger):
        self.root = root
        self.peer_id = peer_id
        self.log = logger

        self.groups = GroupManager()
        self.threads = ThreadManager()
        self.attachments = AttachmentStore()

        self.selected_group_id = None
        self.selected_thread_id = None

        self.build_ui()

    def build_ui(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # === Left: Groups ===
        group_frame = tk.Frame(container)
        group_frame.pack(side="left", fill="y")

        tk.Label(group_frame, text="Groups").pack()
        self.group_list = tk.Listbox(group_frame, height=15, width=25)
        self.group_list.pack()
        self.group_list.bind("<<ListboxSelect>>", self.on_group_select)

        tk.Button(group_frame, text="Create Group", command=self.create_group).pack(pady=2)
        tk.Button(group_frame, text="Join Group", command=self.join_group).pack(pady=2)

        # === Middle: Threads ===
        thread_frame = tk.Frame(container)
        thread_frame.pack(side="left", fill="y")

        tk.Label(thread_frame, text="Threads").pack()
        self.thread_list = tk.Listbox(thread_frame, height=15, width=30)
        self.thread_list.pack()
        self.thread_list.bind("<<ListboxSelect>>", self.on_thread_select)

        self.new_thread_btn = tk.Button(thread_frame, text="New Thread", command=self.create_thread)
        self.new_thread_btn.pack(pady=2)

        # === Right: Messages + Input ===
        msg_frame = tk.Frame(container)
        msg_frame.pack(side="left", fill="both", expand=True)

        self.thread_title = tk.Label(msg_frame, text="Select a thread", font=("Arial", 12, "bold"))
        self.thread_title.pack(pady=4)

        self.msg_view = scrolledtext.ScrolledText(msg_frame, height=15, state="disabled")
        self.msg_view.pack(fill="both", expand=True)

        self.msg_entry = tk.Text(msg_frame, height=3)
        self.msg_entry.pack(fill="x", pady=5)

        action_frame = tk.Frame(msg_frame)
        action_frame.pack()

        self.send_btn = tk.Button(action_frame, text="Send", command=self.post_message)
        self.send_btn.grid(row=0, column=0, padx=5)

        tk.Button(action_frame, text="Attach File", command=self.attach_file).grid(row=0, column=1, padx=5)
        tk.Button(action_frame, text="Attach Note", command=self.attach_note).grid(row=0, column=2, padx=5)

    def refresh_groups(self):
        self.group_list.delete(0, tk.END)
        for gid, g in self.groups.get_groups().items():
            self.group_list.insert(tk.END, f"{g['name']} ({gid})")

    def on_group_select(self, event):
        selection = self.group_list.curselection()
        if not selection:
            return
        line = self.group_list.get(selection[0])
        gid = line.split("(")[-1][:-1]
        self.selected_group_id = gid
        self.refresh_threads()

    def refresh_threads(self):
        self.thread_list.delete(0, tk.END)
        group = self.groups.groups.get(self.selected_group_id)
        if not group:
            return
        for tid, t in group["threads"].items():
            self.thread_list.insert(tk.END, f"{t['title']} ({tid})")

    def on_thread_select(self, event):
        selection = self.thread_list.curselection()
        if not selection:
            return
        line = self.thread_list.get(selection[0])
        tid = line.split("(")[-1][:-1]
        self.selected_thread_id = tid
        self.show_thread()

    def show_thread(self):
        group = self.groups.groups.get(self.selected_group_id)
        thread = group["threads"].get(self.selected_thread_id)
        self.thread_title.config(text=thread["title"])

        self.msg_view.configure(state="normal")
        self.msg_view.delete("1.0", tk.END)
        for msg in thread["messages"]:
            self.msg_view.insert(tk.END, f"{msg['user']}: {msg['content']}\n")

        # Show attachments
        for name, data, is_file in self.attachments.get_attachments(self.selected_thread_id):
            label = f"📎 {name} (file)" if is_file else f"📝 {name}"
            self.msg_view.insert(tk.END, f"{label}\n")

        self.msg_view.configure(state="disabled")

    def create_group(self):
        name = simpledialog.askstring("New Group", "Enter group name:")
        if name:
            gid = self.groups.create_group(name, self.peer_id)
            self.log(f"[GROUP] Created group '{name}' ({gid})")
            self.refresh_groups()

    def join_group(self):
        gid = simpledialog.askstring("Join Group", "Enter group ID:")
        if gid:
            self.groups.join_group(gid, self.peer_id)
            self.log(f"[GROUP] Joined group {gid}")
            self.refresh_groups()

    def create_thread(self):
        if not self.selected_group_id:
            return
        group = self.groups.groups[self.selected_group_id]
        role = self.groups.get_role(self.selected_group_id, self.peer_id)
        if role not in ["admin", "contributor"]:
            messagebox.showwarning("Permission Denied", "You are not allowed to create threads.")
            return

        title = simpledialog.askstring("New Thread", "Enter thread title:")
        if title:
            tid = self.threads.create_thread(group, title, self.peer_id)
            self.log(f"[THREAD] Created thread '{title}' in group {self.selected_group_id}")
            self.refresh_threads()

    def post_message(self):
        if not self.selected_group_id or not self.selected_thread_id:
            return
        role = self.groups.get_role(self.selected_group_id, self.peer_id)
        if role not in ["admin", "contributor"]:
            messagebox.showwarning("Permission Denied", "You are not allowed to post messages.")
            return

        text = self.msg_entry.get("1.0", tk.END).strip()
        if text:
            group = self.groups.groups[self.selected_group_id]
            self.threads.post_message(group, self.selected_thread_id, self.peer_id, text)
            self.msg_entry.delete("1.0", tk.END)
            self.show_thread()

    def attach_note(self):
        if not self.selected_thread_id:
            return
        title = simpledialog.askstring("Attach Note", "Note title:")
        content = simpledialog.askstring("Note Content", "Enter the note:")
        if title and content:
            self.attachments.add_note_attachment(self.selected_thread_id, title, content)
            self.log(f"[ATTACHMENT] Note '{title}' added to thread {self.selected_thread_id}")
            self.show_thread()

    def attach_file(self):
        if not self.selected_thread_id:
            return
        filepath = filedialog.askopenfilename(title="Select File")
        if filepath:
            self.attachments.add_file_attachment(self.selected_thread_id, filepath)
            self.log(f"[ATTACHMENT] File '{os.path.basename(filepath)}' attached to thread {self.selected_thread_id}")
            self.show_thread()
