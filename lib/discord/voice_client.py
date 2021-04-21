from io import BytesIO

from discord import VoiceClient
from lib.discord.websocket import MiniMaidVoiceWebSocket


class MiniMaidVoiceClient(VoiceClient):
    async def connect_websocket(self):
        ws = await MiniMaidVoiceWebSocket.from_client(self)
        self._connected.clear()
        while ws.secret_key is None:
            await ws.poll_event()
        self._connected.set()
        return ws

    async def record(self) -> BytesIO:
        return await self.ws.receive_audio_packet(self.client)
