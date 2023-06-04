import discord
from datetime import datetime
import utility.datetools as datetools
emojiIDMap = {
    11:":one:",
    12:":two:",
    13:"5093_keycap_thirteen_emoji",
    14:"2745_keycap_fourteen_emoji",
    15:"7072_keycap_fifteen_emoji",
    16:"1260_keycap_sixteen_emoji",
    17:"9952_keycap_seventeen_emoji",
    18:"7821_keycap_eighteen",
    19:"8133_keycap_nineteen_emoji",
    20:"5178_keycap_twenty_emoji"

    
}
def getDayOfMonthEmojis(date: datetime):
    days = datetools.get_last_day_of_mth(date)
    emojis = [0]*5 # replace 5 with days
    for i in range(5):
        emojis[i] = discord.Emoji(emojiIDMap[i+11])

