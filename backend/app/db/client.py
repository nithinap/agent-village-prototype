import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_url = os.environ["SUPABASE_URL"]
_key = os.environ["SUPABASE_SERVICE_KEY"]

supabase: Client = create_client(_url, _key)
