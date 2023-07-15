from flask import Flask, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room, send, rooms
import ssl
import asyncio
import time
import jwt
import base64
import math

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('fullchain.pem', 'privkey.pem')

app = Flask(__name__)
app.config['SECRET_KEY'] = ''  # Set a secret key for the application
CORS(app, support_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=["*", "http://localhost:8080"])  # Initialize SocketIO


secret = ""
clients = dict()
auth_set = set()
owner_id = ""
client_id = ""

def verify_jwt(data):
    try:
        # Verify the JWT
        decoded_token = jwt.decode(data["token"], base64.b64decode(secret), algorithms=["HS256"])
        return True, decoded_token
    except jwt.ExpiredSignatureError:
        # The token has expired
        return False, "Token has expired."
    except jwt.InvalidTokenError:
        # The token is invalid or tampered
        return False, "Invalid token."

@app.route('/')
def index():
    return render_template("index.html"), 200

@socketio.on('connect')
def handle_connect():
    print('A client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print("a client disconnected")

@socketio.on_error_default  # Handles any uncaught SocketIO errors
def default_error_handler(e):
    print('An error occurred:', e)

@app.route('/<channelid>', methods=["GET", "POST"])
def channel(channelid):
    try:
        rd = request.get_json()
        rd["event_time"] = time.time()
        if rd["action"] == "auth":
            v, r = verify_jwt(rd)
            if not v:
                return r, 400
            auth_set.add(rd["opaqueID"])
        elif rd["action"] == "leftClick":
            if rd["opaque_id"] in auth_set:
                socketio.emit("leftClick", rd, to=str(channelid))
        elif rd["action"] == "rightClick":
            if rd["opaque_id"] in auth_set:
                socketio.emit("rightClick", rd, to=str(channelid))
        return "success", 200

    except Exception as e:
        print(e)
        return "fail", 400

@socketio.on('init')
def initiate_socket(data):
    print(data)
    if data not in clients:
        clients[data] = [request.sid]
        join_room(data)
    else:
        join_room(data)
        clients[data].append(request.sid)
    emit("init", data)

@socketio.on('json')
def handle_json(json):
    emit(json, json=True)

def run_flask():
    try:
        socketio.run(app, host='0.0.0.0', port=8080, ssl_context=context)
    except ssl.SSLEOFError:
        print("Client disconnect")

async def main():
    flask_task = asyncio.create_task(run_flask())

    await asyncio.gather(flask_task)

if __name__ == '__main__':
    asyncio.run(main())
