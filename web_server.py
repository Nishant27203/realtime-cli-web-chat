from __future__ import annotations

import sqlite3
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit

from config import APP_NAME, WEB_HOST, WEB_PORT


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-for-mca-demo"
socketio = SocketIO(app, cors_allowed_origins="*")

USERS = {}  # sid -> {"username": str, "room": str}
ROOM = "GENERAL"
MAX_IMAGE_BYTES = 1_500_000  # ~1.5MB in base64/data-url form (demo-friendly)
DB_PATH = "chat.db"
HISTORY_LIMIT = 50


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts INTEGER NOT NULL,
              room TEXT NOT NULL,
              username TEXT NOT NULL,
              type TEXT NOT NULL,
              content TEXT NOT NULL,
              filename TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_message(*, room: str, username: str, type_: str, content: str, filename: str | None = None) -> None:
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO messages (ts, room, username, type, content, filename) VALUES (?, ?, ?, ?, ?, ?)",
            (int(time.time()), room, username, type_, content, filename),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_history(room: str, limit: int = HISTORY_LIMIT) -> list[dict]:
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT ts, room, username, type, content, filename FROM messages WHERE room = ? ORDER BY id DESC LIMIT ?",
            (room, limit),
        ).fetchall()
    finally:
        conn.close()

    # reverse to chronological order
    out: list[dict] = []
    for r in reversed(rows):
        out.append(
            {
                "ts": int(r["ts"]),
                "room": r["room"],
                "username": r["username"],
                "type": r["type"],
                "content": r["content"],
                "filename": r["filename"],
            }
        )
    return out


@app.route("/")
def index():
    return render_template("index.html", app_name=APP_NAME)


@socketio.on("connect")
def handle_connect():
    emit("system", {"message": "Connected to Web Chat Server."})


@socketio.on("join")
def handle_join(data):
    username = (data or {}).get("username", "").strip() or "Guest"
    sid = request.sid

    # store user
    USERS[sid] = {"username": username, "room": ROOM}
    join_room(ROOM)

    emit("history", {"room": ROOM, "items": fetch_history(ROOM)})
    emit("system", {"message": f"{username} joined the chat."}, room=ROOM)
    _send_user_list()


@socketio.on("chat")
def handle_chat(data):
    sid = request.sid
    info = USERS.get(sid)
    if not info:
        return
    message = (data or {}).get("message", "").strip()
    if not message:
        return
    username = info["username"]
    save_message(room=info["room"], username=username, type_="text", content=message)
    emit(
        "chat",
        {"username": username, "message": message, "room": info["room"]},
        room=info["room"],
    )


@socketio.on("image")
def handle_image(data):
    """
    Receives a data-url image payload from a browser client and broadcasts it to the room.
    NOTE: This is a demo approach (in-memory). Production should store files and send URLs.
    """
    sid = request.sid
    info = USERS.get(sid)
    if not info:
        return

    payload = data or {}
    data_url = (payload.get("dataUrl") or "").strip()
    filename = (payload.get("filename") or "image").strip()

    if not data_url.startswith("data:image/"):
        emit("system", {"message": "Only image files are supported."})
        return

    if len(data_url.encode("utf-8", errors="ignore")) > MAX_IMAGE_BYTES:
        emit("system", {"message": "Image too large. Please upload a smaller image."})
        return

    username = info["username"]
    save_message(room=info["room"], username=username, type_="image", content=data_url, filename=filename)
    emit(
        "image",
        {"username": username, "dataUrl": data_url, "filename": filename, "room": info["room"]},
        room=info["room"],
    )


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    info = USERS.pop(sid, None)
    if not info:
        return
    leave_room(info["room"])
    emit("system", {"message": f"{info['username']} left the chat."}, room=info["room"])
    _send_user_list()


def _send_user_list():
    users = [u["username"] for u in USERS.values()]
    emit("users", {"users": users}, broadcast=True)


if __name__ == "__main__":
    # Cross-platform run: `python web_server.py`
    init_db()
    socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=True, allow_unsafe_werkzeug=True)

