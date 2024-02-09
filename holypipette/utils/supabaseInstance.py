from supabase import create_client, Client
# import hashlib
# import machineid
import os

# local_device_ID = machineid.id()
# print(local_device_ID)

# h = hashlib.sha256()
# h.update(local_device_ID.encode()) # give a encoded string. Makes the String to the Hash 
# hashed_ID:str = h.hexdigest() # gets the Hash
# print(hashed_ID)


# Set environment variables
# Get environment variables
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")
url: str = "https://tqovnhganyopddqphwda.supabase.co"
# url: str = os.environ.get("SUPABASE_URL")
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxb3ZuaGdhbnlvcGRkcXBod2RhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDY3MzcwNzcsImV4cCI6MjAyMjMxMzA3N30._q6AOTckJaZ00M0Pb5t6PpLo3LTsWQNN1rPNkKKevhs"
supabase: Client = create_client(url, key)
# data = supabase.table("movements").insert({ "device_id": 32432, "x": 43, "y": 423, "z": 231}).execute()
print(f"Supbase instance : {supabase}")