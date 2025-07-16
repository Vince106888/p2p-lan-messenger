# group_collaboration.py
import os
import uuid

class GroupManager:
    def __init__(self):
        self.groups = {}  # group_id -> {name, members, roles, threads}

    def create_group(self, name, creator_id):
        group_id = str(uuid.uuid4())[:8]
        self.groups[group_id] = {
            "name": name,
            "members": {creator_id},
            "roles": {creator_id: "admin"},
            "threads": {}
        }
        return group_id

    def join_group(self, group_id, user_id):
        if group_id in self.groups:
            self.groups[group_id]["members"].add(user_id)
            if user_id not in self.groups[group_id]["roles"]:
                self.groups[group_id]["roles"][user_id] = "viewer"

    def set_role(self, group_id, user_id, role):
        if group_id in self.groups:
            self.groups[group_id]["roles"][user_id] = role

    def get_role(self, group_id, user_id):
        return self.groups[group_id]["roles"].get(user_id, "viewer")

    def get_groups(self):
        return self.groups


class ThreadManager:
    def __init__(self):
        self.threads = {}  # thread_id -> {title, creator, messages}

    def create_thread(self, group, title, creator_id):
        thread_id = str(uuid.uuid4())[:8]
        group["threads"][thread_id] = {
            "title": title,
            "creator": creator_id,
            "messages": []
        }
        return thread_id

    def post_message(self, group, thread_id, user_id, content):
        if thread_id in group["threads"]:
            group["threads"][thread_id]["messages"].append({
                "user": user_id,
                "content": content
            })

    def get_thread(self, group, thread_id):
        return group["threads"].get(thread_id)


class AttachmentStore:
    def __init__(self):
        self.attachments = {}  # thread_id -> list of (filename, data, is_file)
        os.makedirs("attachments", exist_ok=True)

    def add_note_attachment(self, thread_id, filename, note):
        if thread_id not in self.attachments:
            self.attachments[thread_id] = []
        self.attachments[thread_id].append((filename, note, False))

    def add_file_attachment(self, thread_id, filepath):
        if thread_id not in self.attachments:
            self.attachments[thread_id] = []
        filename = os.path.basename(filepath)
        dest_path = os.path.join("attachments", filename)
        with open(filepath, 'rb') as f_in, open(dest_path, 'wb') as f_out:
            f_out.write(f_in.read())
        self.attachments[thread_id].append((filename, dest_path, True))

    def get_attachments(self, thread_id):
        return self.attachments.get(thread_id, [])
