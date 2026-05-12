#!/usr/bin/env python3
"""
ai-bench — AI-friendly HTTP benchmark tool.

Single-file, zero‑install (urllib3 often pre‑installed).
Usage:  python bench.py --url http://host/api --qps 500 --duration 30

HTTP methods: GET, POST, PUT, DELETE, PATCH …
Body formats: --body (raw), --json, --form (urlencoded), --form-data (multipart)
"""

import argparse
import json as json_mod
import sys
import threading
import time
import statistics
import urllib.parse

try:
    import urllib3
    HAS_POOL = True
except ImportError:
    HAS_POOL = False
    import urllib.request as urllib_req


# ── result collector ──────────────────────────────────────────────

class BenchResult:
    """Thread-safe latency + error accumulator."""

    def __init__(self):
        self.latencies: list[float] = []
        self.errors = 0
        self._lock = threading.Lock()

    def add(self, latency_ms: float, success: bool):
        with self._lock:
            (self.latencies if success else self.errors).append(latency_ms)

    def snapshot(self):
        with self._lock:
            return list(self.latencies), self.errors

    def total(self):
        with self._lock:
            return len(self.latencies) + self.errors


# ── body helpers ──────────────────────────────────────────────────

def _parse_kv_pairs(items):
    """Parse ['key=val', 'k2=v2'] into dict."""
    d = {}
    for item in items or []:
        if "=" in item:
            k, v = item.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def prepare_body(args):
    """
    Convert --json / --form / --form-data / --body into
    (body, extra_headers, multipart_fields).
    Only one body type may be used.
    """
    given = [k for k in ["body", "json", "form", "form_data"] if getattr(args, k)]
    if len(given) > 1:
        sys.exit(f"error: --{'/--'.join(given)} are mutually exclusive")

    body = None
    extra = {}
    multipart = None

    if args.json:
        body = args.json
        extra["Content-Type"] = "application/json"

    elif args.form:
        data = _parse_kv_pairs(args.form)
        body = urllib.parse.urlencode(data)
        extra["Content-Type"] = "application/x-www-form-urlencoded"

    elif args.form_data:
        data = _parse_kv_pairs(args.form_data)
        if HAS_POOL:
            multipart = data
        else:
            sys.exit("error: --form-data requires urllib3 (pip install urllib3)")

    elif args.body:
        body = args.body

    return body, extra, multipart


# ── worker thread ────────────────────────────────────────────────

class BenchWorker(threading.Thread):
    """One thread sending requests at a controlled per‑thread rate."""

    def __init__(self, url, method, headers, body, multipart_fields,
                 qps_per_thread, result_ref, pool, stop_flag):
        super().__init__(daemon=True)
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.multipart = multipart_fields
        self.qps = qps_per_thread
        self.result_ref = result_ref
        self.pool = pool
        self.stop = stop_flag

    def run(self):
        delay = 1.0 / self.qps
        next_tick = time.monotonic()

        while not self.stop.is_set():
            now = time.monotonic()
            if now < next_tick:
                time.sleep(next_tick - now)
                if self.stop.is_set():
                    break
                now = next_tick

            start = time.monotonic()
            ok = False
            try:
                if HAS_POOL:
                    if self.multipart:
                        resp = self.pool.request(
                            self.method, self.url,
                            fields=self.multipart,
                            headers=self.headers,
                        )
                    else:
                        resp = self.pool.request(
                            self.method, self.url,
                            body=self.body,
                            headers=self.headers,
                        )
                    resp.data
                else:
                    req = urllib_req.Request(
                        self.url, data=self.body, headers=self.headers,
                        method=self.method,
                    )
                    with urllib_req.urlopen(req, timeout=30):
                        pass
                ok = True
            except Exception:
                pass

            elapsed_ms = (time.monotonic() - start) * 1000

            r = self.result_ref[0]
            if r is not None:
                r.add(elapsed_ms, ok)

            next_tick = now + delay


# ── probing ──────────────────────────────────────────────────────

