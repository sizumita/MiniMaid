import asyncio
from io import BytesIO
import wave
import struct
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from discord.opus import Decoder


class PacketBase:
    def is_rpc(self) -> bool:
        return False


class RTPPacket(PacketBase):
    def __init__(self, header: bytes, decrypted: bytes):
        self.header = header
        self.decrypted = decrypted
        self.seq, self._timestamp, self.ssrc = struct.unpack_from('>HII', header, 2)

    @property
    def timestamp(self):
        return self._timestamp


class RTCPPacket(PacketBase):
    def __init__(self, data: bytes):
        self.data = data[8:]
        self.header = data[:8]
        self.decrypted = None

    def is_rpc(self) -> bool:
        return True


class BufferDecoder:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.executor = ThreadPoolExecutor(10)
        self.queue = asyncio.Queue(10 ^ 3)
        self.task = None
        self.decoder = Decoder()
        self.decoded = asyncio.Event()
        self.last_timestamp = None
        self.file = BytesIO()

    async def decode_task(self):
        self.file.seek(0)
        wav = wave.open(self.file, "w")
        wav.setnchannels(Decoder.CHANNELS)
        wav.setsampwidth(Decoder.SAMPLE_SIZE//Decoder.CHANNELS)
        wav.setframerate(Decoder.SAMPLING_RATE)

        try:
            while True:
                packet = await self.queue.get()

                if len(packet.decrypted) < 10:
                    continue

                data = self.decoder.decode(packet.decrypted)
                if self.last_timestamp is not None:
                    blank = (packet.timestamp - self.last_timestamp) / Decoder.SAMPLING_RATE
                    if blank > 0.02:
                        margin = bytes(2 * int(Decoder.SAMPLE_SIZE *
                                               (blank - 0.02) *
                                               Decoder.SAMPLING_RATE))
                        await self.loop.run_in_executor(self.executor, partial(wav.writeframes, margin))
                wav.writeframes(data)
                self.last_timestamp = packet.timestamp
        except asyncio.CancelledError:
            pass
        finally:
            wav.close()
            self.file.seek(0)
            self.decoded.set()

    async def push(self, packet: PacketBase) -> None:
        await self.queue.put(packet)

    def stop(self):
        if self.task is not None:
            self.task.cancel()
        self.file.seek(0)

    def start(self):
        self.task = self.loop.create_task(self.decode_task())
