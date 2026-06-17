"""Test which Volcano ARK embedding models actually work."""
import urllib.request
import json

API_KEY = "ark-b3073932-b876-4adc-990c-71191e1fdf78-280ce"
URL = "https://ark.cn-beijing.volces.com/api/v3/embeddings"

models_to_test = [
    "doubao-embedding-vision-251215",
    "doubao-embedding-vision-250615",
    "doubao-embedding-large-text-250515",
    "doubao-embedding-large-text-240915",
    "doubao-embedding-text-240715",
    "doubao-embedding-text-240515",
    "doubao-embedding-vision-241215",
    "doubao-embedding-vision-250328",
]

for model in models_to_test:
    data = json.dumps({
        "model": model,
        "input": ["测试文本"]
    }).encode('utf-8')

    req = urllib.request.Request(URL, data=data)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        if 'data' in result:
            dim = len(result['data'][0]['embedding']) if result.get('data') else '?'
            print(f"✅ {model}: WORKS! (dim={dim})")
        else:
            print(f"⚠️  {model}: {str(result)[:100]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        msg = json.loads(body).get('error', {}).get('message', '')[:80]
        print(f"❌ {model}: {msg}")
    except Exception as e:
        print(f"❌ {model}: {str(e)[:80]}")
