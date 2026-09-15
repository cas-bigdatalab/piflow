# Workspace 文件接口文档

本文档说明供前端使用的用户工作区文件接口：

- `POST /workspace/list`
- `POST /workspace/mkdir`
- `POST /workspace/file/delete`
- `POST /workspace/directory/delete`
- `POST /workspace/delete/batch`
- `POST /workspace/download/batch`
- `POST /workspace/upload/path`

这两个接口定义位于 [`/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py`](/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py)。

---

## 1. 列出用户目录

### 接口信息

- 方法：`POST`
- 路径：`/workspace/list`
- Content-Type：`application/json`

### 接口说明

根据 `user_id` 和相对目录，列出该目录下的所有文件和文件夹。

如果 `dir_path` 为空，则列出该用户根目录下的所有文件和文件夹。

分页参数是可选的：

- 不传 `page/page_size`：保持旧行为，返回当前目录全部 `items`
- 同时传入 `page/page_size`：返回分页后的 `items`，并额外返回 `pagination`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `user_id` | `string` | 是 | 用户 ID |
| `dir_path` | `string` | 否 | 用户工作区内的相对目录，默认 `""` |
| `page` | `number` | 否 | 页码，从 `1` 开始；需与 `page_size` 一起传 |
| `page_size` | `number` | 否 | 每页条数；需与 `page` 一起传 |

### `dir_path` 说明

支持以下写法：

- `""`：列出用户根目录
- `"/"`：列出用户根目录
- `"."`：列出用户根目录
- `"/outputs"`：列出用户目录下的 `outputs`
- `"/temp/chat_001"`：列出用户目录下的指定子目录

限制：

- 不允许使用 `..`
- 不允许越权访问其他用户目录
- 如果传入的是文件路径而不是目录，会返回错误

### 请求示例

```json
{
  "user_id": "alice",
  "dir_path": "/outputs",
  "page": 1,
  "page_size": 20
}
```

### 成功响应

不使用分页时，响应保持兼容旧版本：

```json
{
  "user_id": "alice",
  "dir_path": "/outputs",
  "items": [
    {
      "name": "reports",
      "path": "/outputs/reports",
      "type": "directory",
      "size": null,
      "last_modified": "2026-06-26T15:10:20.123456"
    },
    {
      "name": "result.csv",
      "path": "/outputs/result.csv",
      "type": "file",
      "size": 128,
      "last_modified": "2026-06-26T15:11:02.654321"
    }
  ]
}
```

使用分页时，会额外返回 `pagination`：

```json
{
  "user_id": "alice",
  "dir_path": "/outputs",
  "items": [
    {
      "name": "reports",
      "path": "/outputs/reports",
      "type": "directory",
      "size": null,
      "last_modified": "2026-06-26T15:10:20.123456"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 53,
    "total_pages": 3,
    "has_more": true
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|---|---|---|
| `user_id` | `string` | 用户 ID |
| `dir_path` | `string` | 当前实际列出的目录路径，用户工作区相对路径 |
| `items` | `array` | 当前目录下的文件和文件夹列表 |
| `pagination` | `object` | 仅在传入分页参数时返回 |

`items` 元素字段：

| 字段名 | 类型 | 说明 |
|---|---|---|
| `name` | `string` | 文件名或目录名 |
| `path` | `string` | 用户工作区内相对路径，统一以 `/` 开头 |
| `type` | `string` | `file` 或 `directory` |
| `size` | `number \| null` | 文件大小，目录为 `null` |
| `last_modified` | `string` | 最后修改时间，ISO 格式 |

### 排序规则

返回结果按以下规则排序：

1. 文件夹在前
2. 文件在后
3. 同类型按名称字母序排序

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | 路径非法或越权 |
| `400` | 指定路径不是目录 |
| `400` | `page`/`page_size` 未同时提供或值非法 |
| `404` | 目录不存在 |

### 前端调用示例

```ts
const res = await fetch("/workspace/list", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    user_id: "alice",
    dir_path: "/outputs",
    page: 1,
    page_size: 20
  })
});

