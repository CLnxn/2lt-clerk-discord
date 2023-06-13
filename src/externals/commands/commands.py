import discord
from internals.api.internals import CommandApi
class base():
    def __init__(self, hooks: CommandApi) -> None:
        self.api = hooks
    def subscribeTo(self, tree: discord.app_commands.CommandTree):
        pass

    # returns a check for whether message is from same channel & author as specified in args 

    # e.g. usage: 
        #     msg = await tree.client.wait_for(
        #     'message', 
        #     timeout=self.ACTIONS_TIMEOUT, 
        #     check=self.init_msg_check(channel.id,interaction.user))
    def init_msg_check(self, channel_id: int, user: discord.User | discord.Member):
        def msg_check(message: discord.Message):
            # logging.debug(f"is same channel: {message.channel.id == channel_id}, {channel_id}")
            is_same_channel = message.channel.id == channel_id
            is_same_author = message.author == user 
            return is_same_channel and is_same_author
        return msg_check
    