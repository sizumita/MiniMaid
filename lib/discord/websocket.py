from typing import TYPE_CHECKING, Optional
import asyncio
from aiohttp import ClientWebSocketResponse
from io import BytesIO

from discord.gateway import DiscordVoiceWebSocket
import nacl.secret

from lib.discord.buffer_decoder import BufferDecoder, RTPPacket

if TYPE_CHECKING:
    from bot import MiniMaid


class MiniMaidVoiceWebSocket(DiscordVoiceWebSocket):
    def __init__(self, websocket: ClientWebSocketResponse, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__(websocket, loop)
        self.can_record = False
        self.box: Optional[nacl.secret.SecretBox] = None
        self.decoder = BufferDecoder(self.loop)
        self.record_task = None
        self.is_recording = False

    def decrypt_xsalsa20_poly1305(self, data: bytes) -> tuple:
        if self.box is None:
            raise ValueError("box is None")
        is_rtcp = 200 <= data[1] < 205
        if is_rtcp:
            header, encrypted = data[:8], data[8:]
            nonce = bytearray(24)
            nonce[:8] = header
        else:
            header, encrypted = data[:12], data[12:]
            nonce = bytearray(24)
            nonce[:12] = header
        return header, self.box.decrypt(bytes(encrypted), bytes(nonce))

    def decrypt_xsalsa20_poly1305_suffix(self, data: bytes) -> tuple:
        if self.box is None:
            raise ValueError("box is None")
        is_rtcp = 200 <= data[1] < 205
        if is_rtcp:
            header, encrypted, nonce = data[:8], data[8:-24], data[-24:]
        else:
            header, encrypted, nonce = data[:12], data[12:-24], data[-24:]
        return header, self.box.decrypt(bytes(encrypted), bytes(nonce))

    def decrypt_xsalsa20_poly1305_lite(self, data: bytes) -> tuple:
        if self.box is None:
            raise ValueError("box is None")
        is_rtcp = 200 <= data[1] < 205
        if is_rtcp:
            header, encrypted, _nonce = data[:8], data[8:-4], data[-4:]
        else:
            header, encrypted, _nonce = data[:12], data[12:-4], data[-4:]
        nonce = bytearray(24)
        nonce[:4] = _nonce
        return header, self.box.decrypt(bytes(encrypted), bytes(nonce))

    async def record(self) -> None:
        try:
            state = self._connection
            while True:
                recv = await self.loop.sock_recv(state.socket, 2 ** 16)
                if not self.is_recording:
                    continue
                decrypt_fn = getattr(self, f'decrypt_{state.mode}')
                header, data = decrypt_fn(recv)
                if 200 <= header[1] <= 204:
                    continue
                packet = RTPPacket(header, data)
                packet.calc_extention_header_length(data)
                await self.decoder.push(packet)
        except Exception as e:
            import sys
            print("error at record")
            print(sys.exc_info())

    async def receive_audio_packet(self, bot: 'MiniMaid') -> BytesIO:
        self.decoder.clean()
        self.box = nacl.secret.SecretBox(bytes(self._connection.secret_key))

        self.is_recording = True
        try:
            await bot.wait_for("record_stop", timeout=30)
        except asyncio.TimeoutError:
            pass
        self.is_recording = False

        return await self.decoder.decode()

    async def received_message(self, msg: dict) -> None:
        await super(MiniMaidVoiceWebSocket, self).received_message(msg)

        op = msg['op']

        if op == 4:
            self.can_record = True
            self.record_task = self.loop.create_task(self.record())

    async def close(self, code: int = 1000) -> None:
        if self.record_task is not None:
            self.record_task.cancel()
        await super(MiniMaidVoiceWebSocket, self).close(code)
