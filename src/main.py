
import logging, discord
from env import TOKEN
from clients.appclient import AppClient 
from internals.api.internals import InternalState
def init_log(logfile = None, lvl = logging.DEBUG):
    logging.basicConfig(filename=logfile, level=lvl)
    logging.info(f'Initialised logging to file {logfile} with logging level: {lvl}')

init_log()
internals = InternalState()
internals.start()

intents = discord.Intents.default()
intents.message_content = True
client = AppClient(intents=intents)





# client.run(TOKEN)