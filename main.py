from TwitchPlays import *
from RunelitePlugin import RunelitePlugin as rp
from OBSWebsocketManager import OBSWebsocketManager as obs_mgr
from dotenv import load_dotenv
import os
import threading
from global_hotkeys import *
import numpy as np
from sklearn.cluster import DBSCAN
import socketio
import asyncio
import cv2
import json
import pygetwindow as gw
import math
import aiofiles
import logging



runelite_ws_url = "ws://localhost:8085"
runelite_ws = rp(runelite_ws_url)
sio = socketio.AsyncClient()
obs_ws = obs_mgr(password=os.getenv("OBS_PASS"))
logging.getLogger("simpleobsws").setLevel(logging.FATAL)

# Set the LOKY_MAX_CPU_COUNT environment variable
os.environ['LOKY_MAX_CPU_COUNT'] = '4'


image_path = "osrs negative.png"
click_cooldown = .1
channel = "thepiledriver"
heat_map = True
command_chance = 1.0
command_cooldown = .5
channel_id = "23728793" # 934681057 23728793
block_mouse = False
block_type = False


load_dotenv()
click_dict = dict()
cmd_dict = dict()
auth_list = list()

x_coordinates = np.array([])
y_coordinates = np.array([])

y_offset = 23
x_offset = 0
viewport_width = 0
viewport_height = 0
actions = list()
tug_of_war = 0
is_chaos = True

def get_window(partial_title):
    for window in gw.getWindowsWithTitle(partial_title):
        if partial_title.lower() in window.title.lower():
            return window
    return None

async def write_json(file_name, data):
    try:
        # Open the file in write mode and use "async with" from aiofiles
        async with aiofiles.open(file_name, 'w') as file:
            # Dump the JSON data into the file
            await file.write(json.dumps(data))
    except Exception as e:
        print(f'Error writing file: {e}')


@sio.event
async def connect():
    await obs_ws.change_text_source("tug", "tug: " + str(tug_of_war))
    print("I'm connected!")
    await sio.emit("init", channel_id)

@sio.event
async def message(data):
    print('Received message:', data)

@sio.event
async def leftClick(data):
    global x_coordinates, y_coordinates, click_dict
    size_x, size_y = pydirectinput.size()
    '''if data["opaque_id"] in click_dict:
        if click_dict[data["opaque_id"]]["time"] + click_cooldown > data["event_time"]:
            return'''
    print(data["x"], data["y"])
    x, y = int(data["x"] * size_x), int(data["y"] * size_y)
    if not mask[y, x].any():
        click_dict[data["opaque_id"]] = {
            "time": data["event_time"],
            "button": "left",
            "coords": (x, y)
        }
    await write_json('./browser_source/coords.json', click_dict)

@sio.event
async def rightClick(data):
    global x_coordinates, y_coordinates, click_dict
    size_x, size_y = pydirectinput.size()
    '''if data["opaque_id"] in click_dict:
        if click_dict[data["opaque_id"]]["time"] + click_cooldown > data["event_time"]:
            return'''
    
    x, y = int(data["x"] * size_x), int(data["y"] * size_y)
    if not mask[y, x].any():
        click_dict[data["opaque_id"]] = {
            "time": data["event_time"],
            "button": "right",
            "coords": (x, y)
        }
    await write_json('./browser_source/coords.json', click_dict)

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

async def interaction_loop():
    global click_dict, cmd_dict
    while True:
        if tug_of_war <= 0:
            cooldown = 0.1
        else:
            cooldown = (tug_of_war * 100 + 1000) / 1000
        await asyncio.sleep(cooldown / 2)
        if len(click_dict) > 0:
            await mouse_loop()
        await asyncio.sleep(cooldown / 2)
        if len(cmd_dict) > 0:
            await cmd_loop()




async def mouse_loop():
    global x_coordinates, y_coordinates, click_dict, block_mouse
    
    if len(click_dict) == 0:
        return
    x_coordinates = np.array([data["coords"][0] for user, data in click_dict.items()])
    y_coordinates = np.array([data["coords"][1] for user, data in click_dict.items()])

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
    for i, (user, data) in enumerate(click_dict.items()):
        if labels[i] == most_populated_cluster_label:
            button = data["button"]
            if button in click_counts:
                click_counts[button] += 1
    most_clicked_key = max(click_counts, key=click_counts.get)

    # Human-like mouse movement and click
    x, y = (round(center[0]), round(center[1]))
    print("Center coordinates:", x, y)
    
    click_dict = dict()
    await clicky(x, y - y_offset, most_clicked_key, steady=True)

def most_common_action_query_pair(cmd_dict):
    action_query_count = {}

    # Count occurrences of each action-query pair
    for user, cmd in cmd_dict.items():
        action_query = (cmd["action"], cmd["query"].lower())
        action_query_count[action_query] = action_query_count.get(action_query, 0) + 1

    # Find the most common action-query pair
    most_common_pair = max(action_query_count, key=action_query_count.get)
    result = {
        "action": most_common_pair[0],
        "query": most_common_pair[1]
    }
    return result

