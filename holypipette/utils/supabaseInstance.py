from supabase import create_client, Client
import hashlib
import machineid
from dotenv import load_dotenv
import os 

load_dotenv()

local_device_ID = machineid.id()
print(local_device_ID)

h = hashlib.sha256()
h.update(local_device_ID.encode()) # give a encoded string. Makes the String to the Hash 
hashed_ID:str = h.hexdigest() # gets the Hash
print(hashed_ID)


# Get environment variables
url: str = os.environ.get("SUPABASE_URL")
# print(url)
key: str = os.environ.get("SUPABASE_KEY")
# print(key)
supabase: Client = create_client(url, key)
print(f"Supbase instance : {supabase}")