# API Contract

This document lets a backend developer implement a compliant detection
service for this frontend, without reading frontend code.

---

## 1. Base URL

- Frontend reads `NEXT_PUBLIC_API_BASE_URL` (e.g. `http://localhost:8000`).
- All endpoints are under the prefix `/api/v1`.
- Full URL: `{NEXT_PUBLIC_API_BASE_URL}/api/v1/<endpoint>`.

## 2. Request model

Every detection request includes:

| Field     | Type   | Required | Meaning                                                         |
| --------- | ------ | -------- | --------------------------------------------------------------- |
| `model`   | string | yes      | Identifier of the detection model to use (user-selected).       |
| `context` | string | no       | User-supplied supplementary info (e.g. source, background).     |
| content   | varies | yes      | The content to detect: `text` field or `file` field (see §4).   |

Note: `model` values are deployment-defined identifiers. Examples:
`"text-detector"`, `"image-detector"`, `"video-detector"`.

## 3. Common rules

- Text detection: send/receive `application/json`.
- Image/video detection: send `multipart/form-data` with fields
  `file`, `model`, `context`.
- JSON responses must set `Content-Type: application/json`.
- Non-2xx error body:

```json
{ "error": { "code": "invalid_text", "message": "user-friendly English message" } }
```

  `code` is optional; `message` is required. Never include stack traces.

## 4. Detection response model

Every detection endpoint returns this shape. The frontend treats it as the
contract and does not adapt backend field names, so **field names must match
exactly**.

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
    "reasoning": "A short explanation of why the model reached this conclusion."
  },
  "model": { "name": "string", "version": "string" },
  "error": { "code": "string", "message": "string" }
}
```

Rules:

- `id`, `modality`, `status` are required.
- `progress` (0–100): optional; never fabricate intermediate values.
  It is omitted while `queued` / `processing` and is `100` once `completed`.
- `result` present only when `status == "completed"`.
- `result.reasoning`: required, a short human-readable explanation
  (interpretability) tied to the result.
- `error` present only when `status == "failed"`.
- Terminal statuses: `completed` and `failed`.
- `ai_probability` / `human_probability` are in range 0–1.
- `confidence` is the model's self-assessed certainty.
- `uncertain` is used when the model cannot decide.

## 5. Task-based detection (all modalities)

All detection is task-based: submit content, then poll for the result.
The backend assigns the task `id`; clients do **not** manage tasks (there is
no list / cancel / delete API). From the end user's perspective this is simply
a wait — submit, then wait for the result — behaving like a synchronous
request that takes some seconds because model inference is compute-heavy.

```
POST /api/v1/detections/text    (JSON body:   model, context?, text)
POST /api/v1/detections/image   (multipart:   file, model, context?)
POST /api/v1/detections/video   (multipart:   file, model, context?)
```

Request validation errors (`400` / `413` / `422`) are still returned
immediately by the create call. On success (`200`) each create call returns a
non-terminal `DetectionResponse`:

```json
{
  "id": "det_x1f9c02",
  "modality": "text",
  "status": "queued",
  "model": { "name": "text-detector", "version": "1.0.0" }
}
```

Then poll for the result:

```
GET /api/v1/tasks/:id
```

The frontend polls every ~2000 ms and stops when `status` becomes
`completed` or `failed`. `progress` is omitted while `queued`/`processing`
and is `100` once `completed`.

### 5.1 Text detection

```
POST /api/v1/detections/text
Content-Type: application/json
```

```json
{
  "model": "text-detector",
  "context": "Source: an anonymous blog post, 2026-07-01.",
  "text": "The text to analyze."
}
```

Response: `DetectionResponse` with `status: "queued"` (or `"processing"`),
no `result`, the task `id`, and `modality: "text"`. See §5.4 for polling.

### 5.2 Image detection

```
POST /api/v1/detections/image
Content-Type: multipart/form-data   (do not set this header; the browser sets the boundary)
```

Form fields:

| Field     | Type   | Required | Meaning                        |
| --------- | ------ | -------- | ------------------------------ |
| `file`    | binary | yes      | One image.                     |
| `model`   | string | yes      | Detection model identifier.    |
| `context` | string | no       | User-supplied supplementary info. |

Response: `DetectionResponse` with `status: "queued"` (or `"processing"`),
no `result`, the task `id`, and `modality: "image"`. See §5.4 for polling.

### 5.3 Video detection

```
POST /api/v1/detections/video
Content-Type: multipart/form-data
```

Form fields: same as image (`file`, `model`, `context`).

Response: `DetectionResponse` with `status: "queued"` (or `"processing"`),
no `result`, the task `id`, and `modality: "video"`. See §5.4 for polling.

### 5.4 Polling a task

```
GET /api/v1/tasks/:id
```

Returns the current snapshot of the task. The frontend polls every ~2000 ms
and stops when status is `completed` or `failed`.

Completed example:

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
    "reasoning": "Uniform sentence structure, predictable transitions, and low lexical variation are consistent with machine-generated writing."
  },
  "model": { "name": "text-detector", "version": "1.0.0" }
}
```

Failed example:

```json
{
  "id": "det_x1f9c02",
  "modality": "video",
  "status": "failed",
  "error": { "code": "processing_error", "message": "The video could not be analyzed." }
}
```

## 6. HTTP status codes

| Code | Meaning                                  |
| ---- | ---------------------------------------- |
| 200  | Success (task body per §4).              |
| 400  | Invalid request (e.g. empty text, unknown `model`). |
| 404  | Task not found.                          |
| 422  | Unsupported file / analysis rejected.    |
| 500  | Internal error.                          |
| 503  | Service unavailable (no capacity).       |

## 7. Additional notes

- Client-side file validation is UX-only; the backend remains the real
  validator.
- Optional future flow for large files: direct upload to object storage via
  `POST /api/v1/uploads`, then create a task with a storage key. Not required
  for the current version.
- Backend must allow the frontend origin via CORS.

## 8. Model catalog (convenience endpoint)

Not part of the base contract; provided so the frontend can discover the
deployment-defined model identifiers instead of hard-coding them.

```
GET /api/v1/models
```

Optional query parameter `modality` filters the list for a single modality:

| Parameter | Type | Required | Meaning |
| --------- | ---- | -------- | ------- |
| `modality` | `text` \| `image` \| `video` | no | Only return models for this modality. Omit to list all. |

Examples:

```
GET /api/v1/models
GET /api/v1/models?modality=text
GET /api/v1/models?modality=image
GET /api/v1/models?modality=video
```

Response (unfiltered):

```json
{
  "models": [
    { "name": "text-detector", "version": "1.0.0", "modality": "text" },
    { "name": "image-detector", "version": "1.0.0", "modality": "image" },
    { "name": "video-detector", "version": "1.0.0", "modality": "video" }
  ]
}
```

Example (filtered): `GET /api/v1/models?modality=text` returns only

```json
{ "models": [{ "name": "text-detector", "version": "1.0.0", "modality": "text" }] }
```

Rules:

- `modality` maps to the detection endpoints: `text` / `image` / `video`.
- An invalid `modality` value returns `400` with
  `error.code == "invalid_request"`.
- Unknown `model` values sent to a detection endpoint return `400` with
  `error.code == "invalid_model"`.