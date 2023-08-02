import simpleobsws
import asyncio

class OBSWebsocketManager:
    def __init__(self, host='localhost', port=4455, password=None):
        self.host = host
        self.port = port
        self.password = password
        self.obs_ws = None
        asyncio.ensure_future(self.connect())

    async def connect(self):
        try:
            parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False) # Create an IdentificationParameters object (optional for connecting)
            self.obs_ws = simpleobsws.WebSocketClient(url=f"ws://{self.host}:{self.port}", password=self.password, identification_parameters=parameters)
            await self.obs_ws.connect()
            await self.obs_ws.wait_until_identified()
        except Exception as e:
            print(f"Failed to connect to OBS Studio: {str(e)}")

    async def disconnect(self):
        if self.obs_ws is not None:
            await self.obs_ws.disconnect()

    async def change_text_source(self, source, text):
        if self.obs_ws is None or not self.obs_ws.identified:
            print("Please connect to OBS Studio first.")
            return

        try:
            request = simpleobsws.Request(requestType='SetInputSettings', requestData={'inputName': source, "inputSettings" : {'text': text}})
            response = await self.obs_ws.call(request)
            if response.ok():
                pass
            else:
                print(f"Failed to change text: {response.requestStatus.comment}")
        except simpleobsws.NotIdentifiedError:
            print("Please wait until OBS Studio is identified before making requests.")
        except simpleobsws.MessageTimeout as e:
            print(f"Failed to change text: {str(e)}")