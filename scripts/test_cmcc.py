import urllib.request, json, time

with open(r"C:\Users\Administrator\.openclaw\workspace\tvbox\sources\china.json", "r", encoding="utf-8") as f:
    data = json.load(f)

channels = data["channels"]
print(f"Testing {len(channels)} channels...")

ok_list = []
fail_list = []

for i, ch in enumerate(channels[:10]):
    url = ch["url"]
    name = ch["name"]
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        start = time.time()
        resp = urllib.request.urlopen(req, timeout=8)
        elapsed = time.time() - start
        ct = resp.headers.get("Content-Type", "")
        print(f"OK  [{i+1}] {name}: {ct} ({elapsed:.1f}s)")
        ok_list.append(ch)
    except Exception as e:
        print(f"FAIL[{i+1}] {name}: {str(e)[:50]}")
        fail_list.append(ch)

print(f"\nResult: {len(ok_list)}/{len(channels[:10])} first 10 reachable")