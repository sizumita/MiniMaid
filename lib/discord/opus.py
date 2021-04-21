# type: ignore
import asyncio
from io import BytesIO
import wave
import struct
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import time

from discord.opus import Decoder


class PacketBase:
    def is_rpc(self) -> bool:
        return False


class RTPPacket(PacketBase):
    def __init__(self, header: bytes, decrypted: bytes):
        self.version = (header[0] & 0b11000000) >> 6
        self.padding = (header[0] & 0b00100000) >> 5
        self.extend = (header[0] & 0b00010000) >> 4
        self.cc = header[0] & 0b00001111
        self.marker = header[1] >> 7
        self.payload_type = header[1] & 0b01111111
        self.offset = 0
        self.ext_length = None
        self.ext_header = None
        self.csrcs = None
        self.profile = None

        self.header = header
        self.decrypted = decrypted
        self.seq, self._timestamp, self.ssrc = struct.unpack_from('>HII', header, 2)

    def calc_extention_header_length(self, data: bytes) -> None:
        if self.cc:
            self.csrcs = struct.unpack_from(
                '>%dI' % self.cc, data, self.offset)  # type: ignore
            self.offset += self.cc * 4
        if self.extend:
            self.profile, self.ext_length = struct.unpack_from(
                '>HH', data)
            self.ext_header = struct.unpack_from(
                '>%dI' % self.ext_length, data, 4)
            self.offset += self.ext_length * 4 + 4
        self.decrypted = self.decrypted[self.offset:]

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
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.executor = ThreadPoolExecutor(10)
        self.queue: asyncio.Queue = asyncio.Queue(10 ^ 3)
        self.task = None
        self.decoder = Decoder()
        self.decoded = asyncio.Event()
        self.last_timestamp = None
        self.file = BytesIO()
        self.unix_timestamp = None

    async def decode_task(self) -> None:
        self.decoded.clear()
        wav = wave.open(self.file, "w")
        wav.setnchannels(Decoder.CHANNELS)
        wav.setsampwidth(Decoder.SAMPLE_SIZE // Decoder.CHANNELS)
        wav.setframerate(Decoder.SAMPLING_RATE)

        try:
            while True:
                packet = await self.queue.get()

                if len(packet.decrypted) < 10:
                    self.unix_timestamp = time.time()
                    continue

                data = self.decoder.decode(packet.decrypted)
                if self.last_timestamp is not None:
                    blank = (packet.timestamp - self.last_timestamp) / Decoder.SAMPLING_RATE
                    t = time.time()
                    if blank > 0.02 or (t - self.unix_timestamp) > 0.5:
                        margin = b'\0' * int((t - self.unix_timestamp) * Decoder.SAMPLING_RATE * Decoder.CHANNELS)
                        await self.loop.run_in_executor(self.executor, partial(wav.writeframes, margin))
                wav.writeframes(data)
                self.last_timestamp = packet.timestamp
                self.unix_timestamp = time.time()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(e)
        finally:
            wav.close()
            self.file.seek(0)
            self.decoded.set()

    async def push(self, packet: PacketBase) -> None:
        await self.queue.put(packet)

    def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()

    def start(self) -> None:
        self.task = self.loop.create_task(self.decode_task())

    def clean(self) -> None:
        self.file = BytesIO()
        self.task = None
        self.unix_timestamp = None
        self.last_timestamp = None
