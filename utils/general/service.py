# supabase service
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_PRIVATE_KEY")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

def getSupabaseClient(): # for public routes
    return create_client(url, key)

def getSupabaseServiceClient(): # for protected routes (Read,Write, View access)
    return create_client(url, service_key)