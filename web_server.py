from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from config import WEB_HOST, WEB_PORT, APP_NAME


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key-for-mca-demo"
socketio = SocketIO(app, cors_allowed_origins="*")

USERS = {}  # sid -> {"username": str, "room": str}
ROOM = "GENERAL"


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
    emit(
        "chat",
        {"username": username, "message": message, "room": info["room"]},
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
    # Run on configured host/port
    socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=True)

