# TVBox 直播源管理与加速配置中心
# TVBox Live TV Source Management & Acceleration Hub

## 项目简介

基于开源 TVBox 方案，为 Android 4.4 电视盒子构建的直播源管理与加速配置中心。

**核心原则：只保留经过实际测试验证可用的源，不知道能不能用的坚决不添加！**

---

## 可用源（经过 HTTP HEAD 测试验证）

| 源名称 | 频道数 | 测试可用率 | 说明 |
|--------|--------|------------|------|
| **YanG聚合** | 129 | 100% (5/5) | 主要来源，包含央视、咪咕、移动等频道 |
| **trial** | 24 | 60% (3/5) | 国际频道为主（CNA、TRT等） |

**说明：**
- 测试方法：对每个源的抽样频道发送 HTTP HEAD 请求
- 阈值：可用率 >= 30% 才保留
- 测试日志：`sources/test_log_v4.txt`
- 测试报告：`sources/all_sources_report.txt`

---

## 源文件说明

```
sources/
  YanG聚合.json    # 经过验证的可用源（129频道，100%可用）
  trial.json       # 经过验证的可用源（24频道，60%可用）
  working_sources.json  # 可用源总表
  all_sources_report.txt # 完整测试报告
  test_log_v4.txt   # 测试过程日志
```

---

## 添加新源的流程

1. **获取源**：从可信的 GitHub 仓库（如 YanG-1989/m3u、gnodgl/IPTV 等）获取 m3u/txt 源
2. **解析**：运行 `scripts/fetch_sources.py` 解析源并保存到 `sources/` 目录
3. **测试**：运行 `scripts/test_and_build.py` 对新源进行 HTTP HEAD 测试
4. **评估**：检查 `working_sources.json`，只保留可用率 >= 30% 的源
5. **确认**：可用源自动保存为独立 JSON 文件

---

## 工具脚本

| 脚本 | 功能 |
|------|------|
| `scripts/fetch_sources.py` | 从 GitHub 获取 m3u/txt 源并解析为 JSON |
| `scripts/test_and_build.py` | 测试所有源，过滤可用率 >= 30% 的源，生成可用源列表 |
| `scripts/inspect_yang.py` | 检查 YanG 源的频道构成 |

---

## 配置文件格式

TVBox 配置文件（`tvbox-config.json`）：
```json
{
  "name": "TVBox 直播源管理",
  "version": "1.0.0",
  "sources": [
    {
      "name": "YanG聚合",
      "url": "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
      "type": "m3u"
    }
  ]
}
```

---

## 频道分类

YanG聚合源包含以下类型频道：
- **央视**：CCTV-1 至 CCTV-17（含4K频道）
- **咪咕**：移动咪咕直播（4K/高清）
- **省级卫视**：各省卫视地方台
- **晴彩频道**：移动特色频道（广场舞、少年、竞技等）

---

## 相关资源

- TVBox 官方：[https://github.com/o0Half0o/TVBox](https://github.com/o0Half0o/TVBox)
- YanG 聚合源：[https://github.com/YanG-1989/m3u](https://github.com/YanG-1989/m3u)

---

*最后更新：2026-05-12*