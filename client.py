import socket
import threading
import sys
from config import HOST, CLI_PORT


def print_banner() -> None:
    print("------------------------------------")
    print("        CHAT CLIENT LOGIN")
    print("------------------------------------\n")


def read_input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


class ChatClient:
    def __init__(self, server_ip: str, port: int, username: str) -> None:
        self.server_ip = server_ip
        self.port = port
        self.username = username
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self._print_lock = threading.Lock()

    def connect(self) -> bool:
        try:
            self.sock.connect((self.server_ip, self.port))
            self.running = True
        except OSError as e:
            print(f"Connection failed: {e}")
            return False

        # Simple handshake: wait for USERNAME? then send username
        try:
            data = self.sock.recv(1024).decode("utf-8")
            if not data.startswith("USERNAME?"):
                print("Unexpected response from server.")
                return False
            self.sock.sendall((self.username + "\n").encode("utf-8"))

            # Check for possible error
            self.sock.settimeout(0.5)
            try:
                resp = self.sock.recv(1024).decode("utf-8")
                if resp.startswith("ERROR"):
                    print(resp.strip())
                    return False
                else:
                    # Push back any non-error data into a local buffer (just print it)
                    if resp.strip():
                        print(resp.strip())
            except socket.timeout:
                pass
            finally:
                self.sock.settimeout(None)
        except OSError as e:
            print(f"Handshake failed: {e}")
            return False

        return True

    def start(self) -> None:
        print("\nConnecting to server...")
        if not self.connect():
            print("Could not connect. Exiting.")
            return

        print("Connection successful!")
        print(f"Welcome {self.username}\n")

        print("----------------------------------------")
        print("          CHAT ROOM : GENERAL")
        print("----------------------------------------\n")

        threading.Thread(target=self.receive_loop, daemon=True).start()
        self.send_loop()

    def _safe_print(self, text: str, end: str = "\n") -> None:
        with self._print_lock:
            print(text, end=end, flush=True)

    def _read_line(self) -> str:
        buf = b""
        while True:
            ch = self.sock.recv(1)
            if not ch:
                return ""
            if ch == b"\n":
                return buf.decode("utf-8", errors="replace")
            buf += ch

    def receive_loop(self) -> None:
        try:
            while self.running:
                line = self._read_line()
                if not line:
                    self._safe_print("\nSYSTEM: Connection closed by server.")
                    break
                message = line.rstrip("\n")
                self._safe_print(f"\n{message}", end="\n")
                self._safe_print("> ", end="")
        except OSError:
            pass
        finally:
            self.running = False

    def send_loop(self) -> None:
        print("Type your message below")
        print("----------------------------------------")
        print("Commands: /help /users /rooms /join <room> /who /msg <user> <text> /exit\n")

        try:
            while self.running:
                msg = read_input("> ")
                if msg is None:
                    continue

                msg = msg.strip()
                if not msg:
                    continue

                if msg == "/exit":
                    self.sock.sendall((msg + "\n").encode("utf-8"))
                    print("\nDisconnecting from server...\n")
                    break

                try:
                    self.sock.sendall((msg + "\n").encode("utf-8"))
                except OSError:
                    print("SYSTEM: Failed to send message.")
                    break
        finally:
            self.running = False
            try:
                self.sock.close()
            except OSError:
                pass
            print("You have left the chat.")
            print("Connection closed.")


def main() -> None:
    print_banner()
    server_ip = read_input(f"Enter Server IP  ({HOST}) : ").strip() or HOST
    port_str = read_input(f"Enter Port       ({CLI_PORT}) : ").strip() or str(CLI_PORT)
    username = read_input("\nEnter Username   : ").strip()

    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    try:
        port = int(port_str)
    except ValueError:
        print("Invalid port number.")
        sys.exit(1)

    client = ChatClient(server_ip, port, username)
    client.start()


if __name__ == "__main__":
    main()