async def cmd_loop():
    global cmd_dict
    if len(cmd_dict) == 0:
        return
    j = most_common_action_query_pair(cmd_dict)
    print(j)
    await runelite_ws.send(json.dumps(j))
    cmd_dict = dict()
    await update_obs_cmd()
       
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
    "d": [("down", lambda: random.randint(200, 350))],
    "space": [(" ", lambda: random.randint(100, 250))]
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

async def message_hack(ctx: commands.Context):
    for m in [f"!{cmd}" for cmd in list(bot.commands.keys())] + list(bot.cmds.keys()) + list(bot.keys.keys()) + list(bot.mouse.keys()):
        if ctx.content.lower().split()[0] == m.lower():
            return
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}\\|;:'\",.<>?/`~ ")

    # Filter the input string to keep only the allowed characters
    m =  ''.join(char for char in ctx.content[:120] if char in allowed_chars)
    j = {
        "action": "message",
        "query": "message",
        "user": ctx.author.name,
        "msg": m
    }
    await runelite_ws.send(json.dumps(j))

bot.chance = command_chance
bot.cooldown = command_cooldown
bot.rcv_message = message_hack
# bot.cmd["!help"] = help_cmd

async def clicky(x, y, button="left", steady=False):
    global block_mouse
    pos = pydirectinput.position()
    distance = math.sqrt((x - pos[0])**2 + (y - pos[1])**2)
    fraction = distance / 1100
    r = max(random.uniform(0.5, 1) * fraction, random.uniform(0.05, 0.17))
    x = int(x) + x_offset
    y = int(y) + y_offset
    print(x, y)
    # Prevent bad clicks
    if not (0 <= x <= 1919) or not (0 <= y <= 1079):
        return
    if mask[y, x].any():
        return
    
    cmd = [
        "python",
        "human_mouse.py",
        str(x),
        str(y),
        str(r),
        button,
        str(int(steady))
    ]
    while block_mouse:
        await asyncio.sleep(0.2)
    block_mouse = True
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()  # Wait for the subprocess to finish
    block_mouse = False

@bot.command(name="chaos")
async def chaos(ctx: commands.Context):
    global tug_of_war, is_chaos
    if ctx.author.is_mod:
        tug_of_war = max(tug_of_war -  10, -50)
    else:
        tug_of_war = max(tug_of_war -  1, -50)
    if not is_chaos and tug_of_war <= 0:
        is_chaos = True
        await ctx.reply("CHAOS!!!!!!!")
    await obs_ws.change_text_source("tug", "tug: " + str(tug_of_war))


@bot.command(name="order")
async def order(ctx: commands.Context):
    global tug_of_war, is_chaos
    if ctx.author.is_mod:
        tug_of_war = min(tug_of_war +  10, 50)
    else:
        tug_of_war = min(tug_of_war +  1, 50)
    if is_chaos and tug_of_war > 0:
        is_chaos = False
        await ctx.reply("Order.")
    await obs_ws.change_text_source("tug", "tug: " + str(tug_of_war))

@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    cmds = [f"!{cmd}" for cmd in list(bot.commands.keys())] + list(bot.cmds.keys()) + list(bot.keys.keys()) + list(bot.mouse.keys())
    response = f"Commands: {', '.join(cmds)}."
    await ctx.reply(response)

@bot.command(name="space")
async def space(ctx: commands.Context):
    for i in range(10):
        await bot.send_input(" ", random.uniform(75, 150))
        await asyncio.sleep(1)


async def update_obs_cmd():
    global actions
    if len(cmd_dict) > 0:
        most_common = most_common_action_query_pair(cmd_dict)
        actions.insert(0, "!" + " ".join(most_common.values())[:25])
        actions = actions[:5]
        await write_json("browser_source/actions.json", actions)
        # await obs_ws.change_text_source(source="cmd_text", text="Next: !" + " ".join(most_common.values())[:25])
    else:
        # await obs_ws.change_text_source(source="cmd_text", text="Next:")
        pass
    

@bot.command(name="goal")
async def goal_cmd(ctx: commands.Context):
    if ctx.author.is_mod or ctx.author.is_broadcaster:
        await obs_ws.change_text_source(source="goal", text=("Goal: " + " ".join(ctx.message.content.split()[1:])))

@bot.command(name="drop")
async def drop_all(ctx: commands.Context):
    legal = ["essence", "logs", "shrimp", "trout", "salmon", "bones", "ore", "burn", "herring"]
    global cmd_dict
    q = " ".join(ctx.message.content.split()[1:])
    is_legal = False
    for l in legal:
        if l in q.lower():
            is_legal = True
            break
    if not is_legal:
        return
    j = {
        "action": "drop",
        "query": q
    }
    cmd_dict[ctx.message.author] = j
    await update_obs_cmd()
    