def probe(url, method, headers, body, multipart_fields, pool):
    """Warm connection pool and measure baseline latency."""
    latencies = []
    for _ in range(5):
        start = time.monotonic()
        try:
            if HAS_POOL:
                if multipart_fields:
                    resp = pool.request(method, url, fields=multipart_fields,
                                        headers=headers)
                else:
                    resp = pool.request(method, url, body=body, headers=headers)
                resp.data
            else:
                req = urllib_req.Request(url, data=body, headers=headers,
                                         method=method)
                with urllib_req.urlopen(req, timeout=30):
                    pass
            latencies.append((time.monotonic() - start) * 1000)
        except Exception:
            pass
        time.sleep(0.1)
    return statistics.mean(latencies) if latencies else 100.0


def suggest_threads(probe_ms, target_qps):
    """Guess a reasonable thread count."""
    max_per_thread = 1000.0 / max(probe_ms, 1)
    raw = max(4, int(target_qps / max_per_thread * 1.2))
    return min(200, raw)


# ── report ───────────────────────────────────────────────────────

def fmt_report(stats):
    l = stats["latency_ms"]
    diff = abs(stats["actual_qps"] - stats["target_qps"])
    ok = diff / max(stats["target_qps"], 1) < 0.15

    ratio = stats['actual_qps'] / max(stats['target_qps'], 1)
    lines = []
    lines.append(f"Throughput: {'✅ 达标' if abs(ratio-1)<0.1 else '⚠️ 偏差' + ('偏高' if ratio>1 else '偏低')} "
                 f"(目标 {stats['target_qps']} qps，实际 {stats['actual_qps']} qps，{ratio*100:.0f}%)")
    lines.append(f"延迟分布：中位数 {l['p50']}ms，90% 请求在 {l['p90']}ms 内完成，"
                 f"99% 请求在 {l['p99']}ms 内完成")
    if l['min'] < l['p50'] * 0.3:
        lines.append(f"最快响应 {l['min']}ms，说明大多数请求处理非常快")
    if l['max'] > l['p99'] * 3:
        lines.append(f"最慢响应 {l['max']}ms 显著偏离 P99（{l['p99']}ms），存在长尾延迟")
    if stats['error_pct'] == 0:
        lines.append(f"错误率 0% ✅ —— 接口稳定")
    else:
        lines.append(f"错误率 {stats['error_pct']}% ⚠️ —— 需要关注")
    analysis = "\n".join(lines)

    return (
        "## ai-bench Report\n\n"
        "### 结果\n"
        "| 目标 QPS | 实际 QPS | 状态 | 耗时 | 请求总数 | 错误数 | 错误率 |\n"
        "|---------|---------|------|------|---------|-------|-------|\n"
        f"| {stats['target_qps']} | {stats['actual_qps']} "
        f"| {'✅' if ok else '⚠️'} | {stats['duration']}s "
        f"| {stats['total_requests']} | {stats['errors']} "
        f"| {stats['error_pct']}% |\n\n"
        "### 延迟 (ms)\n"
        "| 平均 | 中位数 | P90 | P95 | P99 | 最小 | 最大 |\n"
        "|------|--------|-----|-----|-----|------|------|\n"
        f"| {l['avg']} | {l['p50']} | {l['p90']} | {l['p95']} "
        f"| {l['p99']} | {l['min']} | {l['max']} |\n\n"
        "### 分析\n"
        f"{analysis}\n"
    )


