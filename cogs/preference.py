from discord.ext import commands
import discord
from sqlalchemy.future import select
from typing import TYPE_CHECKING
from lib.database.models import Preference
from lib.utils import try_send_error_message

if TYPE_CHECKING:
    from bot import MiniMaid

SUGGEST_ADMINISTRATOR = "自動で退出します。再度権限を確認してから導入してください。管理者権限を付与することを推奨します。"

CANNOT_CREATE_CHANNEL = "チャンネル作成権限が存在しないため、専用チャンネルを作成できませんでした。\n" + SUGGEST_ADMINISTRATOR

CANNOT_SEND_MESSAGE = "メッセージを送信する権限が存在しませんでした。\n" +  SUGGEST_ADMINISTRATOR


class PreferenceCog(commands.Cog):
    def __init__(self, bot: 'MiniMaid') -> None:
        self.bot = bot

    async def greeting(self, channel) -> None:
        embed = discord.Embed(
            title="MiniMaidへようこそ",
            description="MiniMaidは、小規模サーバーに適した便利Botです。音楽の再生やダイス、チーム分けなどの機能があります。",
            colour=discord.Colour.blue()
        )
        embed.add_field(
            name="ヘルプコマンド",
            value="このチャンネルに`help`と送信することで表示できます。コマンド一覧はhelpコマンドを使用してください。",
            inline=False
        )
        embed.add_field(
            name="招待URL",
            value=f"[サーバーに招待する](https://discord.com/api/oauth2/authorize?"
                  f"client_id={self.bot.user.id}&permissions=8&scope=bot)",
            inline=False
        )
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await try_send_error_message(channel.guild, CANNOT_SEND_MESSAGE)

    @commands.Cog.listener(name="on_guild_join")
    async def create_preference(self, guild: discord.Guild) -> None:
        async with self.bot.db.Session() as session:
            sql = select(Preference).where(Preference.guild_id == guild.id)
            result = await session.execute(sql)
            data = result.scalars().first()

            # if preference has already created
            if data is not None:
                return
            await session.commit()

            try:
                new_channel = await guild.create_text_channel(
                    name="minimaid-control",
                    topic="MiniMaid操作用のチャンネルです。このチャンネルは自動生成されました。"
                )
            except discord.Forbidden:
                await try_send_error_message(guild, CANNOT_CREATE_CHANNEL)
                await guild.leave()
                return

            async with session.begin():
                pref = Preference(guild_id=guild.id, command_channel_id=new_channel.id)
                session.add(pref)

        await self.greeting(new_channel)


def setup(bot):
    return bot.add_cog(PreferenceCog(bot))
