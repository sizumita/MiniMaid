from discord.opus import Decoder as DiscordDecoder


class Decoder(DiscordDecoder):
    @staticmethod
    def packet_get_nb_channels(data: bytes) -> int:
        return 2
