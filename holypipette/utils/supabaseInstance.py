import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import os
# load_dotenv()

extDataDir = os.getcwd()
if getattr(sys, 'frozen', False):
    extDataDir = sys._MEIPASS
load_dotenv(dotenv_path=os.path.join(extDataDir, '.env'))
# Get environment variables
url: str = os.environ.get("SUPABASE_URL")
# print(url)
key: str = os.environ.get("SUPABASE_KEY")
# print(key)
supabase: Client = create_client(url, key)
# print(f"Supbase instance : {supabase}")