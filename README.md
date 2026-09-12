# AI 内容检测服务（后端）

针对文本 / 图像 / 视频的 AI 内容检测后端服务。当前默认使用确定性 mock 检测器，
使完整 API 流程在没有任何机器学习依赖的情况下即可运行与联调；真实模型的接入入口
已预留（见 `DETECTORS.md`）。

- 接口契约：`API_zh.md` / `API_en.md`
- 检测器实现指南：`DETECTORS.md`

---

## 功能特性

- 文本、图像、视频三种检测模态，统一走「创建任务 → 轮询结果」异步流程
- 任务状态机：`queued → processing → completed / failed`，由后台线程执行推理
- 统一响应契约（`DetectionResponse`），与前端严格对应
- 统一异常处理与错误响应体 `{ "error": { "code", "message" } }`
- 模型目录接口 `GET /api/v1/models`，支持按模态筛选
- CORS 白名单可通过环境变量配置

## 依赖

本项目为 mock 先行架构，目前**不包含任何机器学习库**，只有一份极小的 Web 依赖集：

| 库 | 用途 |
| --- | --- |
| `fastapi` | Web 框架：路由、上传、BackgroundTasks、CORS、异常处理 |
| `uvicorn` | ASGI 服务器（`run.py` 启动入口） |
| `pydantic`（v2） | 请求 / 响应数据模型（`app/models.py`，用到 `model_copy` 等 v2 API） |

> `starlette` 为 `fastapi` 的底层依赖，无需单独安装，但代码直接引用了
> `starlette.exceptions.HTTPException`。

其余全部为标准库：`asyncio`、`logging`、`os`、`pathlib`、`threading`、`uuid`、
`hashlib`、`time`、`typing`。

接入真实模型时，可依据模态按需添加推理库（如 `torch`、`opencv-python`、
`Pillow`），不影响现有接口行为（见 `DETECTORS.md` §8）。

## 目录结构

```
run.py                      uvicorn 启动入口
app/
├── main.py                 FastAPI 应用、CORS、全局异常处理、/health
├── config.py               前缀、mock 延迟、模型目录、文件类型白名单
├── models.py               Pydantic 契约（DetectionResult 等）
├── errors.py               模型校验与任务 ID 生成
├── files.py                上传文件读取与类型校验（后端为安全边界）
├── task_store.py           内存任务存储（线程安全）
├── runner.py               后台执行检测器、维护任务状态机
├── routers/                HTTP 路由：text / image / video / tasks / material
└── detectors/              模型层：mock.py（默认）+ text/image/video.py（待实现）
```

## 快速开始

```bash
# 1. 创建并激活环境
conda create -n detection-service-back python=3.11 -y
conda activate detection-service-back

# 2. 安装依赖
pip install fastapi "uvicorn[standard]"

# 3. 启动服务（默认 http://0.0.0.0:8000，--reload 热重载）
python run.py
# 或
python -m uvicorn app.main:app --reload
```

验证：

- 健康检查：`GET http://localhost:8000/health` → `{"status": "ok"}`
- 交互式文档：`http://localhost:8000/docs`

## 配置（环境变量）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CORS_ALLOWED_ORIGINS` | `*` | 允许的跨域来源，逗号分隔 |
| `MOCK_TEXT_DELAY` | `1.0` | mock 文本检测延迟（秒），设 `0` 关闭 |
| `MOCK_IMAGE_DELAY` | `2.0` | mock 图像检测延迟（秒） |
| `MOCK_VIDEO_DELAY` | `6.0` | mock 视频检测延迟（秒） |

## API 速览

所有接口位于前缀 `/api/v1` 之下：

- `POST /detections/text`（JSON：`model`、`context?`、`text`）
- `POST /detections/image`（multipart：`file`、`model`、`context?`）
- `POST /detections/video`（multipart：`file`、`model`、`context?`）
- `GET /tasks/{id}`（轮询检测结果）
- `GET /models`（模型目录，可选 `?modality=text|image|video`）
- `GET /health`（服务健康检查）

完整契约字段与示例见 `API_zh.md`。

## 接入真实模型

当前 `app/detectors/` 默认启用 `mock.py`，`text.py` / `image.py` / `video.py`
为待填充的占位实现。实现后仅需在 `app/detectors/__init__.py` 切换导入即可激活，
路由与任务调度无需改动。详见 `DETECTORS.md`。