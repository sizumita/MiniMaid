import io
from typing import Optional
from datetime import datetime

import discord


class RecorderModel:
    def __init__(self):
        self.file: Optional[io.BytesIO] = None
        self.filename = f"{datetime.now().timestamp()}.wav"

    def make_file(self):
        return discord.File(self.file, self.filename)
