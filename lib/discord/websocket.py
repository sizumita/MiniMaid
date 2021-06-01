from typing import TYPE_CHECKING, Optional
import asyncio
from aiohttp import ClientWebSocketResponse
from io import BytesIO
import sys
import struct
import time

from discord.gateway import DiscordVoiceWebSocket
import nacl.secret

from lib.discord.buffer_decoder import BufferDecoder, RTPPacket
from lib.discord.ring_buffer import RingBuffer

if TYPE_CHECKING:
    from bot import MiniMaid


class MiniMaidVoiceWebSocket(DiscordVoiceWebSocket):
    def __init__(self, websocket: ClientWebSocketResponse, loop: asyncio.AbstractEventLoop, hook=None) -> None:
        super().__init__(websocket, loop, hook=hook)
        self.can_record = False
        self.box: Optional[nacl.secret.SecretBox] = None
        self.decoder = BufferDecoder(self.loop)
        self.replay_decoder = BufferDecoder(self.loop)
        self.record_task = None
        self.is_recording = False
        self.ring_buffer = RingBuffer()

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

    async def receive_audio_packet(self) -> None:
        try:
            state = self._connection
            while True:
                recv = await self.loop.sock_recv(state.socket, 2 ** 16)
                if not self.is_recording:
                    if 200 <= recv[1] <= 204:
                        continue
                    seq, timestamp, ssrc = struct.unpack_from('>HII', recv, 2)
                    self.ring_buffer.append(ssrc, dict(time=time.time(), data=recv))
                    continue
                decrypt_fn = getattr(self, f'decrypt_{state.mode}')
                header, data = decrypt_fn(recv)
                if 200 <= recv[1] <= 204:
                    continue
                packet = RTPPacket(header, data)
                packet.calc_extention_header_length(data)
                packet.set_real_time()
                await self.decoder.push(packet)
        except Exception as e:
            print(e)
            print("error at record")
            print(sys.exc_info())

    async def replay(self) -> BytesIO:
        self.box = nacl.secret.SecretBox(bytes(self._connection.secret_key))
        state = self._connection
        self.is_recording = True
        try:
            items = self.ring_buffer.get_all_items(time.time() - 30)
            self.replay_decoder.clean()

            for item in items:
                decrypt_fn = getattr(self, f'decrypt_{state.mode}')
                header, data = decrypt_fn(item['data'])
                packet = RTPPacket(header, data)
                packet.calc_extention_header_length(data)
                packet.real_time = item['time']
                await self.replay_decoder.push(packet)
        finally:
            self.is_recording = False

        return await self.replay_decoder.decode()

    async def record(self, bot: 'MiniMaid', is_invent: bool = False) -> BytesIO:
        self.decoder.clean()
        self.box = nacl.secret.SecretBox(bytes(self._connection.secret_key))

        self.is_recording = True
        try:
            await bot.wait_for("record_stop", timeout=None if is_invent else 30)
        except asyncio.TimeoutError:
            pass
        self.ring_buffer.clear()
        self.is_recording = False

        return await self.decoder.decode()

    async def received_message(self, msg: dict) -> None:
        await super(MiniMaidVoiceWebSocket, self).received_message(msg)

        op = msg['op']
        data = msg.get('d')

        if op == 4:
            self.can_record = True
            self.record_task = self.loop.create_task(self.receive_audio_packet())
        elif op == 5:
            if self.is_recording:
                self.decoder.add_ssrc(data)

    async def close(self, code: int = 1000) -> None:
        if self.record_task is not None:
            self.record_task.cancel()
        await super(MiniMaidVoiceWebSocket, self).close(code)