const data = await res.json();
```

---

## 2. 创建目录

### 接口信息

- 方法：`POST`
- 路径：`/workspace/mkdir`
- Content-Type：`application/json`

### 接口说明

在指定用户工作区下创建目录；若目录已存在，则保持幂等成功。

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `user_id` | `string` | 是 | 用户 ID |
| `dir_path` | `string` | 是 | 要创建的目录路径，必须位于当前用户工作区内 |

### 请求示例

```json
{
  "user_id": "alice",
  "dir_path": "/outputs/reports"
}
```

### 成功响应

```json
{
  "user_id": "alice",
  "dir_path": "/outputs/reports"
}
```

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | 路径非法或越权 |
| `400` | 同名路径已存在但不是目录 |

---

## 3. 删除文件

### 接口信息

- 方法：`POST`
- 路径：`/workspace/file/delete`
- Content-Type：`application/json`

### 请求示例

```json
{
  "user_id": "alice",
  "path": "/outputs/result.csv"
}
```

### 成功响应

```json
{
  "user_id": "alice",
  "deleted": {
    "path": "/outputs/result.csv",
    "type": "file"
  }
}
```

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | 路径非法或越权 |
| `400` | 指定路径不是文件 |
| `404` | 路径不存在 |

---

## 4. 删除目录

### 接口信息

- 方法：`POST`
- 路径：`/workspace/directory/delete`
- Content-Type：`application/json`

### 接口说明

递归删除指定目录及其全部子文件、子目录。

### 请求示例

```json
{
  "user_id": "alice",
  "path": "/outputs/reports"
}
```

### 成功响应

```json
{
  "user_id": "alice",
  "deleted": {
    "path": "/outputs/reports",
    "type": "directory"
  }
}
```

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | 路径非法或越权 |
| `400` | 指定路径不是目录 |
| `404` | 路径不存在 |

---

## 5. 批量删除文件或目录

### 接口信息

- 方法：`POST`
- 路径：`/workspace/delete/batch`
- Content-Type：`application/json`

### 接口说明

支持一次提交多个路径，路径既可以是文件，也可以是目录。接口会逐项执行，返回成功项与失败项，不因单个失败而整体中断。

### 请求示例

```json
{
  "user_id": "alice",
  "paths": [
    "/outputs/result.csv",
    "/outputs/reports",
    "/outputs/not-found.txt"
  ]
}
```

### 成功响应

```json
{
  "user_id": "alice",
  "deleted": [
    {
      "path": "/outputs/result.csv",
      "type": "file"
    },
    {
      "path": "/outputs/reports",
      "type": "directory"
    }
  ],
  "failed": [
    {
      "path": "/outputs/not-found.txt",
      "status_code": 404,
      "detail": "path not found"
    }
  ]
}
```

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | `paths` 为空 |

---

## 6. 批量下载文件或目录

### 接口信息

- 方法：`POST`
- 路径：`/workspace/download/batch`
- Content-Type：`application/json`

### 接口说明

用于下载用户工作区中的文件或目录，下载根路径固定为：

```text
workspace/users/${user_id}
```

接口按以下规则处理：

- 传入单个文件：直接返回该文件
- 传入单个目录：将整个目录递归打包为 zip 后返回
- 传入多个路径：无论是文件、目录还是混合，统一打包为一个 zip 返回

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `user_id` | `string` | 是 | 用户 ID |
| `paths` | `string[]` | 是 | 要下载的路径列表，路径必须位于当前用户工作区内 |

### 请求示例

单文件下载：

```json
{
  "user_id": "alice",
  "paths": ["/outputs/result.csv"]
}
```

单目录下载：

```json
{
  "user_id": "alice",
  "paths": ["/outputs/reports"]
}
```

混合批量下载：

```json
{
  "user_id": "alice",
  "paths": [
    "/outputs/result.csv",
    "/outputs/reports",
    "/temp/a.txt"
  ]
}
```

### 成功响应

状态码：`200 OK`

响应体为文件二进制流：

- 单文件时：直接返回原文件
- 目录或多路径时：返回 `application/zip`

### 文件名规则

- 单文件：保持原文件名
- 单目录：使用目录名作为 zip 文件名，例如 `reports.zip`
- 多路径混合：使用 `workspace_batch_<id>.zip`

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | `paths` 为空 |
| `400` | 路径非法、越权或指向用户根目录 |
| `404` | 任一路径不存在 |

---

## 7. 按指定目录上传文件

### 接口信息

- 方法：`POST`
- 路径：`/workspace/upload/path`
- Content-Type：`multipart/form-data`

### 接口说明

根据 `user_id` 和指定相对目录上传文件。

文件会保存到指定目录下，文件名直接使用上传文件自己的文件名。

### 与 `/workspace/upload` 的区别

`/workspace/upload` 的保存规则是固定的：

```text
/temp/{safe_thread_id}/{safe_message_id}_{safe_name}
```

而 `/workspace/upload/path` 的保存规则是：

```text
{dir_path}/{上传文件原始文件名}
```

也就是说，这个接口：

- 不根据 `thread_id`、`message_id` 自动规划目录
- 不自动在文件名前拼接消息 ID
- 直接按指定目录保存
- 文件名就是上传文件名本身

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `user_id` | `string` | 是 | 用户 ID |
| `dir_path` | `string` | 否 | 用户工作区内目标目录，默认 `""` |
| `file` | `file` | 是 | 上传文件 |

### `dir_path` 说明

支持以下写法：

- `""`：上传到用户根目录
- `"/"`：上传到用户根目录
- `"."`：上传到用户根目录
- `"/outputs"`：上传到用户目录下的 `outputs`
- `"/outputs/reports"`：上传到指定子目录

限制：

- 不允许使用 `..`
- 不允许越权访问其他用户目录
- 如果目标目录不存在，服务端会自动创建

### 请求示例

```bash
curl -X POST "http://127.0.0.1:8080/workspace/upload/path" \
  -F "user_id=alice" \
  -F "dir_path=/outputs/reports" \
  -F "file=@./report.csv"
