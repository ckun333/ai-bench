# ai-bench

AI-friendly HTTP benchmark tool for OpenClaw agents.

## For Agents

Paste this into your session to install ai-bench:

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
# 验证
ai-bench --help
```

Or use the full installer:

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/install.sh | bash
```

## Description

单文件 Python 压测工具。给它 URL + 目标 QPS + 时长，直接出报告。
依赖只有 urllib3（通常预装），无 urllib3 时自动降级为标准库。

```bash
ai-bench --url http://host/api --qps 500 --duration 60
```

## Usage

```bash
# ── 基础 ──────────────────────────────────────────────
ai-bench -u http://host/api/list -q 500 -d 30

# ── POST + JSON ──────────────────────────────────────
ai-bench -u http://host/api/login -q 200 -d 60 \
    -m POST --json '{"user":"admin","pass":"123"}'

# ── POST + Form-urlencoded ────────────────────────────
ai-bench -u http://host/api/login -q 200 -d 60 \
    -m POST --form "user=admin" --form "pass=123"

# ── POST + Multipart form-data ────────────────────────
ai-bench -u http://host/api/upload -q 50 -d 30 \
    -m POST --form-data "file=@photo.jpg" --form-data "type=avatar"

# ── PUT / DELETE ─────────────────────────────────────
ai-bench -u http://host/api/item/1 -q 100 -d 30 -m PUT --json '{"name":"new"}'
ai-bench -u http://host/api/item/1 -q 100 -d 30 -m DELETE

# ── 自定义 Header ─────────────────────────────────────
ai-bench -u http://host/api -q 500 -d 30 \
    -H "Authorization: Bearer tok_xxx" -H "X-Trace: 1"
```

## Arguments

| Arg | Short | Req | Default | Description |
|-----|-------|-----|---------|-------------|
| `--url` | `-u` | ✅ | — | Target URL |
| `--qps` | `-q` | ✅ | — | Target QPS |
| `--duration` | `-d` | ✅ | — | Duration (seconds) |
| `--method` | `-m` | ❌ | GET | HTTP method (GET/POST/PUT/DELETE/PATCH…) |
| `--threads` | `-t` | ❌ | auto | Thread count |
| `--header` | `-H` | ❌ | — | Header (repeatable) |
| `--body` | `-b` | ❌ | — | Raw request body |
| `--json` | ❌ | ❌ | — | JSON body (auto Content-Type) |
| `--form` | ❌ | ❌ | — | Form field key=val (repeatable) |
| `--form-data` | ❌ | ❌ | — | Multipart field key=val (repeatable) |
| `--warmup` | ❌ | ❌ | 3 | Warmup seconds (0=skip) |

`--body` / `--json` / `--form` / `--form-data` 互斥，不能同时使用。

## Output

### 结果
| 目标 QPS | 实际 QPS | 状态 | 耗时 | 请求总数 | 错误数 | 错误率 |
|---------|---------|------|------|---------|-------|-------|
| 500 | 497.7 | ✅ | 60.0s | 29879 | 0 | 0.0% |

### 延迟 (ms)
| 平均 | 中位数 | P90 | P95 | P99 | 最小 | 最大 |
|------|--------|-----|-----|-----|------|------|
| 12.6 | 8.7 | 21.9 | 26.2 | 55.2 | 4.9 | 397.6 |

### 分析
自动附带性能分析文本，AI 可直接解读。

## Algorithm

1. **Probe** — 发 5 个请求估算基线延迟
2. **Warmup** — 全线程跑 N 秒预热连接池
3. **Benchmark** — GUN 模式速率控制
4. **Report** — Markdown 报告 + 分析

线程数自动计算：
```
max_per_thread = 1000ms / probe_ms
threads = clamp(target_qps / max_per_thread * 1.2, min=4, max=200)
```

## Dependencies

- urllib3（推荐，通常已预装）
- 无 urllib3 时降级为 urllib.request（标准库，无连接池）
- form-data 需要 urllib3

```bash
pip install urllib3
```

## Agent Notes

- 需要压测时直接调用 `ai-bench -u <url> -q <qps> -d <sec>`
- 注意鉴权 Header 传递
- 结果 dev < 15% 为 ✅ 达标
- 错误率 > 0 时 exit code 1
- 不知道压测目标 QPS 时可以先跑 --qps 50 试水再调整
