# 前后端接口契约

本文档供后端开发者实现与本前端配套的检测服务，无需阅读前端代码。

---

## 1. 基础地址

- 前端读取 `NEXT_PUBLIC_API_BASE_URL`（如 `http://localhost:8000`）。
- 所有接口位于前缀 `/api/v1` 之下。
- 完整地址：`{NEXT_PUBLIC_API_BASE_URL}/api/v1/<endpoint>`。

## 2. 请求模型

每个检测请求都包含：

| 字段      | 类型   | 必填 | 含义                                          |
| --------- | ------ | ---- | --------------------------------------------- |
| `model`   | string | 是   | 要使用的检测模型标识（用户选择）。            |
| `context` | string | 否   | 用户提供的补充信息（如来源、背景）。          |
| 内容      | 不定   | 是   | 待检测内容：`text` 字段或 `file` 字段（见 §4）。|

说明：`model` 的取值由部署方定义。示例：`"text-detector"`、
`"image-detector"`、`"video-detector"`。

## 3. 通用规则

- 文本检测：请求与响应均为 `application/json`。
- 图像/视频检测：以 `multipart/form-data` 上传，包含
  `file`、`model`、`context` 三个字段。
- JSON 响应必须带 `Content-Type: application/json`。
- 非 2xx 错误响应体：

```json
{ "error": { "code": "invalid_text", "message": "用户可读的英文提示" } }
```

  `code` 可选，`message` 必填。不得包含堆栈信息。

## 4. 检测响应模型

所有检测接口返回同一结构。前端将其视为既定契约，不会适配字段名，因此
**字段名必须完全一致**。

```json
{
  "id": "string",
  "modality": "text | image | video",
  "status": "queued | processing | completed | failed",
  "progress": 0,
  "result": {
    "label": "ai_generated | human_generated | uncertain",
    "ai_probability": 0.93,
    "human_probability": 0.07,
    "confidence": "low | medium | high",
    "reasoning": "模型得出该结论的原因解释文本。"
  },
  "model": { "name": "string", "version": "string" },
  "error": { "code": "string", "message": "string" }
}
```

规则：

- `id`、`modality`、`status` 必填。
- `progress`（0–100）：可选；不得伪造中间值。
  `queued`/`processing` 阶段省略该字段，`completed` 时为 `100`。
- `result` 仅在 `status == "completed"` 时返回。
- `result.reasoning`：必填，一段简短、可读的解释（可解释性），与结果对应。
- `error` 仅在 `status == "failed"` 时返回。
- 终止状态：`completed` 与 `failed`。
- `ai_probability` / `human_probability` 取值范围 0–1。
- `confidence` 为模型对结论的自我评估（确定程度）。
- 模型无法判定时使用 `uncertain`。

## 5. 基于任务的全部检测（三种模态统一）

所有检测均采用「创建任务 → 轮询结果」的方式。任务 `id` 由后端生成；
前端**不管理任务**（无列表/取消/删除接口）。对最终用户而言，这只是一次
等待——提交后等待结果——行为上等同于同步请求，只是由于模型推理计算量
大，需要等待数秒。

```
POST /api/v1/detections/text    （JSON body：model、context?、text）
POST /api/v1/detections/image   （multipart：file、model、context?）
POST /api/v1/detections/video   （multipart：file、model、context?）
```

请求校验错误（`400` / `413` / `422`）仍由创建请求立即返回。成功后（`200`）
每个创建请求返回一个非终态的 `DetectionResponse`：

```json
{
  "id": "det_x1f9c02",
  "modality": "text",
  "status": "queued",
  "model": { "name": "text-detector", "version": "1.0.0" }
}
```

随后轮询结果：

```
GET /api/v1/tasks/:id
```

前端约每 2000 ms 轮询一次，在状态变为 `completed` 或 `failed` 时停止。
`progress` 在 `queued`/`processing` 阶段省略，`completed` 时为 `100`。

### 5.1 文本检测

```
POST /api/v1/detections/text
Content-Type: application/json
```

```json
{
  "model": "text-detector",
  "context": "来源：一篇匿名博客文章，2026-07-01。",
  "text": "待检测的文本。"
}
```

