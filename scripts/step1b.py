import urllib.request, ssl, json, re, time

TIMEOUT = 12
LOG = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/step1_log.txt'
OUT = 'C:/Users/Administrator/.openclaw/workspace/tvbox/sources/fetched.json'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.read().decode('utf-8', errors='ignore')
    except: return None

def pm3u(c):
    chs = []
    for i,l in enumerate(c.split('\n')):
        l = l.strip()
        if l.startswith('#EXTINF:'):
            m = re.search(r',(.+)$', l)
            n = m.group(1).strip() if m else ''
            lm = re.search(r'tvg-logo="([^"]+)"', l)
            lg = lm.group(1) if lm else ''
            lines = c.split('\n')
            nl = lines[i+1].strip() if i+1 < len(lines) else ''
            if nl.startswith('http'): chs.append({'name':n,'url':nl,'logo':lg})
    return chs

def ptxt(c):
    chs = []
    for l in c.split('\n'):
        l = l.strip()
        if not l or l.startswith('#'): continue
        p = l.rsplit(',', 1)
        if len(p)==2 and p[1].strip().startswith('http'): chs.append({'name':p[0].strip(),'url':p[1].strip(),'logo':''})
    return chs

def pjson(c):
    try: d = json.loads(c)
    except: return []
    chs = []
    if isinstance(d, list):
        for i in d:
            if isinstance(i,dict):
                n = i.get('name') or i.get('title') or ''
                u = i.get('url') or i.get('link') or ''
                if u and u.startswith('http'): chs.append({'name':str(n),'url':u,'logo':str(i.get('logo',''))})
        return chs
    if isinstance(d,dict):
        for k in ['channels','data','list']:
            if k in d and isinstance(d[k],list):
                for i in d[k]:
                    if isinstance(i,dict):
                        n = i.get('name') or i.get('title') or ''
                        u = i.get('url') or i.get('link') or ''
                        if u and u.startswith('http'): chs.append({'name':str(n),'url':u,'logo':str(i.get('logo',''))})
                if chs: return chs
    return chs

srcs = [
    ('https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u','YanG_Gather'),
    ('https://raw.githubusercontent.com/gnodgl/IPTV/master/CCTV.m3u','gnodgl_CCTV'),
    ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/CCTV.m3u','cuikaipeng_CCTV'),
    ('https://raw.githubusercontent.com/cuikaipeng/IPTV/main/IPTV.m3u','cuikaipeng_IPTV'),
    ('https://raw.githubusercontent.com/MercuryZz/IPTVN/refs/heads/Files/IPTV.m3u','IPTVN'),
    ('https://raw.githubusercontent.com/trial/m3u/main/tv.m3u','trial'),
    ('https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u','Kimentanm'),
    ('https://raw.githubusercontent.com/zbefine/iptv/main/iptv.m3u','zbefine'),
    ('https://raw.githubusercontent.com/lalifeier/IPTV/main/txt/IPTV.txt','lalifeier'),
    ('https://raw.githubusercontent.com/dxawi/0/main/0.json','dxawi'),
    ('https://raw.githubusercontent.com/UndCover/PyramidStore/main/py.json','PyramidStore'),
]

with open(LOG,'w',encoding='utf-8') as f: f.write('')

results = {}
for url, name in srcs:
    ts = time.strftime('%H:%M:%S')
    msg = f'[{ts}] Fetching {name}...'
    print(msg)
    with open(LOG,'a',encoding='utf-8') as f: f.write(msg+'\n')
    c = fetch(url)
    if not c:
        results[name] = {'url':url,'status':'FAIL','count':0,'channels':[]}
        continue
    chs = pm3u(c) if '.m3u' in url or '#EXTM3U' in c else (ptxt(c) if url.endswith('.txt') else pjson(c))
    results[name] = {'url':url,'status':'OK','count':len(chs),'channels':chs}
    msg = f'[{ts}]   -> {len(chs)} channels'
    print(msg)
    with open(LOG,'a',encoding='utf-8') as f: f.write(msg+'\n')
    time.sleep(0.3)

with open(OUT,'w',encoding='utf-8') as f:
    json.dump(results,f,ensure_ascii=False,indent=2)
msg = f'Done. Saved to {OUT}'
print(msg)
with open(LOG,'a',encoding='utf-8') as f: f.write(msg+'\n')