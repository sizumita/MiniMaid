import discord
from lib.mpg123 import Mpg123
import audioop
import io
import wave
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio


def remove_header(content: bytes) -> bytes:
    with wave.open(io.BytesIO(content)) as wav:
        bit = wav.getsampwidth()
        pcm = wav.readframes(wav.getnframes())
        if bit != 2:
            pcm = audioop.lin2lin(pcm, bit, 2)

        if wav.getnchannels() == 1:
            pcm = audioop.tostereo(pcm, 2, 1, 1)
        if wav.getframerate() != 48000:
            pcm = audioop.ratecv(pcm, 2, 2, wav.getframerate(), 48000, None)[0]

    return discord.PCMAudio(io.BytesIO(pcm))


def mp3_to_pcm(raw: bytes) -> bytes:
    mp3 = Mpg123()
    mp3.feed(raw)
    rate, channels, encoding = mp3.get_format()
    data = b""
    for frame in mp3.iter_frames():
        data += frame
    if rate != 48000:
        data = audioop.ratecv(data, 2, channels, rate, 48000, None)[0]

    return discord.PCMAudio(io.BytesIO(data))


class AudioEngine:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.executor = ThreadPoolExecutor()

    async def create_source(self, attachment: discord.Attachment) -> discord.PCMAudio:
        raw = await attachment.read()
        if attachment.filename.endswith(".mp3"):
            data = await self.loop.run_in_executor(self.executor, partial(mp3_to_pcm, raw))
        else:
            data = await self.loop.run_in_executor(self.executor, partial(remove_header, raw))

        return discord.PCMVolumeTransformer(data, volume=0.6)
