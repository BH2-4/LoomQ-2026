# 真机证据跑批工具（WP3b）

本目录是**开发侧工具**，不属于 `starter_kit/` 评测物；依赖装在本地
`.venv`（Python 3.10，spinqit 只有 cp310 wheel）。凭证一律走环境变量，
严禁写入仓库。

## 环境准备（已完成）

```bash
cd tools/qpu
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python spinqit pyqpanda
```

macOS 注意：spinqit wheel 的 rpath 有缺陷，运行时要设
`DYLD_LIBRARY_PATH=.venv/lib/python3.10/site-packages/spinqit`。

## 凭证

| 平台 | 环境变量 | 获取方式 |
|---|---|---|
| SpinQ 量旋云 | `SPINQ_USERNAME`、`SPINQ_KEYFILE` | cloud.spinq.cn 控制台 → API 密钥页：记下用户名并**下载 RSA 私钥文件**（spinqit 用私钥签名登录），`SPINQ_KEYFILE` 指向该 pem 文件路径 |
| 本源量子云 | `ORIGINQ_TOKEN` | qcloud.originqc.com.cn → 个人中心 → API Key（一串字符） |

建议放进 `tools/qpu/.env`（已 gitignore），跑前 `export $(grep -v '^#' .env | xargs)`。

## 跑真机（先小 shots 试水，成功再跑正式档）

```bash
# SpinQ 超导真机（先看平台列表再提交）
DYLD_LIBRARY_PATH=.venv/lib/python3.10/site-packages/spinqit \
SPINQ_USERNAME=xxx SPINQ_KEYFILE=/path/to/key.pem \
.venv/bin/python run_spinq_qpu.py --list
DYLD_LIBRARY_PATH=.venv/lib/python3.10/site-packages/spinqit \
SPINQ_USERNAME=xxx SPINQ_KEYFILE=/path/to/key.pem \
.venv/bin/python run_spinq_qpu.py --qasm ../../starter_kit/circuits/bell.qasm --shots 1000

# 本源 悟空真机
ORIGINQ_TOKEN=xxx .venv/bin/python run_originq_qpu.py \
  --qasm ../../starter_kit/circuits/bell.qasm --shots 1000
```

证据 JSON 自动落到 `starter_kit/evidence/files/{spinq,originq}/`，
包含平台、job_id、UTC 时间戳、shots、提交的电路文本与平台原始结果——
正好覆盖 evidence 模板要求的全部字段。
