# ai-bench

AI-friendly HTTP benchmark tool。

给你一个 URL 和目标 QPS，直接出结果和分析。

```bash
ai-bench --url http://your-api:8080/api/list --qps 500 --duration 30
```

## For Humans

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
ai-bench --help
```

## For AI Agents

### 你告诉 AI

> 帮我看下 /api/list 接口能不能抗 500 qps，跑 1 分钟

### AI 执行

```bash
ai-bench -u http://host/api/list -q 500 -d 60
```

### AI 返回

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

### 分析
Throughput: ✅ 达标 (目标 500 qps，实际 497.7 qps，100%)
延迟分布：中位数 8.7ms，90% 请求在 21.9ms 内完成，99% 请求在 55.2ms 内完成
错误率 0% ✅ —— 接口稳定
```

### 更多用法示例

| 场景 | 你说 | AI 执行 |
|------|------|--------|
| **POST + JSON 登录** | 压测登录接口，200 qps 半分钟 | `ai-bench -u http://host/api/login -q 200 -d 30 -m POST --json '{"user":"admin","pass":"123"}'` |
| **表单提交** | 压测提交表单，100 qps | `ai-bench -u http://host/api/submit -q 100 -d 30 -m POST --form "name=test" --form "type=1"` |
| **PUT 更新** | 压测修改接口 | `ai-bench -u http://host/api/item/1 -q 100 -d 30 -m PUT --json '{"name":"new"}'` |
| **DELETE** | 压测删除接口 | `ai-bench -u http://host/api/item/1 -q 100 -d 30 -m DELETE` |
| **加鉴权** | 带 token 压测 | `ai-bench -u http://host/api/list -q 500 -d 60 -H "Authorization: Bearer tok_xxx"` |

### 参数说明

| 参数 | 缩写 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--url` | `-u` | ✅ | — | 目标 URL |
| `--qps` | `-q` | ✅ | — | 目标每秒请求数 |
| `--duration` | `-d` | ✅ | — | 测试持续秒数 |
| `--method` | `-m` | ❌ | GET | HTTP 方法 |
| `--header` | `-H` | ❌ | — | 自定义请求头，可多次使用 |
| `--body` | `-b` | ❌ | — | 原始请求体 |
| `--json` | — | ❌ | — | JSON 请求体（自动 Content-Type） |
| `--form` | — | ❌ | — | 表单字段 key=value（可多次使用） |
| `--form-data` | — | ❌ | — | Multipart 字段 key=value（可多次使用） |
| `--threads` | `-t` | ❌ | 自动 | 线程数 |
| `--warmup` | — | ❌ | 3 | 预热秒数（0=跳过） |

> `--body` / `--json` / `--form` / `--form-data` 互斥，不能同时使用。

### 原理

1. **Probe** — 先发几个请求估算基线延迟
2. **自动算线程数** — 根据延迟算合理并发数
3. **Warmup** — 跑几秒预热连接池
4. **Benchmark** — GUN 模式控制固定 QPS
5. **Report** — 输出 Markdown 报告 + 分析
