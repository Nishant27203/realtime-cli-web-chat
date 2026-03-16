import socket
import threading
from datetime import datetime
from config import HOST, CLI_PORT


class ChatServer:
    def __init__(self, host: str = HOST, port: int = CLI_PORT) -> None:
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # username -> {"conn": socket, "addr": (ip, port), "room": str}
        self.clients: dict[str, dict] = {}
        # room -> set[usernames]
        self.rooms: dict[str, set[str]] = {"GENERAL": set()}
        self.lock = threading.Lock()
        self.running = True

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self._print_banner()
        threading.Thread(target=self.admin_console_loop, daemon=True).start()

        try:
            while self.running:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_new_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.shutdown()

    def _print_banner(self) -> None:
        print("-" * 40)
        print("          CLI CHAT SERVER")
        print("-" * 40)
        print(f"Server Status : Running")
        print(f"IP Address    : {self.host}")
        print(f"Port Number   : {self.port}")
        print("\nAdmin Commands: /users  /rooms  /kick <user>  /broadcast <msg>  /shutdown")
        print("\nWaiting for clients...\n")

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M")

    def _send_line(self, conn: socket.socket, line: str) -> None:
        if not line.endswith("\n"):
            line += "\n"
        conn.sendall(line.encode("utf-8"))

    def broadcast_all(self, message: str, exclude_username: str | None = None) -> None:
        with self.lock:
            dead_clients = []
            for username, info in self.clients.items():
                conn = info["conn"]
                if exclude_username is not None and username == exclude_username:
                    continue
                try:
                    self._send_line(conn, message.rstrip("\n"))
                except OSError:
                    dead_clients.append(username)

            for username in dead_clients:
                info = self.clients.pop(username, None)
                if info:
                    try:
                        info["conn"].close()
                    except OSError:
                        pass
                    self._remove_from_room_locked(username, info.get("room", "GENERAL"))
                    self._log_system(f"{username} disconnected unexpectedly ({info.get('addr')})")

    def broadcast_room(self, room: str, message: str, exclude_username: str | None = None) -> None:
        room = room.upper()
        with self.lock:
            usernames = list(self.rooms.get(room, set()))
            conns = []
            for u in usernames:
                if exclude_username is not None and u == exclude_username:
                    continue
                info = self.clients.get(u)
                if info:
                    conns.append((u, info["conn"]))

        dead = []
        for u, conn in conns:
            try:
                self._send_line(conn, message.rstrip("\n"))
            except OSError:
                dead.append(u)

        if dead:
            with self.lock:
                for u in dead:
                    info = self.clients.pop(u, None)
                    if info:
                        try:
                            info["conn"].close()
                        except OSError:
                            pass
                        self._remove_from_room_locked(u, info.get("room", "GENERAL"))

    def handle_new_client(self, conn: socket.socket, addr) -> None:
        try:
            self._send_line(conn, "USERNAME?")
            username = self._read_line(conn)

            if not username:
                self._send_line(conn, "ERROR: Username cannot be empty.")
                conn.close()
                return

            with self.lock:
                if username in self.clients:
                    self._send_line(conn, "ERROR: Username already taken.")
                    conn.close()
                    return
                self.clients[username] = {"conn": conn, "addr": addr, "room": "GENERAL"}
                self.rooms.setdefault("GENERAL", set()).add(username)

            self._print_client_connected(username, addr)
            self._log_system(f"{username} joined the chat")

            self.broadcast_all(f"SYSTEM: {username} joined the chat.")
            self.send_active_users(username)
            self._send_line(conn, "SYSTEM: Type /help for commands. Default room is GENERAL.")

            self.handle_client_messages(username, conn, addr)
        except ConnectionError:
            conn.close()

    def send_active_users(self, username: str) -> None:
        with self.lock:
            info = self.clients.get(username)
            if not info:
                return
            target_conn = info["conn"]
            users_list = ", ".join(sorted(self.clients.keys()))
        self._send_line(target_conn, f"SYSTEM: Active users: {users_list}")

    def _read_line(self, conn: socket.socket) -> str:
        # Minimal line framing: read until newline
        buf = b""
        while True:
            chunk = conn.recv(1)
            if not chunk:
                return ""
            if chunk == b"\n":
                return buf.decode("utf-8", errors="replace").strip()
            buf += chunk

    def handle_client_messages(self, username: str, conn: socket.socket, addr) -> None:
        try:
            while True:
                message = self._read_line(conn)
                if not message:
                    break

                if message.startswith("/"):
                    if not self.handle_command(username, message):
                        break
                else:
                    room = self.get_user_room(username)
                    formatted = f"[{room}] {username}: {message}"
                    self.broadcast_room(room, formatted, exclude_username=None)
        except ConnectionError:
            pass
        finally:
            self.remove_client(username, addr)

    def get_user_room(self, username: str) -> str:
        with self.lock:
            info = self.clients.get(username)
            return (info.get("room") if info else "GENERAL") or "GENERAL"

    def handle_command(self, username: str, command: str) -> bool:
        with self.lock:
            info = self.clients.get(username)
        if not info:
            return False
        conn = info["conn"]

        parts = command.strip().split(" ", 2)
        cmd = parts[0].lower()

        if cmd == "/help":
            help_text = "\n".join(
                [
                    "Available Commands:",
                    "/help                 Show command list",
                    "/users                Show active users (global)",
                    "/rooms                List rooms",
                    "/join <room>          Join/create a room",
                    "/who                  Show users in your current room",
                    "/msg <user> <text>    Send private message",
                    "/leave                Leave chat (same as /exit)",
                    "/exit                 Disconnect from server",
                    "",
                ]
            )
            self._send_line(conn, help_text.rstrip("\n"))
            return True

        if cmd == "/users":
            with self.lock:
                users = sorted(self.clients.keys())
            lines = ["Active Users:"] + [f"{i}. {u}" for i, u in enumerate(users, start=1)] + [""]
            for line in lines:
                self._send_line(conn, line)
            return True

        if cmd == "/rooms":
            with self.lock:
                rooms = sorted(self.rooms.keys())
            self._send_line(conn, "Rooms:")
            for r in rooms:
                with self.lock:
                    count = len(self.rooms.get(r, set()))
                self._send_line(conn, f"- {r} ({count})")
            self._send_line(conn, "")
            return True

        if cmd == "/join":
            if len(parts) < 2 or not parts[1].strip():
                self._send_line(conn, "SYSTEM: Usage: /join <room>")
                return True
            new_room = parts[1].strip().upper()
            old_room = self.get_user_room(username)
            if new_room == old_room:
                self._send_line(conn, f"SYSTEM: You are already in room {new_room}.")
                return True

            with self.lock:
                self.rooms.setdefault(new_room, set())
                self._remove_from_room_locked(username, old_room)
                self.rooms[new_room].add(username)
                if username in self.clients:
                    self.clients[username]["room"] = new_room

            self.broadcast_room(old_room, f"SYSTEM: {username} left the room {old_room}.")
            self.broadcast_room(new_room, f"SYSTEM: {username} joined the room {new_room}.")
            self._send_line(conn, f"SYSTEM: Joined room {new_room}.")
            self._log_system(f"{username} switched rooms {old_room} -> {new_room}")
            return True

        if cmd == "/who":
            room = self.get_user_room(username)
            with self.lock:
                users = sorted(self.rooms.get(room, set()))
            self._send_line(conn, f"Users in room {room}:")
            for i, u in enumerate(users, start=1):
                self._send_line(conn, f"{i}. {u}")
            self._send_line(conn, "")
            return True

        if cmd == "/msg":
            if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                self._send_line(conn, "SYSTEM: Usage: /msg <user> <text>")
                return True
            target = parts[1].strip()
            text = parts[2].strip()
            with self.lock:
                target_info = self.clients.get(target)
            if not target_info:
                self._send_line(conn, f"SYSTEM: User '{target}' not found.")
                return True
            try:
                self._send_line(target_info["conn"], f"[PM] {username}: {text}")
                self._send_line(conn, f"[PM to {target}] {text}")
            except OSError:
                self._send_line(conn, f"SYSTEM: Failed to message '{target}'.")
            return True

        if cmd in ("/leave", "/exit"):
            self._send_line(conn, "SYSTEM: Disconnecting from server...")
            try:
                conn.close()
            except OSError:
                pass
            return False

        self._send_line(conn, f"SYSTEM: Unknown command '{command}'. Type /help")
        return True

    def _remove_from_room_locked(self, username: str, room: str) -> None:
        room = (room or "GENERAL").upper()
        members = self.rooms.get(room)
        if members and username in members:
            members.remove(username)
        if members is not None and len(members) == 0 and room != "GENERAL":
            # cleanup empty non-default rooms
            self.rooms.pop(room, None)

    def remove_client(self, username: str, addr) -> None:
        with self.lock:
            info = self.clients.pop(username, None)
            existed = info is not None
            if existed:
                room = info.get("room", "GENERAL")
                self._remove_from_room_locked(username, room)
                try:
                    info["conn"].close()
                except OSError:
                    pass

        if existed:
            self._print_client_disconnected(username, addr)
            self._log_system(f"{username} left the chat")
            self.broadcast_all(f"SYSTEM: {username} left the chat.")

    def _log_system(self, text: str) -> None:
        print(f"[{self._now()}] {text}")
        with self.lock:
            total = len(self.clients)
        print(f"Total Active Users : {total}\n")

    def _print_client_connected(self, username: str, addr) -> None:
        print(f"Client Connected : {username} ({addr[0]})")

    def _print_client_disconnected(self, username: str, addr) -> None:
        print(f"Client Disconnected : {username} ({addr[0]})")

    def admin_console_loop(self) -> None:
        while self.running:
            try:
                cmdline = input().strip()
            except EOFError:
                return
            except KeyboardInterrupt:
                return

            if not cmdline:
                continue

            parts = cmdline.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "/users":
                with self.lock:
                    users = sorted(self.clients.keys())
                print("Active Users:")
                for i, u in enumerate(users, start=1):
                    print(f"{i}. {u}")
                print("")
            elif cmd == "/rooms":
                with self.lock:
                    rooms = sorted(self.rooms.keys())
                print("Rooms:")
                for r in rooms:
                    with self.lock:
                        count = len(self.rooms.get(r, set()))
                    print(f"- {r} ({count})")
                print("")
            elif cmd == "/broadcast":
                if not arg:
                    print("Usage: /broadcast <message>\n")
                    continue
                self.broadcast_all(f"SYSTEM: [ADMIN] {arg}")
                self._log_system(f"ADMIN broadcast: {arg}")
            elif cmd == "/kick":
                if not arg:
                    print("Usage: /kick <username>\n")
                    continue
                self.kick_user(arg)
            elif cmd == "/shutdown":
                self._log_system("ADMIN requested shutdown")
                self.running = False
                try:
                    self.server_socket.close()
                except OSError:
                    pass
                self.shutdown()
                return
            else:
                print("Admin Commands: /users /rooms /kick <user> /broadcast <msg> /shutdown\n")

    def kick_user(self, username: str) -> None:
        with self.lock:
            info = self.clients.pop(username, None)
            if not info:
                print(f"User '{username}' not found.\n")
                return
            room = info.get("room", "GENERAL")
            self._remove_from_room_locked(username, room)

        try:
            self._send_line(info["conn"], "SYSTEM: You have been kicked by ADMIN.")
            info["conn"].close()
        except OSError:
            pass
        self.broadcast_all(f"SYSTEM: {username} was kicked by ADMIN.")
        self._log_system(f"ADMIN kicked {username}")

    def shutdown(self) -> None:
        with self.lock:
            for username, info in list(self.clients.items()):
                try:
                    self._send_line(info["conn"], "SYSTEM: Server is shutting down.")
                    info["conn"].close()
                except OSError:
                    pass
            self.clients.clear()
            self.rooms = {"GENERAL": set()}
        self.server_socket.close()


if __name__ == "__main__":
    server = ChatServer()
    server.start()

