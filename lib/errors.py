from lib.context import Context


class MiniMaidException(Exception):
    async def send(self, ctx: Context) -> None:
        raise NotImplemented


class BotNotConnected(MiniMaidException):
    async def send(self, ctx: Context) -> None:
        await ctx.error("このサーバーではボイスチャンネルに接続していません。")


class UserNotConnected(MiniMaidException):
    async def send(self, ctx: Context) -> None:
        await ctx.error("VCに接続した状態で実行してください。")


class NoStageChannel(MiniMaidException):
    async def send(self, ctx: Context) -> None:
        await ctx.error("この機能はステージチャンネルに対応していません。")