# ── main ────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="ai-bench: AI-friendly HTTP benchmark",
        epilog="Body options (--body / --json / --form / --form-data) are mutually exclusive."
    )
    ap.add_argument("--url", "-u", required=True, help="Target URL")
    ap.add_argument("--qps", "-q", type=int, required=True, help="Target QPS")
    ap.add_argument("--duration", "-d", type=int, required=True,
                    help="Duration (seconds)")
    ap.add_argument("--method", "-m", default="GET",
                    help="HTTP method: GET, POST, PUT, DELETE, PATCH … (default GET)")
    ap.add_argument("--threads", "-t", type=int, default=0,
                    help="Thread count (0 = auto)")
    ap.add_argument("--header", "-H", action="append",
                    help="Custom header, repeatable, e.g. -H 'Authorization: Bearer x'")
    ap.add_argument("--body", "-b", help="Raw request body")
    ap.add_argument("--json", help="JSON body (auto Content-Type: application/json)")
    ap.add_argument("--form", action="append",
                    help="Form field key=value (repeatable, form-urlencoded)")
    ap.add_argument("--form-data", action="append",
                    help="Multipart form field key=value (repeatable)")
    ap.add_argument("--warmup", type=int, default=3,
                    help="Warmup seconds (0 = skip)")
    args = ap.parse_args()

    # ── headers ──────────────────────────────────────────────────
    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()

    # ── body preparation ─────────────────────────────────────────
    body, extra_headers, multipart = prepare_body(args)
    headers.update(extra_headers)

    # ── pool ──────────────────────────────────────────────────────
    if not HAS_POOL:
        pool = None
        print("[warn] urllib3 not found — falling back to urllib.request (no connection pool).")
        print("       Install: pip install urllib3\n")
    else:
        pool = urllib3.PoolManager(
            maxsize=200,
            retries=urllib3.Retry(0),
            timeout=urllib3.Timeout(connect=10, read=30),
        )

    # ── probe ────────────────────────────────────────────────────
    print(f"🔍 Probing {args.method} {args.url} …")
    probe_ms = probe(args.url, args.method, headers, body, multipart, pool)
    print(f"   baseline avg: {probe_ms:.1f} ms")

    n_threads = args.threads or suggest_threads(probe_ms, args.qps)
    qpt = args.qps / n_threads
    print(f"   threads={n_threads}  per-thread rate={qpt:.1f} qps")

    # ── workers ──────────────────────────────────────────────────
    result_ref = [BenchResult()]
    stop = threading.Event()
    workers = [
        BenchWorker(args.url, args.method, headers, body, multipart,
                    qpt, result_ref, pool, stop)
        for _ in range(n_threads)
    ]

    # ── warmup ────────────────────────────────────────────────────
    if args.warmup:
        wm = BenchResult()
        result_ref[0] = wm
        for w in workers:
            w.start()
        print(f"\n🔥 Warmup ({args.warmup}s) …")
        time.sleep(args.warmup)
        _, warm_ok = wm.snapshot()
        print(f"   warmup requests done (errors={warm_ok})")

    # ── main test ────────────────────────────────────────────────
    main_result = BenchResult()
    result_ref[0] = main_result
    start = time.monotonic()
    print(f"\n⚡ Benchmarking {args.qps} qps for {args.duration}s …")
    time.sleep(args.duration)
    stop.set()

    for w in workers:
        w.join(timeout=5)

    elapsed = time.monotonic() - start

    # ── report ────────────────────────────────────────────────────
    latencies, errs = main_result.snapshot()
    total = len(latencies) + errs
    latencies.sort()
    e_pct = round(errs / total * 100, 2) if total else 0

    def pct(p):
        return latencies[int(len(latencies) * p)]

    st = {
        "target_qps": args.qps,
        "actual_qps": round(total / elapsed, 1),
        "total_requests": total,
        "errors": errs,
        "error_pct": e_pct,
        "duration": round(elapsed, 1),
        "latency_ms": {
            "avg": round(statistics.mean(latencies), 1),
            "p50": round(statistics.median(latencies), 1),
            "p90": round(pct(0.90), 1),
            "p95": round(pct(0.95), 1),
            "p99": round(pct(0.99), 1),
            "min": round(latencies[0], 1),
            "max": round(latencies[-1], 1),
        },
    }

    print(f"\n📊\n")
    print(fmt_report(st))
    sys.exit(0 if e_pct == 0 and total > 0 else 1)


if __name__ == "__main__":
    main()
