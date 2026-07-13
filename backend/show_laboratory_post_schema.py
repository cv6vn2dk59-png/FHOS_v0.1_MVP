import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json") as response:
    schema = json.load(response)

operation = schema["paths"]["/api/laboratory/"]["post"]

print(json.dumps(operation, indent=2, ensure_ascii=False))
