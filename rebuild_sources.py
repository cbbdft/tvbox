#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 直播源重建工具
- 从 live.zbds.top 抓取原始 M3U 数据
- 过滤纯音频流 (/audio/ 路径)
- 替换为完整视频流 URL
- 输出正确格式的 M3U 文件
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# 数据源 URL
IPTV4_M3U = "https://live.zbds.top/tv/iptv4.m3u"
IPTV4_TXT = "https://live.zbds.top/tv/iptv4.txt"

# 已知的 CCTV 视频流 URL 映射 (从 iptv4.txt 等源获取)
# 格式: {频道名: [视频流URL列表]}
VIDEO_STREAMS = {
    # CCTV 视频流
    "CCTV1": [
        "http://124.116.183.146:9901/tsfile/live/0001_1.m3u8",
        "http://182.150.23.74:808/hls/1/index.m3u8",
        "http://183.11.239.36:808/hls/19/index.m3u8",
        "http://112.46.85.60:8009/hls/501/index.m3u8",
    ],
    "CCTV2": [
        "http://222.169.85.8:9901/tsfile/live/0002_1.m3u8",
        "http://182.150.23.74:808/hls/2/index.m3u8",
        "http://112.46.85.60:8009/hls/502/index.m3u8",
        "http://123.129.70.178:9901/tsfile/live/0002_1.m3u8",
    ],
    "CCTV3": [
        "http://124.116.183.146:9901/tsfile/live/0003_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0003_1.m3u8",
        "http://183.11.239.36:808/hls/91/index.m3u8",
        "http://123.129.70.178:9901/tsfile/live/0003_1.m3u8",
    ],
    "CCTV4": [
        "http://182.150.23.74:808/hls/4/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0004_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0004_1.m3u8",
        "http://112.46.85.60:8009/hls/504/index.m3u8",
    ],
    "CCTV5": [
        "http://182.150.23.74:808/hls/5/index.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0005_1.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0005_1.m3u8",
        "http://123.129.70.178:9901/tsfile/live/0005_1.m3u8",
    ],
    "CCTV5+": [
        "http://cssbyd.imwork.net:8082/hls/6/index.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0116_1.m3u8",
        "http://123.129.70.178:9901/tsfile/live/0016_1.m3u8",
    ],
    "CCTV6": [
        "http://182.150.23.74:808/hls/7/index.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0006_1.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0006_1.m3u8",
    ],
    "CCTV7": [
        "http://182.150.23.74:808/hls/7/index.m3u8",
        "http://182.150.23.74:808/hls/8/index.m3u8",
        "http://182.150.23.74:808/hls/18/index.m3u8",
    ],
    "CCTV8": [
        "http://182.150.23.74:808/hls/8/index.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0008_1.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0008_1.m3u8",
    ],
    "CCTV9": [
        "http://182.150.23.74:808/hls/9/index.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0009_1.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0009_1.m3u8",
    ],
    "CCTV10": [
        "http://182.150.23.74:808/hls/10/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0010_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0010_1.m3u8",
        "http://112.46.85.60:8009/hls/510/index.m3u8",
    ],
    "CCTV11": [
        "http://182.150.23.74:808/hls/11/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0011_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0011_1.m3u8",
        "http://112.46.85.60:8009/hls/511/index.m3u8",
    ],
    "CCTV12": [
        "http://182.150.23.74:808/hls/12/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0012_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0012_1.m3u8",
        "http://112.46.85.60:8009/hls/512/index.m3u8",
    ],
    "CCTV13": [
        "http://ali-m-l.cztv.com/channels/lantian/channel21/1080p.m3u8",
        "http://182.150.23.74:808/hls/13/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0013_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0013_1.m3u8",
    ],
    "CCTV14": [
        "http://182.150.23.74:808/hls/14/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0014_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0014_1.m3u8",
        "http://112.46.85.60:8009/hls/514/index.m3u8",
    ],
    "CCTV15": [
        "http://182.150.23.74:808/hls/15/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0015_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0015_1.m3u8",
        "http://112.46.85.60:8009/hls/515/index.m3u8",
    ],
    "CCTV16": [
        "http://gmxw.7766.org:808/hls/169/index.m3u8",
        "http://182.150.23.74:808/hls/16/index.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0016_1.m3u8",
    ],
    "CCTV17": [
        "http://182.150.23.74:808/hls/17/index.m3u8",
        "http://123.130.84.106:8154/tsfile/live/0019_1.m3u8",
        "http://124.116.183.146:9901/tsfile/live/0017_1.m3u8",
        "http://222.169.85.8:9901/tsfile/live/0017_1.m3u8",
    ],
}


