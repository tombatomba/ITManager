import json
import os
from datetime import datetime, timezone

LOG_FILE = "chat_logs.jsonl"  # JSON Lines format, svaki call u novom redu

print(os.path.abspath(LOG_FILE))

def log_chat(prompt: str, response_text: str, total_tokens: int, model: str):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model":model,
        "prompt": prompt,
        "response": response_text,
        "tokens": total_tokens
    }

    try:
        # append to file
        print('proba da upise')
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            #print('zavrsio pisanje')
    except Exception as e:
        # samo odštampaj grešku, aplikacija nastavlja sa radom
        print(f"[WARNING] Failed to log chat entry: {e}")
        print('pukao')

