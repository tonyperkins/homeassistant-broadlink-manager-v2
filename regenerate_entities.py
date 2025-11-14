#!/usr/bin/env python3
import requests
import json

response = requests.post('http://localhost:8099/api/entities/generate', json={})
print(json.dumps(response.json(), indent=2))
