from TwitchPlays import *
from dotenv import load_dotenv
import os
from pywitch import PyWitchHeat, run_forever
import threading
import pydirectinput
from global_hotkeys import *


click_cooldown = 1
channel = "thepiledriver"

load_dotenv()
user_dict = dict()

def callback(data):
    if data["user_id"] in user_dict:
        if user_dict[data["user_id"]] + click_cooldown > data["event_time"]:
            return
    user_dict[data["user_id"]] = data["event_time"]
    x, y = int(data["x"]*1920), int(data["y"]*1080)
    pydirectinput.mouseDown(x, y, button="left")
    pydirectinput.mouseUp(x, y, button="left")

heat = PyWitchHeat(channel, os.getenv("ACCESS_TOKEN"), callback)
bot = Bot(os.getenv("TWITCH_TOKEN"), "!", [channel])
bot.keys = {
            "w": [("w", 1000)],
            "d": [("d", 1000)],
            "a": [("a", 1000)],
            "s": [("s", 1000)],
            "jump": [("space", 100)],
            "hover": [("space", 1000)]
        }
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
# bot.cmd["!help"] = help_cmd

@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    cmds = [f"!{cmd}" for cmd in list(bot.commands.keys())] + list(bot.cmds.keys()) + list(bot.keys.keys()) + list(bot.mouse.keys())
    response = f"@{ctx.author.name}: {', '.join(cmds)}."
    await ctx.reply(response)

async def kill_script():
    # I dont like this solution
    '''    heat.stop()
    await bot.close()'''
    os._exit(0)

def on_hotkey_press():
    asyncio.run(kill_script())

async def main():
    bindings = [{
        "hotkey": "control + 1",
        "on_press_callback": on_hotkey_press,
        "on_release_callback": None,
        "actuate_on_partial_release": False
    }]
    thread1 = threading.Thread(target=bot.run)
    thread2 = threading.Thread(target=heat.start)
    # thread3 = threading.Thread(target=run_forever)
    thread1.start()
    thread2.start()
    loop = asyncio.get_event_loop()
    register_hotkeys(bindings)
    start_checking_hotkeys()
    # thread3.start()
    thread1.join()
    thread2.join()
    # thread3.join()
    loop.stop()
    

if __name__ == "__main__":
    asyncio.run(main())

# TODO: toggle heat map