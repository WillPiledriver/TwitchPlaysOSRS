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
        self.rcv_message = None

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')

    async def event_message(self, ctx: commands.Context):
        if ctx.echo:
            return
        command = ctx.content.lower()
        print(command)
        
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
        ctx_content_list = ctx.content.split()
        ctx_content_list[0] = ctx_content_list[0].lower()
        ctx.content = " ".join(ctx_content_list)

        await self.handle_commands(ctx)
        await self.rcv_message(ctx)

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
        tasks = [self.send_input(key[0], key[1]() if callable(key[1]) else key[1]) for key in keys]
        await asyncio.gather(*tasks)

    async def type_human(self, inp):
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}\\|;:'\",.?/`~ ")
        shift_keys = set("!@#$%^&*()_+{}|:\"?~QWERTYUIOPASDFGHJKLZXCVBNM")
        inp = ''.join(char for char in inp if char in allowed_chars)
        count = 0
        shift = False
        for c in inp:
            if c in shift_keys:
                shift = True
                pydirectinput.keyDown("shift")
                await asyncio.sleep(random.uniform(0.02, 0.04))
            pydirectinput.keyDown(c)
            await asyncio.sleep(random.uniform(0.03, 0.05))
            pydirectinput.keyUp(c)
            await asyncio.sleep(random.uniform(0.05, 0.075))
            print(c, count, len(inp))
            if len(inp) == count + 1:
                if shift:
                    shift = False
                    pydirectinput.keyUp("shift")
                return
            if inp[count + 1] not in shift_keys:
                shift = False
                pydirectinput.keyUp("shift")
                await asyncio.sleep(random.uniform(0.01, 0.025))
            count += 1

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Send a hello back!
        await ctx.reply(f'Hello {ctx.author.name}!')