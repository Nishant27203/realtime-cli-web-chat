## CLI Chat Tool (Server & Client)

This is a simple **CLI-based multi-user chat application** suitable for MCA-level projects.  
It demonstrates **client–server architecture**, **socket programming**, and **multithreading**.

### Project Structure

- `config.py` – central configuration (host, ports, app name).
- `server.py` – **CLI chat server (admin console)**, accepts connections, manages users/rooms, broadcasts messages.
- `client.py` – **CLI chat client**, handles login, chat interface, commands, and exit.
- `web_server.py` – **web-based chat server** (Flask + Socket.IO) and serves the HTML interface.
- `templates/index.html` – modern web UI for the chat room.
- `requirements.txt` – Python dependencies for the web version.

### How to Run

#### A. CLI Version (Terminal)

1. **Start the server** (in one terminal):

```bash
cd /Users/nishant/Downloads/CLI
python server.py
```

You should see the **CLI CHAT SERVER** banner and "Waiting for clients...".

2. **Start a client** (in another terminal window/tab):

```bash
cd /Users/nishant/Downloads/CLI
python client.py
```

Enter:
- Server IP: `127.0.0.1` (or your server machine IP)
- Port: `9999` (default matches `server.py`)
- Username: e.g. `Rahul`

3. **Start more clients** for multiple users by running `client.py` again in more terminals.

#### B. Web Version (Browser Interface)

1. Install dependencies:

```bash
cd /Users/nishant/Downloads/CLI
pip install -r requirements.txt
```

2. Start the web server:

```bash
python web_server.py
```

3. Open your browser and go to:

```text
http://127.0.0.1:5000
```

4. Enter your **name**, click **Join**, and chat from the web page.  
   Open the URL in multiple browser windows or devices to simulate multiple users.

### Features Implemented

- **Server Interface**
  - Shows status, IP, port.
  - Lists connected clients and total active users.
  - Logs join/leave events with timestamps.
  - Admin commands:
    - `/users` list active users
    - `/rooms` list rooms
    - `/kick <user>` kick a user
    - `/broadcast <msg>` send message to all users
    - `/shutdown` stop server

- **Client Login Interface**
  - Prompts for server IP, port, and username.
  - Validates connection and username uniqueness.

- **Main Chat Interface**
  - Displays join/leave messages (e.g. `Rahul joined the chat`).
  - Shows chat messages as `[ROOM] Username: message`.
  - Simple prompt line `>` for typing.

- **Command Interface**
  - `/help` – show available commands.
  - `/users` – list active users.
  - `/rooms` – list rooms.
  - `/join <room>` – join/create a room.
  - `/who` – show users in your current room.
  - `/msg <user> <text>` – send private message.
  - `/leave` – leave chat (same as `/exit`).
  - `/exit` – disconnect from server.

- **Exit / Disconnect**
  - Client shows:
    - `Disconnecting from server...`
    - `You have left the chat.`
    - `Connection closed.`
  - Server logs that the user left and updates total active users.

### Short Viva Explanation

“This is a professional-looking chat application built for MCA level using client–server architecture.  
The **CLI server** manages multiple clients, rooms, and admin commands; the **CLI client** provides a text-based chat and command interface.  
In addition, a **web interface** built with Flask and Socket.IO offers a modern browser-based chat UI that shows active users and system events in real time.”

