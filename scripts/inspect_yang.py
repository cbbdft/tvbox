import json

with open(r'C:\Users\Administrator\.openclaw\workspace\tvbox\sources\YanG聚合.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

channels = data['channels']
print(f'Total channels: {len(channels)}')

# Filter out maintenance/announcement channels
real_chs = [c for c in channels 
            if '维护' not in c['name'] and '公告' not in c['name'] 
            and '订阅' not in c['name'] and '说明' not in c['name']]

print(f'Real channels (filtered): {len(real_chs)}')
print('\nFirst 15 real channels:')
for i, c in enumerate(real_chs[:15]):
    print(f'  {i+1}. {c["name"]}')

print('\nChannel types breakdown:')
groups = {}
for c in channels:
    name = c['name']
    if 'CCTV' in name or '央視' in name or '央视' in name:
        grp = 'CCTV'
    elif '卫视' in name or '地方' in name or '省' in name:
        grp = 'Local'
    elif '移动' in name or '咪咕' in name:
        grp = 'Migu'
    elif '体育' in name or '足球' in name or '篮球' in name:
        grp = 'Sports'
    elif '维护' in name or '公告' in name or '订阅' in name or '说明' in name:
        grp = 'Meta'
    else:
        grp = 'Other'
    groups[grp] = groups.get(grp, 0) + 1

for grp, cnt in sorted(groups.items(), key=lambda x: -x[1]):
    print(f'  {grp}: {cnt}')