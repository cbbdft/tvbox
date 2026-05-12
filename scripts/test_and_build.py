# -*- coding: utf-8 -*-
"""
TVBox 直播源测试工具 v4
========================
测试步骤：
1. 从源目录读取所有已知的源文件（JSON格式）
2. 对每个源的抽样频道（每源前5个）发送HTTP HEAD请求
3. 统计每个源的可用率
4. 只保留可用率 >= 30% 的源
5. 生成最终可用源列表

使用方法：
    python test_and_build.py

输出：
    - sources/test_results.txt  (测试日志)
    - sources/working_sources.json  (可用源，仅可用源)
    - sources/all_sources_report.txt  (汇总报告)
"""
import os
import sys
import json
import time
import urllib.request
import ssl
import re

# ========== 配置 ==========
SOURCES_DIR = r"C:\Users\Administrator\.openclaw\workspace\tvbox\sources"
OUTPUT_WORKING = os.path.join(SOURCES_DIR, "working_sources.json")
OUTPUT_REPORT = os.path.join(SOURCES_DIR, "all_sources_report.txt")
OUTPUT_LOG = os.path.join(SOURCES_DIR, "test_log_v4.txt")
TIMEOUT = 5  # 短超时，避免挂起
SAMPLE_PER_SOURCE = 5  # 每源测试数量
MIN_SUCCESS_RATE = 0.3  # 最少30%可用率才保留
# =========================

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def log(msg, end='\n'):
    """同时打印和写文件"""
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, end=end)
    try:
        with open(OUTPUT_LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass


def safe_str(s):
    """安全字符串，用于打印"""
    if not s:
        return ""
    try:
        return str(s).encode('gbk', errors='replace').decode('gbk')
    except:
        return str(s)


def test_url(url, timeout=TIMEOUT):
    """测试单个URL，返回(bool, str)"""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return False, 'invalid_url'

    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        req.add_header('Referer', 'https://www.google.com/')

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = resp.status
            ct = resp.headers.get('Content-Type', '')
            cl = resp.headers.get('Content-Length', '0')

            # 成功判断：状态码200，且有content-length或者content-type包含video
            if status == 200:
                if 'video' in ct.lower() or 'application' in ct.lower() or int(cl) > 1000:
                    return True, f'OK-200-{ct[:20]}'
                else:
                    # 可能有效但类型不明确
                    return True, f'OK-200-{cl}bytes'
            return False, f'http_{status}'

    except urllib.error.HTTPError as e:
        return False, f'http_{e.code}'
    except urllib.error.URLError as e:
        return False, f'url_err'
    except TimeoutError:
        return False, 'timeout'
    except Exception as e:
        return False, f'err_{type(e).__name__[:10]}'


def load_sources():
    """加载sources目录下所有JSON文件"""
    sources = {}
    if not os.path.exists(SOURCES_DIR):
        return sources

    for fname in os.listdir(SOURCES_DIR):
        if not fname.endswith('.json'):
            continue
        if fname in ['working_sources.json', 'all_sources_report.txt']:
            continue
        fpath = os.path.join(SOURCES_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 兼容两种格式：{name, channels[]} 或 {source_key: {name, source, channels[]}}
            if 'channels' in data:
                # 顶级格式
                name = data.get('name', fname.replace('.json', ''))
                channels = data.get('channels', [])
                sources[fname] = {'name': name, 'channels': channels, 'file': fname}
            else:
                # 嵌套格式
                for key, val in data.items():
                    if isinstance(val, dict) and 'channels' in val:
                        sources[f"{fname}_{key}"] = {
                            'name': val.get('name', key),
                            'source': val.get('source', ''),
                            'channels': val.get('channels', []),
                            'file': fname
                        }
        except Exception as e:
            log(f"加载 {fname} 失败: {e}")

    return sources


def main():
    # 清理旧日志
    with open(OUTPUT_LOG, 'w', encoding='utf-8') as f:
        f.write(f"TVBox直播源测试 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n")

    log(f"开始测试直播源...")
    log(f"源目录: {SOURCES_DIR}")
    log(f"每源测试: {SAMPLE_PER_SOURCE} 个频道")
    log(f"超时设置: {TIMEOUT} 秒")
    log(f"最低可用率: {MIN_SUCCESS_RATE*100:.0f}%")
    log("")

    sources = load_sources()
    log(f"找到 {len(sources)} 个源")

    if not sources:
        log("没有找到任何源文件！")
        return

    results = {}

    for key, src in sources.items():
        name = src.get('name', key)
        channels = src.get('channels', [])
        source_url = src.get('source', '')

        log(f"\n{'='*50}")
        log(f"源: {name}")
        if source_url:
            log(f"地址: {source_url}")
        log(f"频道总数: {len(channels)}")

        if not channels:
            log("  无频道，跳过")
            results[key] = {'name': name, 'source': source_url, 'total': 0, 'tested': 0, 'working': 0, 'rate': 0, 'status': 'NO_CHANNELS', 'channels': []}
            continue

        # 抽样测试
        sample = channels[:SAMPLE_PER_SOURCE]
        working_channels = []

        for i, ch in enumerate(sample, 1):
            ch_name = ch.get('name', 'unknown')[:30]
            ch_url = ch.get('url', '')
            log(f"  [{i}/{len(sample)}] {safe_str(ch_name)}", end='')

            if not ch_url:
                log(f" -> 跳过（无URL）")
                continue

            is_ok, msg = test_url(ch_url)
            status_icon = "OK" if is_ok else "FAIL"
            log(f" -> {status_icon} ({msg})")

            if is_ok:
                working_channels.append(ch)

            # 短暂休息，避免请求过快
            time.sleep(0.2)

        rate = len(working_channels) / len(sample) if sample else 0
        log(f"  结果: {len(working_channels)}/{len(sample)} 可用 ({rate*100:.0f}%)")

        # 判断是否保留
        if rate >= MIN_SUCCESS_RATE and working_channels:
            status = 'OK'
            log(f"  -> 保留 (可用率 {rate*100:.0f}% >= {MIN_SUCCESS_RATE*100:.0f}%)")
        else:
            status = 'LOW_RATE'
            log(f"  -> 丢弃 (可用率 {rate*100:.0f}% < {MIN_SUCCESS_RATE*100:.0f}%)")

        results[key] = {
            'name': name,
            'source': source_url,
            'file': src.get('file', ''),
            'total': len(channels),
            'tested': len(sample),
            'working': len(working_channels),
            'rate': rate,
            'status': status,
            'channels': channels,  # 全量频道
            'working_channels': working_channels  # 可用频道
        }

    # ========== 汇总报告 ==========
    log(f"\n{'='*60}")
    log(f"[最终汇总]")

    kept = {k: v for k, v in results.items() if v['status'] == 'OK'}
    discarded = {k: v for k, v in results.items() if v['status'] != 'OK'}

    log(f"保留源: {len(kept)}/{len(results)}")
    log(f"丢弃源: {len(discarded)}/{len(results)}")

    for k, v in sorted(kept.items(), key=lambda x: x[1]['rate'], reverse=True):
        log(f"  [保留] {v['name']}: {v['working']}/{v['tested']} ({v['rate']*100:.0f}%)")

    if discarded:
        log(f"\n丢弃的源:")
        for k, v in sorted(discarded.items(), key=lambda x: x[1]['rate'], reverse=True):
            log(f"  [丢弃] {v['name']}: {v['working']}/{v['tested']} ({v['rate']*100:.0f}%) - {v['status']}")

    # ========== 生成可用源文件 ==========
    if kept:
        log(f"\n{'='*60}")
        log(f"[生成可用源文件]")

        # 汇总所有可用频道
        all_working = []
        for k, v in kept.items():
            # 为每个源生成独立文件
            src_data = {
                'name': v['name'],
                'source': v['source'],
                'total': v['total'],
                'tested_sample': v['tested'],
                'working_in_sample': v['working'],
                'sample_success_rate': v['rate'],
                'channels': v['channels']  # 全量保留
            }

            safe_name = v['name'].replace('/', '_').replace('\\', '_').replace(' ', '_')
            out_file = os.path.join(SOURCES_DIR, f"{safe_name}.json")

            try:
                with open(out_file, 'w', encoding='utf-8') as f:
                    json.dump(src_data, f, ensure_ascii=False, indent=2)
                log(f"  保存: {safe_name}.json")
            except Exception as e:
                log(f"  保存失败 {safe_name}.json: {e}")

            # 也加入总表
            all_working.append({
                'name': v['name'],
                'source': v['source'],
                'total': v['total'],
                'rate': v['rate']
            })

        # 保存总表
        with open(OUTPUT_WORKING, 'w', encoding='utf-8') as f:
            json.dump({'sources': all_working, 'count': len(all_working)}, f, ensure_ascii=False, indent=2)
        log(f"  总表: working_sources.json ({len(all_working)} 个可用源)")
    else:
        log(f"\n没有可用源！请检查网络或更新源列表。")
        # 仍然生成空文件
        with open(OUTPUT_WORKING, 'w', encoding='utf-8') as f:
            json.dump({'sources': [], 'count': 0, 'error': 'no_working_sources'}, f, ensure_ascii=False)

    # 生成文本报告
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(f"TVBox 直播源测试报告\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"汇总:\n")
        f.write(f"  测试源总数: {len(results)}\n")
        f.write(f"  可用源数量: {len(kept)}\n")
        f.write(f"  丢弃源数量: {len(discarded)}\n\n")
        f.write(f"可用源列表:\n")
        for k, v in sorted(kept.items(), key=lambda x: x[1]['rate'], reverse=True):
            f.write(f"  - {v['name']} ({v['working']}/{v['tested']} tested, {v['rate']*100:.0f}% success)\n")
            f.write(f"    Total channels: {v['total']}\n")
            if v['source']:
                f.write(f"    Source: {v['source']}\n")
            f.write(f"\n")

        if discarded:
            f.write(f"\n丢弃源列表:\n")
            for k, v in sorted(discarded.items(), key=lambda x: x[1]['rate'], reverse=True):
                f.write(f"  - {v['name']} ({v['working']}/{v['tested']} tested, {v['rate']*100:.0f}%, reason: {v['status']})\n")

    log(f"\n报告已保存: {OUTPUT_REPORT}")
    log(f"可用源: {OUTPUT_WORKING}")
    log(f"\n测试完成！")


if __name__ == '__main__':
    main()