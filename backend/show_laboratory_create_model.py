import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json") as response:
    schema = json.load(response)

model = schema["components"]["schemas"]["LaboratoryResultCreate"]

print(json.dumps(model, indent=2, ensure_ascii=False))
