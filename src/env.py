import os, dotenv
dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB = {'user':os.getenv('DB_USER'), 
      'password':os.getenv('DB_PASSWORD'),
      'host':os.getenv('DB_HOST'),
      'database':os.getenv('DB_NAME')  
      }