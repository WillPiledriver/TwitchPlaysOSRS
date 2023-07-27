from TwitchPlays import *
from RunelitePlugin import RunelitePlugin as rp
from dotenv import load_dotenv
import os
import threading
from global_hotkeys import *
import numpy as np
from sklearn.cluster import DBSCAN
import subprocess
import socketio
import asyncio
import cv2
import json
import pygetwindow as gw
import math

runelite_ws_url = "ws://localhost:8085"
runelite_ws = rp(runelite_ws_url)
sio = socketio.AsyncClient()


# Set the LOKY_MAX_CPU_COUNT environment variable
os.environ['LOKY_MAX_CPU_COUNT'] = '4'


image_path = "open_1920.png"
click_cooldown = 2.5
channel = "thepiledriver"
heat_map = True
command_chance = 1.0
command_cooldown = 5
channel_id = "23728793"


load_dotenv()
user_dict = dict()
auth_list = list()
x_coordinates = np.array([])
y_coordinates = np.array([])

window_y_offset = 23
def get_window(partial_title):
    for window in gw.getWindowsWithTitle(partial_title):
        if partial_title.lower() in window.title.lower():
            return window
    return None

@sio.event
async def connect():
    print("I'm connected!")
    await sio.emit("init", channel_id)

@sio.event
async def message(data):
    print('Received message:', data)

@sio.event
async def leftClick(data):
    global x_coordinates, y_coordinates, user_dict
    size_x, size_y = pydirectinput.size()
    '''if data["opaque_id"] in user_dict:
        if user_dict[data["opaque_id"]]["time"] + click_cooldown > data["event_time"]:
            return'''
    
    x, y = int(data["x"] * size_x), int(data["y"] * size_y)
    if not mask[y, x].any():
        user_dict[data["opaque_id"]] = {
            "time": data["event_time"],
            "button": "left",
            "coords": (x, y)
        }

@sio.event
async def rightClick(data):
    global x_coordinates, y_coordinates, user_dict
    size_x, size_y = pydirectinput.size()
    '''if data["opaque_id"] in user_dict:
        if user_dict[data["opaque_id"]]["time"] + click_cooldown > data["event_time"]:
            return'''
    
    x, y = int(data["x"] * size_x), int(data["y"] * size_y)
    if not mask[y, x].any():
        user_dict[data["opaque_id"]] = {
            "time": data["event_time"],
            "button": "right",
            "coords": (x, y)
        }

@sio.event
async def init(data):
    if data == channel_id:
        print(channel_id)
        print("Good to go")

@sio.event
async def connect_error(data):
    print("The connection failed!")

@sio.event
async def disconnect():
    print("I'm disconnected!")

async def run_socketio():
    await sio.connect("https://willpile.com:8080")
    await sio.wait()

def callback(data):
    global x_coordinates, y_coordinates, user_dict
    size_x, size_y = pydirectinput.size()
    if data["opaque_id"] in user_dict:
        if user_dict[data["opaque_id"]]["time"] + click_cooldown > data["event_time"]:
            return
    
    x, y = int(data["x"] * size_x), int(data["y"] * size_y)
    user_dict[data["opaque_id"]] = {
        "time": data["event_time"],
        "coords": (x, y)
    }

def mouse_loop():
    global x_coordinates, y_coordinates, user_dict
    while True:
        time.sleep(click_cooldown)
        if len(user_dict) == 0:
            continue
        
        x_coordinates = np.array([data["coords"][0] for user, data in user_dict.items()])
        y_coordinates = np.array([data["coords"][1] for user, data in user_dict.items()])

        coordinates = np.column_stack((x_coordinates, y_coordinates))

        # Define the DBSCAN parameters
        eps = 150  # Distance threshold for clustering
        min_samples = 1  # Minimum number of points in a cluster

        # Perform DBSCAN clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(coordinates)

        # Find the cluster with the most points
        unique_labels, counts = np.unique(labels, return_counts=True)
        most_populated_cluster_label = unique_labels[np.argmax(counts)]

        # Get the center coordinates of the most populated cluster
        most_populated_cluster = coordinates[labels == most_populated_cluster_label]
        center = np.mean(most_populated_cluster, axis=0)

        # Count the clicks of the most populated cluster
        click_counts = {
            "left": 0,
            "right": 0
        }
        for i, (user, data) in enumerate(user_dict.items()):
            if labels[i] == most_populated_cluster_label:
                button = data["button"]
                if button in click_counts:
                    click_counts[button] += 1
        most_clicked_key = max(click_counts, key=click_counts.get)

        # Human-like mouse movement and click
        x, y = (round(center[0]), round(center[1]))
        print("Center coordinates:", x, y)
        if mask[y, x].any():
            return
        r = random.uniform(0.5, 1.25)
        user_dict = dict()
        subprocess.call(["python", "human_mouse.py", str(x), str(y), str(r), most_clicked_key])
        time.sleep(random.uniform(0.2, 0.7))
        time.sleep(click_cooldown)

# Load the PNG image
image = cv2.imread(image_path)

# Convert the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Threshold the grayscale image
_, threshold = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)

# Find contours of the black regions
contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Create a mask for black regions
mask = np.zeros_like(image)

# Draw contours on the mask
cv2.drawContours(mask, contours, -1, (255, 255, 255), thickness=cv2.FILLED)


