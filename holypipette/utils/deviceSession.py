from hashlib import sha256
import machineid
from uuid import uuid4
from datetime import datetime

from .supabaseInstance import supabase

h = sha256()
h.update(machineid.id().encode()) # give a encoded string. Makes the String to the Hash 
hashed_ID: str = h.hexdigest() # gets the Hash
# print(hashed_ID)

local_time = datetime.now().isoformat()
print(local_time)

sessionID = str(uuid4())
print(f"Session: {sessionID}")





