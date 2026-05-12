import urllib.request, ssl, json, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return r.read().decode('utf-8', errors='ignore')

def parse_m3u(content):
    chs = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#EXTINF:'):
            m = re.search(r',(.+)$', line)
            n = m.group(1).strip() if m else ''
            lm = re.search(r'tvg-logo="([^"]+)"', line)
            lg = lm.group(1) if lm else ''
            nl = lines[i+1].strip() if i+1 < len(lines) else ''
            if nl.startswith('http'):
                chs.append({'name': n, 'url': nl, 'logo': lg})
    return chs

# Fetch YanG_Gather
print('Fetching YanG_Gather...')
c1 = fetch('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u')
chs1 = parse_m3u(c1)
print(f'  {len(c1)} bytes -> {len(chs1)} channels')

# Fetch gnodgl_CCTV
print('Fetching gnodgl_CCTV...')
c2 = fetch('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u')
chs2 = parse_m3u(c2)
print(f'  {len(c2)} bytes -> {len(chs2)} channels')

# Fetch cuikaipeng_CCTV
print('Fetching cuikaipeng_CCTV...')
c3 = fetch('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u')
chs3 = parse_m3u(c3)
print(f'  {len(c3)} bytes -> {len(chs3)} channels')

# Fetch cuikaipeng_IPTV
print('Fetching cuikaipeng_IPTV...')
c4 = fetch('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u')
chs4 = parse_m3u(c4)
print(f'  {len(c4)} bytes -> {len(chs4)} channels')

# Save all
data = {
    'YanG_Gather': {'name': 'YanG聚合', 'source': 'https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u', 'count': len(chs1), 'channels': chs1},
    'gnodgl_CCTV': {'name': 'CCTV专版', 'source': 'https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u', 'count': len(chs2), 'channels': chs2},
    'cuikaipeng_CCTV': {'name': '崔凯CCTV', 'source': 'https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u', 'count': len(chs3), 'channels': chs3},
    'cuikaipeng_IPTV': {'name': '崔凯IPTV', 'source': 'https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u', 'count': len(chs4), 'channels': chs4},
}

out = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/verified.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Saved to {out}')
print('DONE')