# if heat_map:
    # heat = PyWitchHeat(channel, os.getenv("ACCESS_TOKEN"), callback)
bot = Bot(os.getenv("TWITCH_TOKEN"), "!", [channel])

bot.keys = {
    "l": [("left", lambda: random.randint(750, 1000))],
    "r": [("right", lambda: random.randint(750, 1000))],
    "u": [("up", lambda: random.randint(200, 350))],
    "d": [("down", lambda: random.randint(200, 350))]
}

"""
bot.keys = {
    "open": [("o", 250)],
    "pick": [("p", 250)],
    "push": [("s", 250)],
    "pull": [("y", 250)],
    "close": [("c", 250)],
    "look": [("l", 250)],
    "talk": [("t", 250)],
    "give": [("g", 250)],
    "use": [("u", 250)],
    "inv": [("i", 250)],
    "hint": [("h", 250)],
    "hotswap": [("f10", 250)]
}

noita
bot.keys = {
            "w": [("w", 1000)],
            "d": [("d", 1000)],
            "a": [("a", 1000)],
            "s": [("s", 1000)],
            "jump": [("space", 100)],
            "hover": [("space", 1000)],
            "kick": [("f", 100)],
            "e": [("e", 100)],
            "1": {("1", 100)},
            "2": {("2", 100)},
            "3": {("3", 100)},
            "4": {("4", 100)},
            "5": {("5", 100)},
            "6": {("6", 100)},
            "7": {("7", 100)},
            "8": {("8", 100)},
        }"""
'''bot.mouse = {
            "left": [((-10, 0), 0)],
            "right": [((10, 0), 0)],
            "up": [((0, -10), 0)],
            "down": [((0, 10), 0)],
            "lc": [((0, 0), 1)], # left click
            "rc": [((0, 0), 2)], # right click
            "mm": [((0, 0), 3)], # middle mouse button
            "lu": [((-100, 0), 1), ((0,-100), 2)], # left up, mouse 1 and 2
}'''
bot.chance = command_chance
bot.cooldown = command_cooldown
# bot.cmd["!help"] = help_cmd

def clicky(x, y, button="left", steady=False):
    window = get_window("runelite")
    offsets = window.topleft
    pos = pydirectinput.position()
    distance = math.sqrt((x - pos[0])**2 + (y - pos[1])**2)
    fraction = distance / 1100
    r = max(random.uniform(0.5, 1) * fraction, random.uniform(0.05, 0.17))
    subprocess.call(["python", "human_mouse.py", str(int(x) + offsets[0]), str(int(y) + offsets[1] + window_y_offset), str(r), button, str(int(steady))])


@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    cmds = [f"!{cmd}" for cmd in list(bot.commands.keys())] + list(bot.cmds.keys()) + list(bot.keys.keys()) + list(bot.mouse.keys())
    response = f"Commands: {', '.join(cmds)}."
    await ctx.reply(response)

@bot.command(name="drop")
async def drop_all(ctx: commands.Context):
    j = {
        "action": "drop",
        "query": " ".join(ctx.message.content.split()[1:])
    }
    await runelite_ws.send(json.dumps(j))

@bot.command(name="npc")
async def click_npc(ctx: commands.Context):
    j = {
        "action": "npc",
        "query": " ".join(ctx.message.content.split()[1:])
    }
    await runelite_ws.send(json.dumps(j))

@runelite_ws.event(name="drop")
async def drop_rcv(data):
    data = data["response"]
    await bot.send_input("shift", True)
    for i in range(len(data)):
        clicky(data[i]["x"] + random.randint(-3, 3), data[i]["y"] + random.randint(-3, 3), steady=True)
    await bot.send_input("shift", False)

@runelite_ws.event(name="npc")
async def npc_rcv(data):
    # Remove any trailing zeros (if present)
    x = [coord for coord in data["response"]["x"] if coord != 0]
    y = [coord for coord in data["response"]["y"] if coord != 0]
    centroid_x = sum(x) / len(x)
    centroid_y = sum(y) / len(y)
    r = random.uniform(0.5, 1.25)
    clicky(centroid_x, centroid_y)
    print("Centroid coordinates: ({}, {})".format(int(centroid_x), int(centroid_y)))

async def kill_script():
    # I dont like this solution
    os._exit(0)

def on_hotkey_press():
    asyncio.run(kill_script())

def run_s():
    asyncio.run(run_socketio())

async def main():
    bindings = [{
        "hotkey": "control + down",
        "on_press_callback": on_hotkey_press,
        "on_release_callback": None,
        "actuate_on_partial_release": False
    }]
    thread1 = threading.Thread(target=bot.run)
    # thread3 = threading.Thread(target=run_forever)
    thread1.start()
    if heat_map:
        """thread2 = threading.Thread(target=heat.start)
        thread2.start()"""
        thread2 = threading.Thread(target=run_s)
        thread2.start()
        thread3 = threading.Thread(target=mouse_loop)
        thread3.start()
    loop = asyncio.get_event_loop()
    register_hotkeys(bindings)
    start_checking_hotkeys()
    thread1.join()
    if heat_map:
        thread2.join()
        thread3.join()
    loop.stop()
    

if __name__ == "__main__":
    asyncio.run(main())