import json, urllib.request, re

M3U_URL = "https://raw.githubusercontent.com/BurningC4/Chinese-IPTV/master/TV-IPV4.m3u"
print("Fetching...")
req = urllib.request.Request(M3U_URL, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=15)
content = resp.read().decode("utf-8", errors="replace")
print(f"Got {len(content)} chars")

channels = []
current = None
for line in content.split("\n"):
    line = line.strip()
    if line.startswith("#EXTINF:"):
        m = re.search(r'tvg-id="([^"]*)"', line)
        tvg_id = m.group(1) if m else ""
        m = re.search(r'tvg-logo="([^"]*)"', line)
        tvg_logo = m.group(1) if m else ""
        m = re.search(r",(.+)$", line)
        name = m.group(1).strip() if m else tvg_id
        current = {"name": name, "tvg_id": tvg_id, "logo": tvg_logo, "url": ""}
    elif line and not line.startswith("#") and current:
        current["url"] = line
        if current["url"]:
            channels.append(current)
        current = None

print(f"Parsed {len(channels)} channels")

def sort_key(c):
    n = c["name"]
    if "CCTV" in n:
        m = re.search(r"CCTV[- ]*(\d+)", n)
        if m:
            return (0, int(m.group(1)), n)
        return (0, 99, n)
    return (1, 0, n)

channels.sort(key=sort_key)

# Print first 10
for i, ch in enumerate(channels[:10]):
    print(f"  {i+1}. {ch['name']}")

output = {
    "name": "CCTV+省级卫视 (中国移动源)",
    "source": M3U_URL,
    "total": len(channels),
    "channels": channels
}

with open(r"C:\Users\Administrator\.openclaw\workspace\tvbox\sources\china.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(channels)} channels to china.json")