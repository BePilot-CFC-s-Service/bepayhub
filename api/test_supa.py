# test_supabase.py
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("URL:", url)
print("Key prefix:", key[:20] if key else "VAZIA")

try:
    client = create_client(url, key)
    print("Cliente criado com sucesso!")
except Exception as e:
    print("Erro:", e)