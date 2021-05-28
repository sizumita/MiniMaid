# type: ignore
import asyncio
from functools import partial
from io import BytesIO
import wave
import struct
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import time
from collections import defaultdict
from itertools import zip_longest
import logging

from .opus import Decoder, OpusError

logger = logging.getLogger(__name__)


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
        self.real_time = None

        self.header = header
        self.decrypted = decrypted
        self.seq, self._timestamp, self.ssrc = struct.unpack_from('>HII', header, 2)

    def set_real_time(self):
        self.real_time = time.time()

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

        try:
            if self.decrypted[offset + 1] in [0, 2]:
                offset += 1
        except IndexError:
            self.decrypted = None
            return
        self.decrypted = data[offset + 1:]

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


class SsrcPacketQueue:
    def __init__(self):
        self.queue = defaultdict(list)

    async def push(self, packet: RTPPacket) -> None:
        self.queue[packet.ssrc].append(packet)

    def get(self) -> dict:
        return self.queue


class PacketQueue:
    MAX_SRC = 65535

    def __init__(self, data: list):
        self.queue = data
        self.last_seq = None

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


class ResultPCM:
    def __init__(self, data: list, start_time: int) -> None:
        self.data = data
        self.start_time = start_time

    def add_margin(self, diff: float) -> None:
        byte_count = int(48000 * 2 * diff)  # 周波数 * bit数 * チャンネル数
        self.data = ([0] * byte_count) + self.data


class BufferDecoder:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.executor = ThreadPoolExecutor(10)
        self.task = None
        self.decoded = asyncio.Event()
        self.queue = SsrcPacketQueue()
        self.ssrc = {}

    def is_speaker(self, ssrc: int) -> bool:
        return ssrc in self.ssrc.keys()

    def add_ssrc(self, data: dict) -> None:
        self.ssrc[data["ssrc"]] = data["user_id"]

    async def decode_to_pcm(self):
        pcm_list = []
        c = 0
        for ssrc, packets in self.queue.get().items():
            if c > 15:
                break
            queue = PacketQueue(packets)
            try:
                pcm: ResultPCM = await self.decode_one(queue)
            except OpusError:
                return None
            pcm_list.append(pcm)
            c += 1
        pcm_list.sort(key=lambda x: x.start_time)
        if not pcm_list:
            return None
        first_time = pcm_list[0].start_time
        for pcm in pcm_list:
            await self.loop.run_in_executor(self.executor, partial(pcm.add_margin, pcm.start_time - first_time))

        right_channel = []
        left_channel = []

        i = 0
        for bytes_ in zip_longest(*map(lambda x: x.data, pcm_list)):
            result = 0
            for b in bytes_:
                if b is None:
                    continue
                if result < 0 and b < 0:
                    result = result + b - (result * b * -1)
                elif result > 0 and b > 0:
                    result = result + b - (result * b)
                else:
                    result = result + b
            if result > 1:
                if not i % 2:
                    right_channel.append(1)
                else:
                    left_channel.append(1)
            elif result < -1:
                if not i % 2:
                    right_channel.append(-1)
                else:
                    left_channel.append(-1)
            else:
                if not i % 2:
                    right_channel.append(result)
                else:
                    left_channel.append(result)
            i += 1

        left_len = len(left_channel)
        right_len = len(right_channel)
        if left_len != right_len:
            if not left_len % 2:
                if left_len > right_len:
                    right_channel += [0] * (left_len - right_len)
                else:
                    right_channel = right_channel[:left_len]
            elif not right_len % 2:
                if right_len > left_len:
                    left_channel += [0] * (right_len - left_len)
                else:
                    left_channel = left_channel[:right_len]

        audio = np.array([left_channel, right_channel]).T

        # Convert to (little-endian) 16 bit integers.
        audio = (audio * (2 ** 15 - 1)).astype(np.int16)
        return audio.tobytes()

    async def decode(self):

        file = BytesIO()
        wav = wave.open(file, "wb")
        wav.setnchannels(Decoder.CHANNELS)
        wav.setsampwidth(Decoder.SAMPLE_SIZE // Decoder.CHANNELS)
        wav.setframerate(Decoder.SAMPLING_RATE)

        audio = await self.decode_to_pcm()
        if audio is None:
            return None

        wav.writeframes(audio)
        wav.close()
        file.seek(0)

        return file

    async def decode_one(self, queue: PacketQueue):
        decoder = Decoder()
        pcm = []
        start_time = None

        last_timestamp = None

        while True:
            packet: RTPPacket = await queue.pop()
            if packet is None:
                break
            if packet == -1:
                data = decoder.decode_float(None)
                pcm += data
                last_timestamp = None
                continue
            if start_time is None:
                start_time = packet.real_time
            else:
                start_time = min(packet.real_time, start_time)

            if packet.decrypted is None:
                data = await self.loop.run_in_executor(self.executor, partial(decoder.decode_float, packet.decrypted))
                pcm += data
                last_timestamp = packet.timestamp
                continue

            if len(packet.decrypted) < 10:
                last_timestamp = packet.timestamp
                continue

            if last_timestamp is not None:
                elapsed = (packet.timestamp - last_timestamp) / Decoder.SAMPLING_RATE
                if elapsed > 0.02:
                    margin = [0] * 2 * int(Decoder.SAMPLE_SIZE * (elapsed - 0.02) * Decoder.SAMPLING_RATE)
                    # await self.loop.run_in_executor(self.executor, partial(pcm.append, margin))
                    pcm += margin
            try:
                data = await self.loop.run_in_executor(self.executor, partial(decoder.decode_float, packet.decrypted))
            except Exception:
                logger.error(f"{packet.cc=}")
                logger.error(f"{packet.extend=}")
                raise
            pcm += data
            last_timestamp = packet.timestamp

        del decoder
        return ResultPCM(pcm, start_time)

    async def push(self, packet: PacketBase) -> None:
        await self.queue.push(packet)

    def clean(self) -> None:
        self.queue = SsrcPacketQueue()
        self.ssrc = {}
