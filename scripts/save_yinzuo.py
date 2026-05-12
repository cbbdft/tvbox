import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'TVBox/1.0'}

# Download the full config
url = 'https://jihulab.com/Liangmyjj/tvboxx/-/raw/main/yinzuo2.json'
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
data = resp.read()
text = data.decode('utf-8', errors='replace')

# Save raw
with open(r'C:\Users\Administrator\.openclaw\workspace\tvbox\sources\yinzuo.json', 'w', encoding='utf-8') as f:
    f.write(text)
print('Saved yinzuo.json, size:', len(text))

j = json.loads(text)

# Check lives
print('\n=== Lives ===')
for live in j.get('lives', []):
    print('Name:', live.get('name'), 'Type:', live.get('type'))
    url_live = live.get('url', '')
    epg = live.get('epg', '')
    logo = live.get('logo', '')
    print('  URL:', url_live[:100] if url_live else 'None')
    print('  EPG:', epg[:100] if epg else 'None')
    print('  Logo:', logo[:100] if logo else 'None')
    print()

# Check sites count
print('=== Sites ===')
print('Total sites:', len(j.get('sites', [])))
for s in j.get('sites', []):
    print('  -', s.get('name'), '| key:', s.get('key'), '| type:', s.get('type'), '| api:', s.get('api', '')[:60])

print('\n=== Parses ===')
for p in j.get('parses', []):
    print('  -', p.get('name'), '| key:', p.get('key'))

print('\n=== Flags ===')
print(j.get('flags', []))