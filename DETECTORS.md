# Detect 实现小组开发指南

本文档面向**编写真实检测模型代码**的开发小组，说明在哪里编写、有哪些
要求。只涉及模型推理代码，不涉及 HTTP 接口、任务调度与数据库。

---

## 1. 你的工作范围

后端采用 mock 先行（`app/detectors/mock.py`），真实模型尚未接入。
你的任务是**在下方三个文件中填充真实推理实现**（当前均为 `pass` 占位）：

| 文件 | 函数 | 模态 |
| ---- | ---- | ---- |
| `app/detectors/text.py` | `detect_text` | 文本 |
| `app/detectors/image.py` | `detect_image` | 图像 |
| `app/detectors/video.py` | `detect_video` | 视频 |

> **不要修改 `app/detectors/mock.py`**。它是确定性 mock，作为参考实现与
> 默认回退；真实模型接入前，服务靠它正常工作。

## 2. 整体架构（你只需关心最下面一层）

```
routers/        HTTP 入参校验、创建 queued 任务        (不要动)
   │
runner.py       后台线程中执行探测器、维护任务状态机    (不要动)
   │
detectors/      模型推理 —— 你在这里编码                ← 你的位置
   │
models.py       Pydantic 契约，返回类型 DetectionResult
```

调用链：前端提交 → 路由校验 → 创建任务（queued）→ `runner.py::run_detection`
在线程池中调用你的 `detect_*` → 任务变为 completed/failed。

## 3. 接口契约

每个 `detect_*` 是**同步阻塞函数**，返回 `app.models.DetectionResult`：

```python
from app.models import DetectionResult

def detect_text(text: str, context: str | None, model: str, version: str) -> DetectionResult:
    ...
```

`DetectionResult` 字段（与前端契约严格一致，字段名不可改）：

```python
result = DetectionResult(
    label="ai_generated | human_generated | uncertain",
    ai_probability=0.93,       # 0.0 ~ 1.0
    human_probability=0.07,    # 0.0 ~ 1.0，且 ai + human == 1.0
    confidence="low | medium | high",   # 模型对结论的自我评估
    reasoning="一句话解释为什么这样判定",  # 必填
)
```

### 3.1 label 判定约定

- `ai_generated` / `human_generated`：模型置信地作出判断。
- `uncertain`：无法判定时使用，此时概率应**接近 0.5**、`confidence` 为
  `low` 或 `medium`。

### 3.2 reasoning 必填

`reasoning` 是前端展示的可解释性文本，**不允许为空字符串**，应：
- 简短（1~2 句）、人类可读、与该结果对应；
- 诚实地描述依据（如文本结构特征 / 图像画质特征 / 采样帧特征）；
- 避免绝对化措辞，如 "Definitely AI"、"100% human"。

## 4. 参数说明

- `text` / `data`：原始用户内容（文件为原始字节 `bytes`）；
- `context`：用户补充信息（来源、背景），可选（可能为 `None`）；
- `model` / `version`：已解析的模型标识，用于日志与指标，不用做分发；
- `filename`（image）：原始文件名，扩展名已由 `app/files.py` 校验。

## 5. 如何把实现接上线（激活）

实现完成后，修改 `app/detectors/__init__.py` 末尾的导入，把对应模态从
mock 切换到你的模块：

```python
# 原来：
from app.detectors.mock import detect_text

# 改后：
from app.detectors.text import detect_text
```

其余（路由、任务、执行器）**无需任何改动**。`.pyc` 缓存或旧进程记得重启。

## 6. 编写要求

- **保持同步阻塞函数**：`runner.py` 已用 `asyncio.to_thread` 在线程池中
  执行你的函数，事件循环不会被阻塞；不要自己再包 async。若模型是
  GPU/进程型，可在 `runner.py` 内替换执行方式，但**函数签名保持同步**。
- **不要添加人工 sleep**：mock 用 `time.sleep` 模拟延迟（原因见 §7），
  真实模型的耗时来自推理本身，不需要加延迟。
- **不要伪造进度**：接口契约规定 `progress` 仅在确实可汇报时返回；任务
  状态机由 `runner.py` 维护，你只管返回结果。长视频若有真实阶段
  （拆帧→逐帧推理→聚合），可在 `runner.py` 中插入 `task_store.update()`
  汇报真实进度，但**不要**在检测函数里伪装修饰。
- **错误处理**：不要在 `detect_*` 内部抛 HTTP 异常或返回错误结构。推理
  失败直接 `raise`，`runner.py` 会捕获并转为 `failed` 任务（响应体含
  `error.code = "processing_error"`）。
- **资源安全**：加载模型时注意占用；解码文件前校验其真实格式（后端是
  安全边界，不可信任扩展名/MIME）。
- **确定性**：mock 当前对相同输入返回相同结果，方便测试。真实模型若
  无法保证确定性，不影响契约，只要概率与 reasoning 合理即可。

## 7. 关于延迟与视频 `seed`（重点）

- **延迟**：真实模型推理慢，因此接口被设计为「创建任务＋轮询」。mock
  在最内侧的 `detect_*` 里 `time.sleep` 模拟推理耗时（默认文本 1s、
  图像 2s、视频 6s），使前后端联调能体验真实时序。延迟可用环境变量
  `MOCK_TEXT_DELAY` / `MOCK_IMAGE_DELAY` / `MOCK_VIDEO_DELAY` 覆盖，
  设 `0` 可关闭。
- **视频 `seed`**：`detect_video` 当前签名接收 `seed`（对原始字节哈希，
  是 mock 保证确定性的产物），真实视频模型不需要。二选一：
  - 方案 A（改动最小）：保持现有签名；
  - 方案 B（推荐）：改为
    `detect_video(data: bytes, context: str | None, model: str, version: str)`
    直接接收原始字节，并同步修改 `app/routers/video.py` 里
    `detect_video_seed` 的调用点。

## 8. 开发与自测

```bash
conda run -n detection-service-back python run.py        # 启动服务
conda run -n detection-service-back python -m uvicorn app.main:app --reload   # 热重载
```

自测入口：`POST /api/v1/detections/{text|image|video}` → `GET /api/v1/tasks/{id}`
轮询直到 `completed`。接口文档见 `API_zh.md`。发现 mock 可用的环境变量
与依赖（如 torch、opencv、Pillow）直接安装，但**不要**改变现有接口行为。

## 9. 速查清单（提交前逐条核对）

- [ ] 在 `app/detectors/{text,image,video}.py` 对应函数中实现，`pass` 已移除
- [ ] 返回 `app.models.DetectionResult`，字段名未改
- [ ] `ai_probability + human_probability == 1.0`
- [ ] `reasoning` 非空、简短、诚实、与结果对应
- [ ] 函数为同步阻塞式，无人工 `sleep`、无假进度、无 HTTP 层错误
- [ ] `label == "uncertain"` 时概率接近 0.5
- [ ] `app/detectors/__init__.py` 已从 mock 切换到真实实现
- [ ] 起服务后用真实数据走通「创建任务 → 轮询 → completed」，并验证一次失败路径