@bot.command(name="loot")
async def loot(ctx: commands.Context):
    print("loot send")
    global cmd_dict
    j = {
        "action": "loot",
        "query": " ".join(ctx.message.content.split()[1:])
    }
    cmd_dict[ctx.message.author] = j
    await update_obs_cmd()

@bot.command(name="npc")
async def click_npc(ctx: commands.Context):
    global cmd_dict
    j = {
        "action": "npc",
        "query": " ".join(ctx.message.content.split()[1:])
    }
    cmd_dict[ctx.message.author] = j
    await update_obs_cmd()

@bot.command(name="tile")
async def tile(ctx: commands.Context):
    global cmd_dict
    j = {
        "action": "tile",
        "query": " ".join(ctx.message.content.split()[1:])
    }
    cmd_dict[ctx.message.author] = j
    await update_obs_cmd() 

@bot.command(name="type")
async def type_cmd(ctx: commands.Context):
    global block_type
    while block_type:
        await asyncio.sleep(0.5)
    
    block_type = True
    await bot.type_human(" ".join(ctx.message.content.split()[1:])[:120])
    block_type = False

@runelite_ws.event(name="heartbeat")
async def heartbeat(data):
    global x_offset, y_offset, viewport_width, viewport_height
    data = data["response"]
    w = get_window("runelite")
    xd, yd = (w.width, w.height)
    viewport_width, viewport_height = data["viewportWidth"], data["viewportHeight"]
    # x_offset, y_offset = xd - viewport_width, yd - viewport_height

@runelite_ws.event(name="tile")
async def tile_rcv(data):
    data = data["response"]
    x = [coord for coord in data["x"] if coord != 0]
    y = [coord for coord in data["y"] if coord != 0]
    if len(x) > 0:
        centroid_x = sum(x) / len(x)
        centroid_y = sum(y) / len(y)
        await clicky(centroid_x, centroid_y)
        print("Centroid coordinates: ({}, {})".format(int(centroid_x), int(centroid_y)))

@runelite_ws.event(name="loot")
async def loot_rcv(data):
    data = data["response"]
    print(data)
    x = [coord for coord in data["x"] if coord != 0]
    y = [coord for coord in data["y"] if coord != 0]
    if len(x) > 0:
        centroid_x = sum(x) / len(x)
        centroid_y = sum(y) / len(y)
        await clicky(centroid_x, centroid_y)
        print("Centroid coordinates: ({}, {})".format(int(centroid_x), int(centroid_y)))

@runelite_ws.event(name="drop")
async def drop_rcv(data):
    data = data["response"]
    r = random.uniform(0.095, 0.21)
    await bot.send_input("esc", r)
    await asyncio.sleep(random.uniform(0.05, 0.15))
    await bot.send_input("shift", True)
    for i in range(len(data)):
        await clicky(data[i]["x"] + random.randint(-3, 3), data[i]["y"] + random.randint(-3, 3), steady=True)
    await bot.send_input("shift", False)

@runelite_ws.event(name="npc")
async def npc_rcv(data):
    # Remove any trailing zeros (if present)
    x = [coord for coord in data["response"]["x"] if coord != 0]
    y = [coord for coord in data["response"]["y"] if coord != 0]
    centroid_x = sum(x) / len(x)
    centroid_y = sum(y) / len(y)
    await clicky(centroid_x, centroid_y)
    print("Centroid coordinates: ({}, {})".format(int(centroid_x), int(centroid_y)))

@runelite_ws.event(name="login")
async def login(data):
    global block_mouse
    if data["response"] == "ready":
        response = {
            "action": "login",
            "query": "login",
            "username": os.getenv("OSRS_USER"),
            "password": os.getenv("OSRS_PASS")
        }
        print("Logging in.")
        block_mouse = False
        await clicky(962, 336 - y_offset, steady=True)
        block_mouse = True
        await runelite_ws.send(json.dumps(response))
        await asyncio.sleep(0.5)
        await bot.send_input("enter", random.uniform(0.1, 0.2))
        await asyncio.sleep(0.5)
        await bot.send_input("enter", random.uniform(0.1, 0.2))
    elif data["response"] == "logging in":
        print("Logging in.")
    elif data["response"] == "logged in":
        print("Logged in.")
        block_mouse = False
        await clicky(964, 366 - y_offset, steady=True)

async def kill_script():
    # I dont like this solution
    os._exit(0)

def on_hotkey_press():
    asyncio.run(kill_script())

def run_s():
    asyncio.run(run_socketio())

def run_interaction_loop():
    asyncio.run(interaction_loop())


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
        thread3 = threading.Thread(target=run_interaction_loop)
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