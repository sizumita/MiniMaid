import aiohttp

from lib.database.models import AudioTag


class TagAttachment:
    def __init__(self, audio_tag: AudioTag):
        self.tag = audio_tag
        self.filetype = audio_tag.audio_url.split(".")[-1]
        self.filename = f"{self.tag.name}.{self.filetype}"
        self.url = self.tag.audio_url

    async def read(self) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.tag.audio_url) as response:
                return await response.read()
