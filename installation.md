# ai-bench Installation

Single-file Python tool, no dependencies beyond urllib3 (usually pre-installed).

## Install

Run the following command in your terminal:

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
```

## Verify

```bash
ai-bench --help
```

## Dependencies

- urllib3 (recommended, provides connection pool, usually pre-installed)
- Falls back to urllib.request (stdlib) if urllib3 is missing
- form-data requires urllib3

```bash
pip install urllib3
```

## Usage

```bash
ai-bench --url http://host/api --qps 500 --duration 60
```

See README.md for full usage examples.
