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
