from twitchio.ext import commands
import pydirectinput
import asyncio
import random
import time

class Bot(commands.Bot):
    def __init__(self, token, prefix="!", channels=[]):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token=token, prefix=prefix, initial_channels=channels)
        self.cmds = dict()
        self.keys = dict()
        self.mouse = dict()
        self.user_dict = dict()
        self.chance = 1.0
        self.cooldown = 0

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')

    async def event_message(self, ctx: commands.Context):
        if ctx.echo:
            return
        command = ctx.content.lower()
        
        if command in self.mouse:
            if ctx.author.id not in self.user_dict:
                self.user_dict[ctx.author.id] = time.time()
                if random.random() > self.chance:
                    return
                await self.task_mouse(self.mouse[command], ctx)
                return
            if self.user_dict[ctx.author.id] + self.cooldown > time.time():
                return
            else:
                self.user_dict[ctx.author.id] = time.time()
            if random.random() > self.chance:
                return
            await self.task_mouse(self.mouse[command], ctx)
            return
        
        if command in self.keys:
            if ctx.author.id not in self.user_dict:
                self.user_dict[ctx.author.id] = time.time()
                if random.random() > self.chance:
                    return
                await self.task_keys(self.keys[command], ctx)
                return
            if self.user_dict[ctx.author.id] + self.cooldown > time.time():
                return
            else:
                self.user_dict[ctx.author.id] = time.time()
            if random.random() > self.chance:
                return
            await self.task_keys(self.keys[command], ctx)
            return
        
        if command in self.cmds:
            if ctx.author.id not in self.user_dict:
                self.user_dict[ctx.author.id] = time.time()
                if random.random() > self.chance:
                    return
                await self.cmds[command](ctx)
                return
            if self.user_dict[ctx.author.id] + self.cooldown > time.time():
                return
            else:
                self.user_dict[ctx.author.id] = time.time()
            if random.random() > self.chance:
                return
            await self.cmds[command](ctx)
            return
        await self.handle_commands(ctx)

    async def mouse_event(self, coords: tuple, click: int, ctx: commands.Context):
        pydirectinput.move(coords[0], coords[1])
        buttons = [None, "left", "right", "middle"]
        if click > 0:
            pydirectinput.mouseDown(button=buttons[click])
            await asyncio.sleep(0.5)
            pydirectinput.mouseUp(button=buttons[click])

    async def send_input(self, inp, ms):
        if not isinstance(ms, bool):
            pydirectinput.keyDown(inp)
            await asyncio.sleep(ms/1000)
            pydirectinput.keyUp(inp)
        elif ms is False:
            pydirectinput.keyUp(inp)
        elif ms is True:
            pydirectinput.keyDown(inp)

    async def task_mouse(self, mouse, ctx: commands.Context):
        tasks = []
        for coord, click in mouse:
            tasks.append(self.mouse_event(coord, click, ctx))
        await asyncio.gather(*tasks)

    async def task_keys(self, keys, ctx: commands.Context):
        tasks = []
        for key in keys:
            tasks.append(self.send_input(key[0], key[1]))
        await asyncio.gather(*tasks)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Send a hello back!
        await ctx.send(f'Hello {ctx.author.name}!')