```

### 成功响应

```json
{
  "user_id": "alice",
  "dir_path": "/outputs/reports",
  "path": "/outputs/reports/report.csv",
  "original_filename": "report.csv",
  "size": 128,
  "content_type": "text/csv"
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|---|---|---|
| `user_id` | `string` | 用户 ID |
| `dir_path` | `string` | 请求传入的目标目录 |
| `path` | `string` | 实际保存后的用户相对路径 |
| `original_filename` | `string` | 上传文件原始名称 |
| `size` | `number` | 文件大小，单位字节 |
| `content_type` | `string \| null` | 上传文件 MIME 类型 |

### 保存行为说明

- 若目标目录不存在，服务端会自动创建目录
- 文件名直接使用上传文件原始文件名
- 若目标位置已有同名文件，当前实现会直接覆盖
- 文件保存范围限制在当前用户工作区内

### 错误响应

| HTTP 状态码 | 说明 |
|---|---|
| `400` | `user_id` 为空 |
| `400` | 上传文件名为空 |
| `400` | 路径非法或越权 |
| `400` | 文件路径超出用户工作区 |

### 前端调用示例

```ts
const form = new FormData();
form.append("user_id", "alice");
form.append("dir_path", "/outputs/reports");
form.append("file", file);

const res = await fetch("/workspace/upload/path", {
  method: "POST",
  body: form
});

const data = await res.json();
```

---

## 8. 前端接入建议

### 列目录

- 页面初始化时可调用 `/workspace/list`
- `dir_path` 为空时展示用户根目录
- 点击文件夹后，将其 `path` 作为新的 `dir_path` 再次请求
- 目录内容很多时，可传 `page/page_size` 启用分页；旧页面不改也能继续使用

### 上传文件

- 上传到当前目录时，将当前目录的 `path` 作为 `dir_path`
- 上传完成后，使用返回的 `path` 更新文件列表或重新请求当前目录

### 目录与删除

- 新建目录时调用 `/workspace/mkdir`
- 删除单个文件时调用 `/workspace/file/delete`
- 删除单个目录时调用 `/workspace/directory/delete`
- 多选批量删除时调用 `/workspace/delete/batch`

### 下载

- 单文件下载也可以统一走 `/workspace/download/batch`
- 下载单个目录时，将目录路径作为 `paths` 中唯一元素传入
- 多选下载时，将选中的文件和目录路径统一放入 `paths`

### 推荐约定

- 前端统一使用接口返回的 `path`
- 不要自行拼接路径字符串
- 所有目录跳转、文件下载、上传目标目录，都以服务端返回值为准

---

## 9. 示例流程

### 1. 获取根目录

请求：

```json
{
  "user_id": "alice",
  "dir_path": ""
}
```

### 2. 进入 `/outputs/reports`

请求：

```json
{
  "user_id": "alice",
  "dir_path": "/outputs/reports"
}
```

### 3. 上传 `report.csv` 到 `/outputs/reports`

表单字段：

```text
user_id=alice
dir_path=/outputs/reports
file=report.csv
```

成功后返回：

```json
{
  "user_id": "alice",
  "dir_path": "/outputs/reports",
  "path": "/outputs/reports/report.csv",
  "original_filename": "report.csv",
  "size": 128,
  "content_type": "text/csv"
}
```

---

## 10. 简版接口定义

### `POST /workspace/list`

请求：

```json
{
  "user_id": "string",
  "dir_path": "string",
  "page": 1,
  "page_size": 20
}
```

响应：

```json
{
  "user_id": "string",
  "dir_path": "string",
  "items": [
    {
      "name": "string",
      "path": "string",
      "type": "file | directory",
      "size": 0,
      "last_modified": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0,
    "has_more": false
  }
}
```

### `POST /workspace/mkdir`

请求：

```json
{
  "user_id": "string",
  "dir_path": "string"
}
```

### `POST /workspace/file/delete`

请求：

```json
{
  "user_id": "string",
  "path": "string"
}
```

### `POST /workspace/directory/delete`

请求：

```json
{
  "user_id": "string",
  "path": "string"
}
```

### `POST /workspace/delete/batch`

请求：

```json
{
  "user_id": "string",
  "paths": ["string"]
}
```

### `POST /workspace/download/batch`

请求：

```json
{
  "user_id": "string",
  "paths": ["string"]
}
```

### `POST /workspace/upload/path`

表单：

```text
user_id: string
dir_path: string
file: binary
```

响应：

```json
{
  "user_id": "string",
  "dir_path": "string",
  "path": "string",
  "original_filename": "string",
  "size": 0,
  "content_type": "string"
}
```