def fetch_iptv4_m3u():
    """从 live.zbds.top 抓取 M3U 数据"""
    print("[FETCH] 正在从 live.zbds.top 获取 M3U 数据...")
    try:
        resp = requests.get(IPTV4_M3U, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()
        print(f"[FETCH] 获取成功，共 {len(resp.text)} 字节")
        return resp.text
    except Exception as e:
        print(f"[FETCH] 错误: {e}")
        return None


def parse_m3u_content(content):
    """解析 M3U 内容，返回频道列表"""
    channels = []
    lines = content.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF'):
            # 提取频道名称 (逗号后面的部分)
            match = re.search(r',(.+)$', line)
            if not match:
                i += 1
                continue
            
            name = match.group(1).strip()
            
            # 提取分组
            group = ""
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                group = group_match.group(1)
            
            # 提取 logo
            logo = ""
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            if logo_match:
                logo = logo_match.group(1)
            
            # 下一个非空行就是 URL
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            if i < len(lines):
                url = lines[i].strip()
                channels.append({
                    'name': name,
                    'group': group,
                    'logo': logo,
                    'url': url,
                    'original_line': line,
                })
        
        i += 1
    
    return channels


def is_audio_stream(url):
    """判断是否是纯音频流"""
    return '/audio/' in url.lower()


def is_valid_video_stream(url):
    """判断是否是有效的视频流 URL"""
    # 排除音频流、百度云 mp4 等
    if is_audio_stream(url):
        return False
    if url.endswith('.mp4'):
        return False
    # 必须是 http/https 开头的 m3u8 或 playlist
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    return True


def replace_audio_with_video(channels):
    """将音频流频道替换为视频流"""
    replaced = 0
    skipped = 0
    
    for ch in channels:
        url = ch['url']
        name = ch['name']
        
        if not is_valid_video_stream(url):
            if is_audio_stream(url):
                # 查找视频流映射
                video_key = None
                # 按长度降序匹配，避免 "CCTV1" 匹配到 "CCTV10"
                for key in sorted(VIDEO_STREAMS.keys(), key=len, reverse=True):
                    if key in name:
                        video_key = key
                        break
                
                if video_key and VIDEO_STREAMS[video_key]:
                    # 用视频流替换音频流
                    ch['url'] = VIDEO_STREAMS[video_key][0]
                    ch['replaced'] = True
                    ch['old_url'] = url
                    replaced += 1
                    print(f"  [替换] {name}: {url[:60]}... -> {ch['url'][:60]}...")
                else:
                    skipped += 1
                    print(f"  [跳过] {name}: 无对应视频流映射")
            else:
                print(f"  [保留] {name}: {url[:60]}... (非音频流)")
    
    print(f"\n[统计] 替换了 {replaced} 个音频流，跳过了 {skipped} 个无映射频道")
    return channels


def write_m3u_file(channels, output_path):
    """写入标准 M3U 格式文件"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 文件头（只写一次）
        f.write('#EXTM3U x-tvg-url="http://epg.51zmt.top:8000/e.xml"\n')
        f.write(f'# 更新时间: {now}\n')
        f.write(f'# 频道总数: {len(channels)}\n')
        f.write('#\n\n')
        
        current_group = ""
        for ch in channels:
            group = ch.get('group', '其他')
            
            # 分组标题
            if group != current_group:
                f.write(f'#group-title="{group}"\n')
                current_group = group
            
            # EXTINF 行
            logo = ch.get('logo', '')
            name = ch['name']
            
            if logo:
                f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
            else:
                f.write(f'#EXTINF:-1 group-title="{group}", {name}\n')
            
            # URL 行
            f.write(f'{ch["url"]}\n')
            
            # 频道之间加空行
            f.write('\n')
    
    print(f"[WRITE] 已写入 {len(channels)} 个频道到: {output_path}")


def test_urls_sample(channels, sample_size=5):
    """抽样测试 URL 可用性"""
    import subprocess
    
    sample = channels[:sample_size]
    print(f"\n[SAMPLE TEST] 抽样测试前 {sample_size} 个频道:")
    
    for ch in sample:
        url = ch['url']
        name = ch['name']
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                 '--connect-timeout', '5', '--max-time', '10', url],
                capture_output=True, text=True, timeout=15
            )
            status = result.stdout.strip()
            icon = "✅" if status == "200" else "❌"
            print(f"  {icon} {name}: {status}")
        except Exception as e:
            print(f"  ❌ {name}: 测试失败 ({e})")


def main():
    print("=" * 60)
    print("  TVBox 直播源重建工具")
    print("=" * 60)
    print()
    
    # 1. 抓取原始数据
    content = fetch_iptv4_m3u()
    if not content:
        print("\n错误: 无法获取数据")
        sys.exit(1)
    
    # 2. 解析 M3U
    print("\n[PARSE] 解析 M3U 数据...")
    channels = parse_m3u_content(content)
    print(f"[PARSE] 找到 {len(channels)} 个频道")
    
    # 统计音频流数量
    audio_count = sum(1 for ch in channels if is_audio_stream(ch['url']))
    video_count = sum(1 for ch in channels if is_valid_video_stream(ch['url']) and not is_audio_stream(ch['url']))
    print(f"        其中音频流: {audio_count}, 视频流: {video_count}")
    
    # 3. 替换音频流
    print("\n[REPLACE] 替换音频流为视频流...")
    channels = replace_audio_with_video(channels)
    
    # 4. 抽样测试
    test_urls_sample(channels, sample_size=5)
    
    # 5. 写入文件
    output_dir = Path(__file__).parent / "sources"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "zbds_cctv_satellite_v2.m3u"
    write_m3u_file(channels, str(output_path))
    
    print("\n" + "=" * 60)
    print("  重建完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
