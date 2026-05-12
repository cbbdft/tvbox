import urllib.request, ssl, json, sys

OUT = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/verified.json'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def enc(s):
    """Encode string to gbk-safe, replace non-encodable chars"""
    try:
        return s.encode('gbk', errors='replace').decode('gbk')
    except:
        return s

def test(url):
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6, context=ctx) as r:
            return r.status == 200
    except: return False

with open(OUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = {}
for key, src in data.items():
    name_safe = enc(src['name'])
    print(f'\n=== {name_safe} ({src["count"]} ch) ===')
    chs = src['channels'][:8]
    working = []
    for i, ch in enumerate(chs):
        n = ch['name'][:28] if len(ch['name']) > 28 else ch['name']
        n_safe = enc(n)
        ok = test(ch['url'])
        status = 'OK' if ok else 'FAIL'
        print(f'  [{i+1}] {n_safe}: {status}')
        if ok:
            working.append(ch)

    ratio = len(working) / len(chs) if chs else 0
    print(f'  -> {len(working)}/{len(chs)} working ({ratio*100:.0f}%)')
    results[key] = {'name': src['name'], 'source': src['source'], 'working': len(working), 'total': len(chs), 'ratio': ratio, 'sample_channels': working}

print('\n=== SUMMARY ===')
for key, r in results.items():
    n = enc(r['name'])
    print(f'{n}: {r["working"]}/{r["total"]} ({r["ratio"]*100:.0f}%)')

out2 = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/working.json'
with open(out2, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nSaved to {out2}')
print('DONE')