# ai-bench

AI-friendly HTTP benchmark tool。

给它一个 URL 和目标 QPS，它帮你压测、出报告，不需要理解线程数、ramp-up、pacing 这些底层参数。

```bash
ai-bench --url http://your-api:8080/api/list --qps 500 --duration 30
```

## For Humans

在终端执行以下命令安装 ai-bench：

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
ai-bench --help
```

或者用一键安装脚本：

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/install.sh | bash
```

## For AI Agents

告诉 AI 执行以下命令安装：

```bash
# 如果 bench.py 已在项目中：
python /path/to/ai-bench/bench.py --url ... --qps ... --duration ...

# 或先 curl 下载再使用：
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench && chmod +x ~/.local/bin/ai-bench && ai-bench --url ... --qps 500 --duration 60
```

---

## 快速安装

```bash
# 前提：Python 3 + urllib3（通常预装）
pip install urllib3   # 如缺失

# 下载并安装
curl -sL https://github.com/ckun333/ai-bench/raw/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench

# 验证
ai-bench --help
```

---

## 快速使用

```bash
# 基础（三个必填）
ai-bench -u https://api.example.com/users -q 500 -d 60

# POST + JSON
ai-bench -u https://api.example.com/login -q 200 -d 60 \
    -m POST --json '{"username":"admin","pass":"123"}'

# POST + Form-urlencoded
ai-bench -u https://api.example.com/login -q 200 -d 60 \
    -m POST --form "username=admin" --form "pass=123"

# PUT / DELETE
ai-bench -u https://api.example.com/item/1 -q 100 -d 30 -m PUT --json '{"name":"new"}'
ai-bench -u https://api.example.com/item/1 -q 100 -d 30 -m DELETE

# 自定义 Header
ai-bench -u https://api.example.com/search -q 500 -d 60 \
    -H "Authorization: Bearer token123"

# 指定线程数（默认自动计算）
ai-bench -u https://api.example.com/search -q 1000 -d 30 -t 50

# 跳过预热（默认3秒）
ai-bench -u https://api.example.com/ping -q 300 -d 10 --warmup 0
```

---

## 参数说明

| 参数 | 缩写 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--url` | `-u` | ✅ | — | 目标 URL |
| `--qps` | `-q` | ✅ | — | 目标每秒请求数 |
| `--duration` | `-d` | ✅ | — | 测试持续秒数 |
| `--method` | `-m` | ❌ | GET | HTTP 方法（GET/POST/PUT/DELETE/PATCH…） |
| `--threads` | `-t` | ❌ | 自动 | 线程数（0 = 自动） |
| `--header` | `-H` | ❌ | — | 自定义请求头，可多次使用 |
| `--body` | `-b` | ❌ | — | 原始请求体 |
| `--json` | — | ❌ | — | JSON 请求体（自动设置 Content-Type） |
| `--form` | — | ❌ | — | 表单字段 key=value（可多次使用） |
| `--form-data` | — | ❌ | — | Multipart 字段 key=value（可多次使用） |
| `--warmup` | — | ❌ | 3 | 预热秒数（0=跳过） |

> `--body` / `--json` / `--form` / `--form-data` 互斥，不能同时使用。

---

## 输出示例

```
## ai-bench Report

### 结果
| 目标 QPS | 实际 QPS | 状态 | 耗时 | 请求总数 | 错误数 | 错误率 |
|---------|---------|------|------|---------|-------|-------|
| 500 | 497.7 | ✅ | 60.0s | 29879 | 0 | 0.0% |

### 延迟 (ms)
| 平均 | 中位数 | P90 | P95 | P99 | 最小 | 最大 |
|------|--------|-----|-----|-----|------|------|
| 12.6 | 8.7 | 21.9 | 26.2 | 55.2 | 4.9 | 397.6 |
```

---

## 原理

1. **探测** — 先发几个请求估算基线延迟
2. **计算线程数** — 根据延迟自动算出合理并发线程数
3. **预热** — 全线程跑几秒，让连接池预热
4. **正式测试** — 以 GUN 模式控制每线程速率（固定 QPS）
5. **出报告** — 标准 Markdown 表格，AI 和人一眼看懂

---

## 协议

MIT
