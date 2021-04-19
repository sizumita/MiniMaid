class MiniMaidException(Exception):
    def message(self) -> str:
        raise NotImplementedError


class BotNotConnected(MiniMaidException):
    def message(self) -> str:
        return "このサーバーではボイスチャンネルに接続していません。"


class UserNotConnected(MiniMaidException):
    def message(self) -> str:
        return "VCに接続した状態で実行してください。"


class NoStageChannel(MiniMaidException):
    def message(self) -> str:
        return "この機能はステージチャンネルに対応していません。"


class AudioFileNotFound(MiniMaidException):
    def message(self) -> str:
        return "タグに紐つけられているオーディオファイルが存在しません。"


class LibInitializationException(Exception):
    pass


class OpenFeedException(Exception):
    pass


class CloseException(Exception):
    pass


class OpenFileException(Exception):
    pass


class NotFeedException(Exception):
    pass


class FeedingException(Exception):
    pass


class FormatException(Exception):
    pass


class DecodeException(Exception):
    pass


class NeedMoreException(Exception):
    pass


class DoneException(Exception):
    pass


class LengthException(Exception):
    pass


class ID3Exception(Exception):
    pass
