import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json") as response:
    schema = json.load(response)

for path, methods in schema["paths"].items():
    if "labor" in path.lower():
        print(path, "->", ", ".join(method.upper() for method in methods))
