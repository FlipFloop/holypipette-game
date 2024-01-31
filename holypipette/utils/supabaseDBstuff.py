from supabase import create_client, Client
url: str = "https://tqovnhganyopddqphwda.supabase.co"
# url: str = os.environ.get("SUPABASE_URL")
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxb3ZuaGdhbnlvcGRkcXBod2RhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDY3MzcwNzcsImV4cCI6MjAyMjMxMzA3N30._q6AOTckJaZ00M0Pb5t6PpLo3LTsWQNN1rPNkKKevhs"
# key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
# data = supabase.table("movements").insert({ "device_id": 32432, "x": 43, "y": 423, "z": 231}).execute()
print(f"Supbase instance : {supabase}")