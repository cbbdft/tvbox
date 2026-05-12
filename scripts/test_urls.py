import urllib.request
import json

urls = [
    ('cdn.qiaoji8', 'http://cdn.qiaoji8.com/tvbox.json'),
    ('mitvbox', 'http://mitvbox.xyz/%E5%B0%8F%E7%B1%B3/DEMO.json'),
    ('ok213', 'http://ok213.top/tv'),
]

for name, url in urls:
    print('=== ' + name + ': ' + url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read()
        print('Status: ' + str(resp.status) + ', Size: ' + str(len(data)))
        
        try:
            j = json.loads(data.decode('utf-8', errors='replace'))
            print('JSON! Type: ' + type(j).__name__)
            if isinstance(j, dict):
                print('Keys: ' + str(list(j.keys())))
                spider = j.get('spider', '')
                if spider:
                    print('spider: ' + str(spider)[:200])
                sites = j.get('sites', [])
                if sites:
                    print('sites count: ' + str(len(sites)))
                    if isinstance(sites, list) and sites:
                        print('First site: ' + json.dumps(sites[0], ensure_ascii=False)[:300])
                urls_list = j.get('urls', [])
                if urls_list:
                    print('urls count: ' + str(len(urls_list)))
            elif isinstance(j, list):
                print('List length: ' + str(len(j)))
                if j:
                    print('First item: ' + str(j[0])[:300])
        except Exception as e:
            text = data.decode('utf-8', errors='replace')
            print('Not JSON: ' + text[:300])
        print()
    except Exception as e:
        print('ERROR: ' + str(e))
        print()
