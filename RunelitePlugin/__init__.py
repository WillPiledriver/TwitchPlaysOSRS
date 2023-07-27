import json
import websockets
import asyncio

class RunelitePlugin():
    def __init__(self, url) -> None:
        self.server_url = url
        self.websocket = None
        self.event_handlers = {}
        asyncio.ensure_future(self.connect_websocket())
    
    def event(self, name):
        # Decorator function that takes the event name
        def decorator(func):
            # Inner decorator to wrap the event handler function
            async def async_wrapper(data):
                await func(data)  # Ensure you await the async function inside the event handler

            self.event_handlers[name] = async_wrapper  # Store the event handler
            return async_wrapper
        return decorator
    
    async def send(self, message):
        print(message)
        await self.websocket.send(message)

    async def on_message(self, message):
        m = json.loads(message)
        if m["response"] is None:
            return
        
        event_name = m.get("action")
        handler = self.event_handlers.get(event_name)
        if handler:
            await handler(m)
        else:
            print(f"Received message: {message}")

    async def on_error(self, error):
        print(f"Error: {error}")

    async def on_close(self):
        print("Connection closed")

    async def on_open(self, websocket):
        print("Connection established")

    async def connect_websocket(self):
        try:
            async with websockets.connect(self.server_url) as self.websocket:
                await self.on_open(self.websocket)
                async for message in self.websocket:
                    await self.on_message(message)
        except asyncio.CancelledError:
            await self.on_close()