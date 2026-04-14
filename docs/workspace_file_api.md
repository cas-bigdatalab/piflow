# Workspace File API

面向前端的工作区文件上传/下载接口说明。

接口定义见 [api/server.py](/Users/renhao/PycharmProjects/flow-deepagents-0408/api/server.py)。

## 1. 总览

当前提供两个接口：

- `POST /workspace/upload`
- `GET /workspace/download`

这两个接口都操作服务端的工作区目录。允许访问的顶层目录只有：

- `/temp`
- `/outputs`
- `/artifacts`
- `/logs`

前端通常这样使用：

1. 用户选择或拖拽文件
2. 前端调用 `POST /workspace/upload`
3. 后端返回工作区虚拟路径，例如 `/temp/data.csv`
4. 后续聊天请求里携带这个路径，供 Agent/Skill 使用
5. 如果后端生成了结果文件，前端用 `GET /workspace/download?path=/outputs/result.csv` 下载

## 2. 上传接口

### 2.1 接口信息

- 方法：`POST`
- 路径：`/workspace/upload`
- Content-Type：`multipart/form-data`

### 2.2 表单字段

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | File | 是 | 要上传的文件 |
| `target_dir` | string | 否 | 上传到工作区哪个顶层目录，默认 `temp` |
| `filename` | string | 否 | 服务端保存文件名，默认使用上传文件原名 |

### 2.3 允许的 `target_dir`

- `temp`
- `outputs`
- `artifacts`
- `logs`

不允许上传到其他目录，例如 `skills`、`../temp`。

### 2.4 成功响应

状态码：`200 OK`

```json
{
  "path": "/temp/sample.csv",
  "filename": "sample.csv",
  "size": 1024,
  "content_type": "text/csv"
}
```

字段说明：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `path` | string | 文件在工作区内的虚拟路径，后续可直接传给聊天接口或下载接口 |
| `filename` | string | 最终保存的文件名 |
| `size` | number | 文件字节数 |
| `content_type` | string \| null | 浏览器上传时携带的 MIME 类型 |

### 2.5 失败响应

状态码：`400 Bad Request`

典型场景：

1. 文件名为空

```json
{
  "detail": "filename is required"
}
```

2. 目录非法

```json
{
  "detail": "top-level workspace dir must be one of: ['artifacts', 'logs', 'outputs', 'temp']"
}
```

3. 路径逃逸工作区

```json
{
  "detail": "path escapes workspace: /../secret.txt"
}
```

### 2.6 curl 示例

```bash
curl -X POST "http://127.0.0.1:8080/workspace/upload" \
  -F "file=@/local/path/data.csv" \
  -F "target_dir=temp"
```

指定保存名：

```bash
curl -X POST "http://127.0.0.1:8080/workspace/upload" \
  -F "file=@/local/path/data.csv" \
  -F "target_dir=outputs" \
  -F "filename=result.csv"
```

### 2.7 前端 fetch 示例

```javascript
async function uploadWorkspaceFile(file, targetDir = "temp", filename = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_dir", targetDir);
  if (filename) {
    formData.append("filename", filename);
  }

  const response = await fetch("/workspace/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}
```

拖拽上传示例：

```javascript
async function handleDrop(event) {
  event.preventDefault();
  const files = Array.from(event.dataTransfer.files || []);
  const uploaded = [];

  for (const file of files) {
    const result = await uploadWorkspaceFile(file, "temp");
    uploaded.push(result);
  }

  return uploaded;
}
```

## 3. 下载接口

### 3.1 接口信息

- 方法：`GET`
- 路径：`/workspace/download`
- Query 参数：`path`

### 3.2 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `path` | string | 是 | 工作区虚拟路径，例如 `/outputs/report.csv` |

### 3.3 成功响应

状态码：`200 OK`

返回文件二进制流，响应头中包含：

- `Content-Disposition: attachment; filename="xxx.ext"`
- `Content-Type: application/octet-stream`

### 3.4 失败响应

1. 参数非法或路径越界

状态码：`400 Bad Request`

```json
{
  "detail": "path escapes workspace: /../secret.txt"
}
```

或：

```json
{
  "detail": "top-level workspace dir must be one of: ['artifacts', 'logs', 'outputs', 'temp']"
}
```

2. 文件不存在

状态码：`404 Not Found`

```json
{
  "detail": "file not found"
}
```

### 3.5 curl 示例

```bash
curl -L "http://127.0.0.1:8080/workspace/download?path=/outputs/result.csv" -o result.csv
```

### 3.6 前端 fetch 示例

```javascript
async function downloadWorkspaceFile(path) {
  const response = await fetch(
    `/workspace/download?path=${encodeURIComponent(path)}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Download failed");
  }

  const blob = await response.blob();
  const fileName = path.split("/").pop() || "download.bin";
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
```

## 4. 推荐前端接入流程

### 4.1 用户上传输入文件

前端调用：

```text
POST /workspace/upload
```

后端返回：

```json
{
  "path": "/temp/forest.csv",
  "filename": "forest.csv",
  "size": 20480,
  "content_type": "text/csv"
}
```

前端应保存这个 `path`。

### 4.2 发送聊天消息

建议前端把上传结果里的 `path` 一并传给聊天接口。当前仓库里的 `/chat` 还没有 `files` 字段，如果后续扩展，建议格式如下：

```json
{
  "message": "请处理这个 CSV 文件",
  "thread_id": "thread-001",
  "user_id": "user-001",
  "files": [
    "/temp/forest.csv"
  ]
}
```

### 4.3 下载结果文件

如果后端返回结果文件路径，例如：

```json
{
  "files": [
    "/outputs/final_result.csv"
  ]
}
```

前端直接调用：

```text
GET /workspace/download?path=/outputs/final_result.csv
```

## 5. 注意事项

1. 不要让前端自行拼接本地磁盘绝对路径，只使用工作区虚拟路径。
2. 上传后的文件建议默认放 `/temp`。
3. 最终给用户下载的结果文件建议放 `/outputs`。
4. 前端下载时必须对 `path` 做 `encodeURIComponent`。
5. 如果前端要支持多文件拖拽，建议逐个上传，再把返回的多个 `path` 一起传给聊天接口。
