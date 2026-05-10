#!/usr/bin/env python3
"""
ai-bench — AI-friendly HTTP benchmark tool.

Single-file, zero‑install (urllib3 often pre‑installed).
Usage:  python bench.py --url http://host/api --qps 500 --duration 30
"""

import argparse
import sys
import threading
import time
import statistics

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
            (self.latencies if success else self.errors).append(latency_ms)  # type: ignore

    def snapshot(self):
        with self._lock:
            return list(self.latencies), self.errors

    def total(self):
        with self._lock:
            return len(self.latencies) + self.errors


# ── worker thread ────────────────────────────────────────────────

class BenchWorker(threading.Thread):
    """One thread sending requests at a controlled per‑thread rate."""

    def __init__(self, url, method, headers, body,
                 qps_per_thread, result_ref, pool, stop_flag):
        super().__init__(daemon=True)
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.qps = qps_per_thread
        self.result_ref = result_ref      # atomic pointer (list[BenchResult])
        self.pool = pool
        self.stop = stop_flag

    def run(self):
        delay = 1.0 / self.qps
        next_tick = time.monotonic()

        while not self.stop.is_set():
            # pacing
            now = time.monotonic()
            if now < next_tick:
                time.sleep(next_tick - now)
                if self.stop.is_set():
                    break
                now = next_tick

            # request
            start = time.monotonic()
            ok = False
            try:
                if HAS_POOL:
                    resp = self.pool.request(
                        self.method, self.url,
                        body=self.body, headers=self.headers,
                    )
                    resp.data                      # consume
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

            # record (uses current phase's result collector)
            r = self.result_ref[0]
            if r is not None:
                r.add(elapsed_ms, ok)

            next_tick = now + delay


# ── probing ──────────────────────────────────────────────────────

def probe(url, method, headers, body, pool):
    """Warm the connection pool and measure baseline latency."""
    latencies = []
    for _ in range(5):
        start = time.monotonic()
        try:
            if HAS_POOL:
                resp = pool.request(method, url, headers=headers)
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

    return (
        "## ai-bench Report\n\n"
        "### Summary\n"
        "| Target QPS | Actual QPS | Status | Duration | Total Req | Errors | Error % |\n"
        "|-----------|-----------|--------|---------|----------|-------|--------|\n"
        f"| {stats['target_qps']} | {stats['actual_qps']} "
        f"| {'✅' if ok else '⚠️'} | {stats['duration']}s "
        f"| {stats['total_requests']} | {stats['errors']} "
        f"| {stats['error_pct']}% |\n\n"
        "### Latency (ms)\n"
        "| Avg | P50 | P90 | P95 | P99 | Min | Max |\n"
        "|-----|-----|-----|-----|-----|-----|-----|\n"
        f"| {l['avg']} | {l['p50']} | {l['p90']} | {l['p95']} "
        f"| {l['p99']} | {l['min']} | {l['max']} |\n"
    )


# ── main ────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="ai-bench: AI-friendly HTTP benchmark")
    ap.add_argument("--url", "-u", required=True, help="Target URL")
    ap.add_argument("--qps", "-q", type=int, required=True, help="Target QPS")
    ap.add_argument("--duration", "-d", type=int, required=True, help="Duration (seconds)")
    ap.add_argument("--method", "-m", default="GET", help="HTTP method")
    ap.add_argument("--threads", "-t", type=int, default=0,
                    help="Thread count (0 = auto)")
    ap.add_argument("--header", "-H", action="append",
                    help="Custom header, e.g. -H 'Authorization: Bearer x'")
    ap.add_argument("--body", "-b", help="Request body (for POST/PUT)")
    ap.add_argument("--warmup", type=int, default=3,
                    help="Warmup seconds (0 = skip)")
    args = ap.parse_args()

    # headers
    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()

    # pool / fallback
    if not HAS_POOL:
        pool = None
        print("[warn] urllib3 not found — falling back to urllib.request (no connection pool).")
        print("       Install: pip install urllib3\n")
    else:
        pool = urllib3.PoolManager(
            maxsize=200,
            retries=urllib3.Retry(0),
            timeout=urllib3.Timeout(connect=10, read=30),
            cert_reqs="CERT_NONE",
        )

    # probe
    print(f"🔍 Probing {args.url} …")
    probe_ms = probe(args.url, args.method, headers, args.body, pool)
    print(f"   baseline avg: {probe_ms:.1f} ms")

    n_threads = args.threads or suggest_threads(probe_ms, args.qps)
    qpt = args.qps / n_threads
    print(f"   threads={n_threads}  per-thread rate={qpt:.1f} qps")

    # workers
    result_ref = [BenchResult()]     # atomic pointer for phase-swapping
    stop = threading.Event()
    workers = [
        BenchWorker(args.url, args.method, headers, args.body,
                    qpt, result_ref, pool, stop)
        for _ in range(n_threads)
    ]

    # warmup
    if args.warmup:
        wm = BenchResult()
        result_ref[0] = wm
        for w in workers:
            w.start()
        print(f"\n🔥 Warmup ({args.warmup}s) …")
        time.sleep(args.warmup)
        _, warm_ok = wm.snapshot()
        print(f"   warmup requests done (errors={warm_ok})")

    # main test
    main_result = BenchResult()
    result_ref[0] = main_result
    start = time.monotonic()
    print(f"\n⚡ Benchmarking {args.qps} qps for {args.duration}s …")
    time.sleep(args.duration)
    stop.set()

    for w in workers:
        w.join(timeout=5)

    elapsed = time.monotonic() - start

    # report
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
