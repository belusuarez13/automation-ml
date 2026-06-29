import requests

TOKEN = "8747785658:AAHsNJyy604ChFyGMFhBNuFM7HPmA2j2zSI"
URL = f"https://api.telegram.org/bot{TOKEN}"

updates = requests.get(f"{URL}/getUpdates").json()
print(updates)