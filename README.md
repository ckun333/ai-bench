# ai-bench

AI-friendly HTTP benchmark tool。

给它一个 URL 和目标 QPS，它帮你压测、出报告，不需要理解线程数、ramp-up、pacing 这些底层参数。

```bash
# 一行命令，开始压测
ai-bench --url http://your-api:8080/api/list --qps 500 --duration 30
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

# POST + 鉴权
ai-bench -u https://api.example.com/login -q 200 -d 30 \
    -m POST -b '{"username":"admin","password":"pass"}' \
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
| `--method` | `-m` | ❌ | GET | HTTP 方法 |
| `--threads` | `-t` | ❌ | 自动 | 线程数（0 = 自动） |
| `--header` | `-H` | ❌ | — | 自定义请求头，可多次使用 |
| `--body` | `-b` | ❌ | — | 请求体 |
| `--warmup` | — | ❌ | 3 | 预热秒数（0=跳过） |

---

## 输出示例

```
## ai-bench Report

### Summary
| Target QPS | Actual QPS | Status | Duration | Total Req | Errors | Error % |
|-----------|-----------|--------|---------|----------|-------|--------|
| 500 | 497.7 | ✅ | 60.0s | 29879 | 0 | 0.0% |

### Latency (ms)
| Avg | P50 | P90 | P95 | P99 | Min | Max |
|-----|-----|-----|-----|-----|-----|-----|
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

## Roadmap

### v1.0 ✅ 当前
- [x] URL / QPS / Duration 控制
- [x] 自动线程数计算
- [x] 预热阶段
- [x] Header / Body / Method 支持
- [x] Markdown 报告
- [x] urllib3 连接池 + 标准库降级
- [x] OpenClaw Skill 集成

### v1.5 🔜 短期
- [ ] 场景配置文件（JSON/YAML，多端点 + 参数化）
- [ ] 渐增式 ramp-up（QPS 从低到高渐变）
- [ ] CSV / JSON 输出（CI 集成用）
- [ ] 响应体校验（断言状态码、关键字等）

### v2.0 🚀 中期
- [ ] Cookie / Session 维持
- [ ] Auth token 轮换
- [ ] Think time 模拟真实用户行为
- [ ] 多场景并发测试
- [ ] 错误详情记录（哪些请求失败了）

### v3.0 🌟 远期
- [ ] Proxy 支持
- [ ] SLA 断言（P99 < 500ms 自动告警）
- [ ] Web 实时看板
- [ ] 分布式压测（多节点协同）

---

## 协议

MIT
