from io import BytesIO
from typing import Optional

from discord import VoiceClient
from lib.discord.websocket import MiniMaidVoiceWebSocket


class MiniMaidVoiceClient(VoiceClient):
    async def connect_websocket(self) -> MiniMaidVoiceWebSocket:
        ws = await MiniMaidVoiceWebSocket.from_client(self)
        self._connected.clear()
        while ws.secret_key is None:
            await ws.poll_event()
        self._connected.set()
        return ws

    async def record(self) -> Optional[BytesIO]:
        return await self.ws.record(self.client)

    async def replay(self) -> Optional[BytesIO]:
        return await self.ws.replay()