响应：`DetectionResponse`，`status` 为 `"queued"`（或 `"processing"`），
不含 `result`，返回任务 `id`，`modality: "text"`。轮询方式见 §5.4。

### 5.2 图像检测

```
POST /api/v1/detections/image
Content-Type: multipart/form-data   （不要手动设置该头，boundary 由浏览器生成）
```

表单字段：

| 字段      | 类型   | 必填 | 含义                          |
| --------- | ------ | ---- | ----------------------------- |
| `file`    | binary | 是   | 单张图片。                    |
| `model`   | string | 是   | 检测模型标识。                |
| `context` | string | 否   | 用户提供的补充信息。          |

响应：`DetectionResponse`，`status` 为 `"queued"`（或 `"processing"`），
不含 `result`，返回任务 `id`，`modality: "image"`。轮询方式见 §5.4。

### 5.3 视频检测

```
POST /api/v1/detections/video
Content-Type: multipart/form-data
```

表单字段：同图像检测（`file`、`model`、`context`）。

响应：`DetectionResponse`，`status` 为 `"queued"`（或 `"processing"`），
不含 `result`，返回任务 `id`，`modality: "video"`。轮询方式见 §5.4。

### 5.4 轮询任务

```
GET /api/v1/tasks/:id
```

返回任务当前快照。前端约每 2000 ms 轮询一次，
在状态变为 `completed` 或 `failed` 时停止。

完成示例：

```json
{
  "id": "det_x1f9c02",
  "modality": "text",
  "status": "completed",
  "progress": 100,
  "result": {
    "label": "ai_generated",
    "ai_probability": 0.91,
    "human_probability": 0.09,
    "confidence": "high",
    "reasoning": "句式结构统一、过渡词可预测、词汇变化度低，符合机器生成文本的特征。"
  },
  "model": { "name": "text-detector", "version": "1.0.0" }
}
```

失败示例：

```json
{
  "id": "det_x1f9c02",
  "modality": "video",
  "status": "failed",
  "error": { "code": "processing_error", "message": "The video could not be analyzed." }
}
```

## 6. HTTP 状态码

| 状态码 | 含义                                     |
| ------ | ---------------------------------------- |
| 200    | 成功（响应体见第 4 节）。                |
| 400    | 请求无效（如文本为空、`model` 未知）。   |
| 404    | 任务不存在。                             |
| 422    | 文件不支持 / 分析被拒绝。                |
| 500    | 服务器内部错误。                         |
| 503    | 服务不可用（无处理能力）。               |

## 7. 补充说明

- 前端文件校验仅用于体验优化，后端仍是真正的安全边界。
- 可选的未来流程（大文件直传）：`POST /api/v1/uploads` 获取直传地址，
  再以存储 key 创建检测任务。当前版本不要求实现。
- 后端需通过 CORS 允许前端来源的跨域请求。

## 8. 模型列表接口（便捷端点）

不属于基础契约，提供该端点便于前端动态发现部署方定义的模型标识，
而非硬编码模型名。

```
GET /api/v1/models
```

可选 query 参数 `modality` 用于按模态筛选：

| 参数       | 类型                  | 必填 | 含义                                   |
| ---------- | --------------------- | ---- | -------------------------------------- |
| `modality` | `text` \| `image` \| `video` | 否 | 仅返回该模态的模型。省略时返回全部。 |

示例：

```
GET /api/v1/models
GET /api/v1/models?modality=text
GET /api/v1/models?modality=image
GET /api/v1/models?modality=video
```

响应（未过滤）：

```json
{
  "models": [
    { "name": "text-detector", "version": "1.0.0", "modality": "text" },
    { "name": "image-detector", "version": "1.0.0", "modality": "image" },
    { "name": "video-detector", "version": "1.0.0", "modality": "video" }
  ]
}
```

过滤示例：`GET /api/v1/models?modality=text` 仅返回

```json
{ "models": [{ "name": "text-detector", "version": "1.0.0", "modality": "text" }] }
```

规则：

- `modality` 与检测端点对应：`text` / `image` / `video`。
- 传无效的 `modality` 值时返回 `400`，且 `error.code == "invalid_request"`。
- 向检测端点传递未知的 `model` 值时返回 `400`，且 `error.code == "invalid_model"`。