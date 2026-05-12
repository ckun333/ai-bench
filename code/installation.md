# ai-bench 安装说明

单文件 Python 工具，唯一依赖 urllib3（通常已预装）。

## 安装

在终端执行以下命令：

```bash
curl -sL https://raw.githubusercontent.com/ckun333/ai-bench/main/bench.py -o ~/.local/bin/ai-bench
chmod +x ~/.local/bin/ai-bench
```

## 验证

```bash
ai-bench --help
```

## 依赖

- urllib3（推荐，提供连接池，通常已预装）
- 无 urllib3 时自动降级为标准库 urllib.request（无连接池）
- form-data 模式需要 urllib3

```bash
pip install urllib3
```

## 用法

```bash
ai-bench --url http://host/api --qps 500 --duration 60
```

完整用法见 README.md。
