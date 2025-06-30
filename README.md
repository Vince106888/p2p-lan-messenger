# 🛰️ P2P LAN Messenger

A decentralized, peer-to-peer LAN messaging and file-sharing system with end-to-end encryption.

> 🔐 Built with Python, Tkinter GUI, AES encryption, and Diffie-Hellman key exchange.

---

## 🚀 Features

- ✅ Peer discovery over LAN (UDP broadcast)
- ✅ Secure messaging over TCP
- ✅ Encrypted file transfer using AES (CBC) + Diffie-Hellman key exchange
- ✅ Simple and intuitive GUI (Tkinter)
- ✅ Auto-refreshing peer list
- ✅ Logs and error reporting

---

## 📸 GUI Preview

![Screenshot Placeholder](https://via.placeholder.com/800x400?text=GUI+Preview+Coming+Soon)

---

## 🧠 How It Works

| Component       | Tech Used        | Purpose                          |
|----------------|------------------|----------------------------------|
| Discovery       | UDP Broadcast     | Find peers on LAN                |
| Messaging       | TCP Sockets       | Send text messages               |
| File Transfer   | TCP + AES + DH    | Encrypt and send files securely  |
| UI              | Tkinter           | Desktop GUI                      |
| Encryption      | AES-256-CBC       | Symmetric file/message encryption |
| Key Exchange    | Diffie-Hellman    | Generate shared secret keys      |

---

## 🛠️ Installation


git clone https://github.com/your-username/p2p-lan-messenger.git
cd p2p-lan-messenger
pip install -r requirements.txt
✅ Ensure all devices are on the same local network

📦 Dependencies
Python 3.8+

pycryptodome for AES/DH

tkinter (pre-installed with Python)

pip install pycryptodome
▶️ Running the App
On each device or terminal:

python main.py
You’ll see:

Peer list updating every 5s

Options to send messages or files

Logs for status and errors

🧪 Testing Tips
Run main.py on at least 2 machines in the same LAN

Use the GUI to:

Select a peer

Send a secure message or encrypted file

Received files are saved as received_<filename> in the current directory

🧰 Project Structure
p2p-lan-messenger/
├── main.py                # GUI Entry point
├── README.md
├── requirements.txt
├── peer/
│   ├── discovery.py       # Peer discovery (UDP)
│   ├── messaging.py       # Text message sending (TCP)
│   ├── file_transfer.py   # Secure file transfer (TCP + AES + DH)
│   ├── crypto_utils.py    # AES and Diffie-Hellman utilities
🤝 Contributing
Pull requests and suggestions welcome!

🧾 License
MIT License

✨ Author
Built with 💡 by Vincent Nyamao
