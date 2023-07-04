from flask import Flask, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room, send, rooms
import ssl
import asyncio
import time

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('/etc/letsencrypt/live/willpile.com/fullchain.pem', '/etc/letsencrypt/live/willpile.com/privkey.pem')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'  # Set a secret key for the application
CORS(app, support_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=["*", "http://localhost:8080"])  # Initialize SocketIO



clients = dict()

@app.route('/')
def index():
    return render_template("index.html"), 200

@socketio.on('connect')
def handle_connect():
    print('A client connected')

@app.route('/<channelid>', methods=["GET", "POST"])
def channel(channelid):
    try:
        rd = request.get_json()
        rd["event_time"] = time.time()
        if rd["action"] == "auth":
            print(rd, channelid)
        elif rd["action"] == "leftClick":
            print("left click")
            print(channelid)
            socketio.emit("leftClick", rd, to=str(channelid))
        elif rd["action"] == "rightClick":
            print("right click")
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
        print(data)
        join_room(data)
    else:
        join_room(data)
        clients[data].append(request.sid)
    emit("init", data)

@socketio.on('json')
def handle_json(json):
    emit(json, json=True)

def run_flask():
    socketio.run(app, host='0.0.0.0', port=8080, ssl_context=context)

async def main():
    flask_task = asyncio.create_task(run_flask())

    await asyncio.gather(flask_task)

if __name__ == '__main__':
    asyncio.run(main())