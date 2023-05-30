import discord
class base():
    def subscribe(self, tree: discord.app_commands.CommandTree):
        pass
    
    def init_msg_check(self, channel_id: int, user: discord.User | discord.Member):
        def msg_check(message: discord.Message):
            # logging.debug(f"is same channel: {message.channel.id == channel_id}, {channel_id}")
            is_same_channel = message.channel.id == channel_id
            is_same_author = message.author == user 
            return is_same_channel and is_same_author
        return msg_check