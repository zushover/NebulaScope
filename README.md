# NebulaScope

NebulaScope 是一个面向 LLM / VLM 推理优化研究的轻量本地实时监控面板。它将 NVIDIA GPU 遥测与推理引擎指标分开采集，通过统一的内存指标仓库和 WebSocket 推送到浏览器。

第一版专注于可运行的单机 MVP，不包含数据库、账号系统、分布式推理或具体推理引擎实现。

## 功能

- NVML GPU 指标：利用率、显存、功耗、温度、核心/显存时钟
- 推理指标：throughput、token 数、batch、请求数、TTFT、TPOT、KV Cache、prefill/decode latency
- 0.75 秒默认采样与 WebSocket 实时推送
- 可插拔 `EngineMetricsAdapter`
- Python Hook 与 HTTP Metrics API
- 无 GPU 或无推理引擎时仍可正常启动
- 内置 Mock 推理源和原生 Canvas 实时折线图
- Evaluation / Accuracy 接口预留

## 安装

建议使用 Python 3.10 或更高版本。

```bash
cd NebulaScope
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动

### Windows 一键启动

直接双击项目根目录中的启动器：

- `start_mock.bat`：启动完整 Mock 推理面板，适合开发和演示
- `start_gpu_only.bat`：只采集本机真实 GPU 指标

启动器会自动检查本地虚拟环境、按需安装依赖并打开浏览器。终端窗口需要保持开启；按 `Ctrl+C` 即可停止服务。

### 命令行启动

Mock 模式（推荐先用它验证完整 Dashboard）：

```bash
python backend/main.py --mock
```

浏览器访问 <http://localhost:8000>。

仅监控本机 GPU：

```bash
python backend/main.py
```

可选参数：

```bash
python backend/main.py --mock --gpu-index 0 --interval 0.5 --host 127.0.0.1 --port 8000
```

若系统没有 NVIDIA GPU、驱动或可用 NVML，GPU 区域会显示不可用，但推理指标、Mock 模式和 API 仍可工作。

## 接入自研推理代码

### Python Hook

在同一 Python 进程中，可以使用统一接口发布数据：

```python
from backend.metrics import metrics

metrics.update(
    status="running",
    model_name="My-VLM",
    engine_name="CustomEngine",
    throughput=145.2,
    input_tokens=2048,
    output_tokens=512,
    batch_size=8,
    active_requests=6,
    ttft=43.0,
    tpot=7.2,
    kv_cache_used=6.2,
    kv_cache_total=12.0,
    prefill_latency=86.0,
    decode_latency=28.0,
)
```

短名称会映射到统一字段，例如 `throughput` → `throughput_tps`、`ttft` → `ttft_ms`。KV used/total 同次提交时会自动计算 usage %。

### HTTP API

外部进程可向监控服务发布指标：

```bash
curl -X POST http://localhost:8000/api/metrics/inference \
  -H "Content-Type: application/json" \
  -d '{"model_name":"MyModel","status":"running","throughput":145,"batch_size":8,"ttft":43}'
```

当前快照：`GET /api/metrics`。交互式接口文档：<http://localhost:8000/docs>。

## 增加推理引擎 Adapter

继承 `backend/adapters/base.py` 中的接口：

```python
from backend.adapters.base import EngineMetricsAdapter


class CustomEngineAdapter(EngineMetricsAdapter):
    def get_metrics(self) -> dict:
        return {
            "status": "running",
            "model_name": "MyModel",
            "throughput_tps": 120.0,
            "batch_size": 4,
        }
```

`get_metrics()` 应快速返回一份最新快照。后续的 `VLLMAdapter`、`SGLangAdapter` 可以通过引擎内部统计、Prometheus endpoint 或自定义 Hook 实现，而无需修改 Dashboard。

## Evaluation 接口

第一版只预留展示与提交接口：

```bash
curl -X POST http://localhost:8000/api/metrics/evaluation \
  -H "Content-Type: application/json" \
  -d '{"benchmark":"MMLU","metric_name":"accuracy","score":0.712,"samples":14042}'
```

后续可由 lm-evaluation-harness、MMLU、GSM8K、HumanEval 或自定义评测 adapter 调用。

## 测试

```bash
pytest -q
```

## 目录

```text
NebulaScope/
├── backend/
│   ├── main.py
│   ├── metrics/       # GPU、推理、评测与内存存储
│   ├── adapters/      # 可插拔引擎 adapter
│   └── api/           # WebSocket routes
├── frontend/          # 无构建依赖的实时 Dashboard
├── tests/
├── requirements.txt
└── README.md
```

## 下一步扩展方向

- vLLM / SGLang Prometheus adapter
- 多 GPU 指标与进程级显存归因
- KV block/page 命中率、驱逐、复用率与碎片率
- 量化配置和实验元数据
- benchmark run 与 accuracy 历史
- profiler trace 导入与对齐分析
