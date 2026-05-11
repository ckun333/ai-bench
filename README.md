# ai-bench

AI-friendly HTTP benchmark tool。给一个 URL 和目标 QPS，直接出结果和分析。

## For Humans

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
ai-bench --help
```

## For AI Agents

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench && chmod +x ~/.local/bin/ai-bench
```

## 使用说明

### 你告诉 AI

> 帮我看下 www.xxx.com/api/list 接口能不能抗 500 qps，跑 1 分钟

### AI 执行

```bash
ai-bench -u www.xxx.com/api/list -q 500 -d 60
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

### 更多用法

| 场景 | 你告诉 AI | AI 执行 |
|------|----------|---------|
| POST + JSON | 压测登录接口 www.xxx.com/api/login，POST 请求，body 传 JSON `{"user":"admin","pass":"123"}`，200 qps，跑 30 秒 | `ai-bench -u www.xxx.com/api/login -q 200 -d 30 -m POST --json '{"user":"admin","pass":"123"}'` |
| 表单提交 | 压测提交表单接口 www.xxx.com/api/submit，POST 请求，表单字段 name=test、type=1，100 qps，跑 1 分钟 | `ai-bench -u www.xxx.com/api/submit -q 100 -d 60 -m POST --form "name=test" --form "type=1"` |
| PUT 更新 | 压测更新接口 www.xxx.com/api/item/1，PUT 请求，body 传 JSON `{"name":"new"}`，100 qps，跑 30 秒 | `ai-bench -u www.xxx.com/api/item/1 -q 100 -d 30 -m PUT --json '{"name":"new"}'` |
| DELETE | 压测删除接口 www.xxx.com/api/item/1，DELETE 请求，100 qps，跑 30 秒 | `ai-bench -u www.xxx.com/api/item/1 -q 100 -d 30 -m DELETE` |
| 带鉴权 | 压测列表接口 www.xxx.com/api/list，GET 请求，带 Authorization header `Bearer tok_xxx`，500 qps，跑 1 分钟 | `ai-bench -u www.xxx.com/api/list -q 500 -d 60 -H "Authorization: Bearer tok_xxx"` |

## MIT
