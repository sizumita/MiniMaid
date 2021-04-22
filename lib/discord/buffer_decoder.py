# type: ignore
import asyncio
from io import BytesIO
import wave
import struct
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from .opus import Decoder


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
        self.unix_timestamp = None

        self.header = header
        self.decrypted = decrypted
        self.seq, self._timestamp, self.ssrc = struct.unpack_from('>HII', header, 2)

    def calc_extention_header_length(self, data: bytes) -> None:
        if not (data[0] == 0xbe and data[1] == 0xde and len(data) > 4):
            return
        self.ext_length = int.from_bytes(data[2:4], "big")
        offset = 4
        for i in range(self.ext_length):
            byte_ = data[offset]
            offset += 1
            if byte_ == 0:
                continue
            offset += 1 + (0b1111 & (byte_ >> 4))

        if self.decrypted[offset+1] in [0, 2]:
            offset += 1
        self.decrypted = data[offset+1:]

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


class PacketQueue:
    MAX_SRC = 65535

    def __init__(self):
        self.queue = []
        self.last_seq = None

    async def push(self, packet: RTPPacket):
        self.queue.append(packet)

    async def pop(self):
        if not self.queue:
            return None

        if self.last_seq is None:
            packet = self.queue.pop(0)
            self.last_seq = packet.seq
            return packet
        if self.last_seq == self.MAX_SRC:
            self.last_seq = -1
        if self.queue[0].seq - 1 == self.last_seq:
            packet = self.queue.pop(0)
            self.last_seq = packet.seq
            return packet

        for i in range(1, min(1000, len(self.queue))):
            if self.queue[i].seq - 1 == self.last_seq:
                packet = self.queue.pop(i)
                self.last_seq = packet.seq
                return packet
        self.last_seq = None
        return -1


class BufferDecoder:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.executor = ThreadPoolExecutor(10)
        self.task = None
        self.decoder = Decoder()
        self.decoded = asyncio.Event()
        self.queue = PacketQueue()

    async def decode(self):
        file = BytesIO()
        wav = wave.open(file, "wb")
        wav.setnchannels(Decoder.CHANNELS)
        wav.setsampwidth(Decoder.SAMPLE_SIZE // Decoder.CHANNELS)
        wav.setframerate(Decoder.SAMPLING_RATE)

        last_timestamp = None

        while True:
            packet: RTPPacket = await self.queue.pop()
            if packet is None:
                break
            if packet == -1:
                data = self.decoder.decode(None)
                wav.writeframes(data)
                last_timestamp = None
                continue

            if len(packet.decrypted) < 10:
                last_timestamp = packet.timestamp
                continue

            if last_timestamp is not None:
                elapsed = (packet.timestamp - last_timestamp) / \
                          Decoder.SAMPLING_RATE
                if elapsed > 0.02:
                    margin = bytes(2 * int(Decoder.SAMPLE_SIZE *
                                           (elapsed - 0.02) *
                                           Decoder.SAMPLING_RATE))
                    await self.loop.run_in_executor(self.executor, partial(wav.writeframes, margin))
            data = self.decoder.decode(packet.decrypted)
            wav.writeframes(data)
            last_timestamp = packet.timestamp

        wav.close()
        file.seek(0)
        return file

    async def push(self, packet: PacketBase) -> None:
        await self.queue.push(packet)

    def clean(self) -> None:
        self.queue = PacketQueue()
        self.decoder = Decoder()
