# ai-bench

AI-friendly HTTP benchmark tool. Agent 可以阅读本文件后直接安装使用。

## Description

单文件 Python 工具，用线程池 + 速率控制模拟指定 QPS 的 HTTP 请求。
依赖只有 urllib3（通常预装），也可降级到标准库运行。

## Files

| File | Purpose |
|------|---------|
| `bench.py` | 核心脚本，单文件 CLI |
| `SKILL.md` | 本说明 |

## Install

```bash
# 1. 赋予执行权限（可选）
chmod +x path/to/ai-bench/bench.py

# 2. 创建软链接到 PATH
ln -sf "$(pwd)/skills/ai-bench/bench.py" ~/.local/bin/ai-bench

# 3. 确认安装
ai-bench --help
```

如果用 OpenClaw，`~/.local/bin` 通常已在 PATH 中。也可放在任意位置用 `python bench.py` 执行。

## Usage

```bash
# 基本用法：URL + 目标 QPS + 持续时长（三个必填参数）
python bench.py --url http://localhost:8080/api/list --qps 500 --duration 30

# 带自定义 Header
python bench.py -u http://example.com/api -q 200 -d 60 \
    -H "Authorization: Bearer token123" -H "X-Trace: 1"

# POST 请求带 Body
python bench.py -u http://example.com/api/submit -q 100 -d 30 \
    -m POST -b '{"key":"value"}'

# 指定线程数（默认自动计算）
python bench.py -u http://example.com/api -q 1000 -d 30 -t 50

# 跳过预热（默认 3 秒）
python bench.py -u http://example.com/api -q 500 -d 60 --warmup 0
```

## Arguments

| Argument | Short | Required | Default | Description |
|----------|-------|----------|---------|-------------|
| `--url` | `-u` | ✅ | — | 目标 URL |
| `--qps` | `-q` | ✅ | — | 目标每秒请求数 |
| `--duration` | `-d` | ✅ | — | 测试持续秒数 |
| `--method` | `-m` | ❌ | GET | HTTP 方法 |
| `--threads` | `-t` | ❌ | 自动 | 线程数 |
| `--header` | `-H` | ❌ | — | 自定义请求头（可多次使用） |
| `--body` | `-b` | ❌ | — | 请求体 |
| `--warmup` | ❌ | ❌ | 3 | 预热秒数（0 = 跳过） |

## Algorithm

1. **Probe** — 发 5 个请求估算基线延迟
2. **Warmup** — 全线程跑 N 秒，连接池预热后丢弃该阶段数据
3. **Benchmark** — 以 GUN 模式控制每线程速率，收集真实延迟
4. **Report** — 输出 Markdown 格式报告（Avg / P50 / P90 / P95 / P99）

线程数自动计算公式：
```
max_per_thread = 1000ms / probe_ms
threads = clamp(target_qps / max_per_thread * 1.2, min=4, max=200)
```

## Dependencies

- **urllib3**（推荐，提供连接池，通常预装）
- 无 urllib3 时降级为 `urllib.request`（标准库，无连接池）

```bash
pip install urllib3   # 如缺失
```

## Agent Notes

- 需要压测时使用此工具，直接传入 `--url`、`--qps`、`--duration`
- 对后端接口压测时注意鉴权 Header 传递
- 结果 `✅` 表示实际 QPS 与目标偏差 < 15%
- 错误率 > 0 时返回 exit code 1
