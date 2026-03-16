# Realtime CLI + Web Chat

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-green)
![Render](https://img.shields.io/badge/Deployment-Render-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

A real-time chat application that enables communication between **terminal (CLI) users** and **web browser users** using **WebSockets**.

This project demonstrates how to build a lightweight messaging system using **Python, Flask, and Flask-SocketIO**, allowing multiple users to exchange messages instantly across different interfaces.

---

## 🌐 Live Demo

Web Chat Interface:
https://realtime-cli-web-chat.onrender.com

---

## 🚀 Features

* Real-time messaging using WebSockets
* CLI (terminal) chat client
* Web browser chat interface
* Multi-user communication
* Lightweight Python server
* Deployable to cloud platforms
* Simple and extensible architecture

---

## 🛠 Tech Stack

**Backend**

* Python
* Flask
* Flask-SocketIO

**Frontend**

* HTML
* CSS
* JavaScript
* Socket.IO

**Deployment**

* Render
* GitHub

---

## 📁 Project Structure

```
realtime-cli-web-chat/
│
├── client.py            # CLI chat client
├── server.py            # Socket communication server
├── web_server.py        # Web interface server
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
│
├── templates/
│   └── index.html       # Web chat UI
│
└── README.md
```

---

## ⚙️ Installation & Local Setup

### 1️⃣ Clone the repository

```
git clone https://github.com/Nishant27203/realtime-cli-web-chat.git
cd realtime-cli-web-chat
```

---

### 2️⃣ Install dependencies

```
pip install -r requirements.txt
```

---

### 3️⃣ Start the web server

```
python web_server.py
```

The web interface will be available at:

```
http://localhost:5000
```

---

### 4️⃣ Start the CLI client

Open another terminal and run:

```
python client.py
```

Enter the following when prompted:

```
Server IP: 127.0.0.1
Port: 9999
Username: your_name
```

---

## 🏗 Architecture

           +-------------------+
           |   CLI Client      |
           |   (client.py)     |
           +---------+---------+
                     |
                     |
                     v
           +-------------------+
           |   Chat Server     |
           |   Flask-SocketIO  |
           |   server.py       |
           +---------+---------+
                     |
                     |
                     v
           +-------------------+
           |   Web Server      |
           |   web_server.py   |
           +---------+---------+
                     |
                     |
                     v
           +-------------------+
           |   Web Browser     |
           |   index.html      |
           +-------------------+

 The application uses **Flask-SocketIO and WebSockets** to maintain persistent connections between the server and multiple clients, enabling real-time communication between CLI users and web users.

## 🖥 Usage

1. Open the **web interface** in a browser
2. Enter a username and join the chat
3. Start sending messages in real time
4. CLI users can also connect using the terminal client

Both CLI and web users can communicate through the same chat server.

---

## 📸 Screenshots

You can add screenshots of the application interface here.

Example:

```
screenshots/chat-interface.png
```

---

## 🧠 Architecture Overview

```
CLI Client
     │
     │
     ▼
Socket Server (Flask-SocketIO)
     │
     │
     ▼
Web Client (Browser)
```

The system uses **WebSockets** to maintain persistent connections between the server and multiple clients, enabling real-time communication.

---

## 🔮 Future Improvements

* Multiple chat rooms
* Private messaging
* Message history storage
* User authentication
* Improved UI/UX
* Online users list

---

## 👤 Author

Nishant
GitHub: https://github.com/Nishant27203

---

## 📜 License

This project is open source and available under the MIT License.
