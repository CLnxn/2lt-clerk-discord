
import discord
from discord.app_commands import CommandTree, Choice, checks, describe, choices
from commands.commands import base
import logging
from validation.validator import datestring_validator
class command(base):
    ACTIONS_TIMEOUT = 60.0
    def subscribe(self, tree: CommandTree):
        super().subscribe(tree)
        
        @tree.command(name="ord", description="When do you ord?")
        @describe(actions="What should I do?")
        @choices(actions=[
            Choice(name='when', value=1),
            Choice(name='set', value=2),
            Choice(name='who', value=3)

        ])
        @checks.cooldown(2.0,1.0)
        async def ord(interaction: discord.Interaction, actions: Choice[int]):
            
            channel = interaction.channel
            if actions.name == 'when':
                # call to /when endpoints to retrieve data
                date = "insert_date_here"
                remaining_days = 0
                await interaction.response.send_message(f"You will ord in {remaining_days} days on: {date}")

            elif actions.name == 'set':

                await interaction.response.send_message("What is your ORD date? Please use DD/MM/YYYY format!")
                
                msg = await tree.client.wait_for(
                    'message', 
                    timeout=self.ACTIONS_TIMEOUT, 
                    check=self.init_msg_check(channel.id,interaction.user))
                
                validation_result, obj = datestring_validator(msg.content)

                if not validation_result:
                    await channel.send("Oh no, the date format seems incorrect. Do check again.")
                    return
                # call to /set endpoint to set data
                
                
                await channel.send("ORD Date set!")

                
            elif actions.name == 'who':
                await interaction.response.send_message("Who's ord date are you curious about?")
