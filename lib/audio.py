import discord
from lib.mpg123 import Mpg123
import audioop
import io
import wave
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio


def make_pcm(content: bytes) -> io.BytesIO:
    """
    wavのファイルからヘッダーを取り除き、フレームレートなどを合わせます。
    :param content: wavのデータ
    :return: 出力するPCM
    """
    with wave.open(io.BytesIO(content)) as wav:
        bit = wav.getsampwidth()
        pcm = wav.readframes(wav.getnframes())
        if bit != 2:
            pcm = audioop.lin2lin(pcm, bit, 2)

        if wav.getnchannels() == 1:
            pcm = audioop.tostereo(pcm, 2, 1, 1)
        if wav.getframerate() != 48000:
            pcm = audioop.ratecv(pcm, 2, 2, wav.getframerate(), 48000, None)[0]

    return io.BytesIO(pcm)


def mp3_to_pcm(raw: bytes) -> io.BytesIO:
    """
    MP3のデータをPCMに変換します。
    :param raw: MP3のデータ
    :return: 出力するPCM
    """
    mp3 = Mpg123()
    mp3.feed(raw)
    rate, channels, encoding = mp3.get_format()
    data = b""
    for frame in mp3.iter_frames():
        data += frame
    if rate != 48000:
        data = audioop.ratecv(data, 2, channels, rate, 48000, None)[0]

    return io.BytesIO(data)


class AudioEngine:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.executor = ThreadPoolExecutor()

    async def to_pcm(self, raw: bytes, filetype: str) -> io.BytesIO:
        """
        データをPCMに変換します。

        :param raw: 変換するデータ
        :param filetype: 変換するデータのタイプ
        :return: 出力するPCM
        """
        if filetype == "mp3":
            return await self.loop.run_in_executor(self.executor, partial(mp3_to_pcm, raw))
        else:
            return await self.loop.run_in_executor(self.executor, partial(make_pcm, raw))

    async def create_source(self, attachment: discord.Attachment) -> discord.AudioSource:
        """
        Attachmentからdiscord.PCMAudioを作成します。

        :param attachment: 変換するアタッチメント
        :return: 出力するPCMAudio
        """
        raw = await attachment.read()

        data = await self.to_pcm(raw, "mp3" if attachment.filename.endswith(".mp3") else "wav")

        return discord.PCMVolumeTransformer(discord.PCMAudio(data), volume=0.8)
