import os
import hashlib
import sys
from dotenv import dotenv_values

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import get_settings

def fingerprint(val):
    if not val: return "None"
    val = val.strip()
    if len(val) < 8: return "too short"
    h = hashlib.sha256(val.encode()).hexdigest()
    return f"{val[:4]}...{val[-4:]} (SHA256: {h})"

print("=== OS ENV ===")
os_val = os.environ.get('WEATHER_API_KEY')
print("In os.environ:", fingerprint(os_val) if os_val else "Not set")

print("=== .env FILES ===")
root_env = dotenv_values("../.env")
print("Root .env:", fingerprint(root_env.get('WEATHER_API_KEY')))

backend_env = dotenv_values(".env")
print("Backend .env:", fingerprint(backend_env.get('WEATHER_API_KEY')))

print("=== PYDANTIC SETTINGS ===")
settings = get_settings()
print("Loaded by backend:", fingerprint(settings.weather_api_key))
