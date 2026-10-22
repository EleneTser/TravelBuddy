import json
import urllib.request

with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
    models = json.load(r)["data"]

for m in models:
    p = m.get("pricing", {})
    if p.get("prompt") == "0" and p.get("completion") == "0":
        print(m["id"])