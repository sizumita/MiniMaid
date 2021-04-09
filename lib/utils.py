import discord


async def try_send_error_message(guild: discord.Guild, error) -> bool:
    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).send_messages:
            continue
        await channel.send(error)
        return True
    try:
        await guild.owner.send(error)
        return True
    except discord.Forbidden:
        return False
