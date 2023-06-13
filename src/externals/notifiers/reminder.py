import discord
from discord import Guild
from discord.abc import GuildChannel, Messageable
from internals.api.notifier import Reminder
from internals.enums.enum import RemindersScope
from externals.exceptions.errors import error, GenericErrorType, CommandErrorType
import logging
async def on_reminder(tree: discord.app_commands.CommandTree, reminder_obj: Reminder):
    user_id = reminder_obj.user_id
    guild_id = reminder_obj.guild_id
    channel_id = reminder_obj.channel_id
    content = reminder_obj.content
    scope = reminder_obj.scope
    user = tree.client.get_user(user_id) 
    
    if scope == RemindersScope.PERSONAL:

        if not user:
            logging.error(f"unable to find user with id: {user_id}")
            return error(CommandErrorType.INVALID_USER_EXCEPTION, reminder_obj)
        # need to test for injection vulnerability
        await user.send(f"You have the following reminders: {content}")
        return

    if scope == RemindersScope.GUILD:
        if not guild_id:
            return error(CommandErrorType.INVALID_GUILD_EXCEPTION, reminder_obj)
        
        guild: Guild | None = await tree.client.get_guild(guild_id)
        
        if not guild:
            return error(CommandErrorType.INVALID_GUILD_EXCEPTION, reminder_obj)
        if not channel_id:
            return error(CommandErrorType.INVALID_CHANNEL_EXCEPTION, reminder_obj)
        channel: GuildChannel | None = await guild.get_channel(channel_id)
        if not channel:
            return error(CommandErrorType.INVALID_CHANNEL_EXCEPTION, reminder_obj)
            
        if isinstance(channel, Messageable):
            await channel.send(f"You have the following reminders: {content}")
        return
    
    if scope == RemindersScope.NO_GUILD_CHANNEL:
        if not channel_id:
            return error(CommandErrorType.INVALID_CHANNEL_EXCEPTION, reminder_obj)
        channel: GuildChannel | None = await guild.get_channel(channel_id)
        if not channel:
            return error(CommandErrorType.INVALID_CHANNEL_EXCEPTION, reminder_obj)
        if isinstance(channel, Messageable):
            await channel.send(f"You have the following reminders: {content}")
        
        

    