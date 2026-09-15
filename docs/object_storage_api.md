# Object Storage API

面向前端的对象存储文件保存/目录查询接口说明。

接口定义见 [server.py](/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py)。

## 1. 总览

当前新增两个接口：

- `POST /storage/save`
- `POST /storage/list`

这两个接口面向 MinIO 对象存储，不影响现有的：

- `POST /workspace/upload`
- `GET /workspace/download`

前端需要区分两套能力：

- `workspace` 接口：操作服务端本地工作区文件
- `storage` 接口：操作对象存储中的结果目录

## 2. 业务规则

### 2.1 桶名解析规则

后端会根据 `user_id` 自动解析桶名：

- 如果 `user_id` 包含下划线，例如 `aaa_bbb`，桶名取后半段 `bbb`
- 如果 `user_id` 不包含下划线，例如 `admin`，统一使用桶 `admin`

前端不需要自己计算桶名。

### 2.2 固定存储根目录

前端传入和看到的路径，都是相对于对象存储业务根目录的相对路径。

例如前端传：

```text
task1/result.json
```

后端实际保存到对象存储的对象 key 是：

```text
corpus/output/piflow/task1/result.json
```

前端不需要也不应该传这个固定前缀。

### 2.3 路径约束

前端传入的 `target_path` 和 `dir_path` 都必须是相对路径：

- 允许：`""`、`task1`、`task1/result.json`、`task1/subdir`
- 不允许：`../secret`、`/corpus/output/piflow/...`

## 3. 保存文件到对象存储

### 3.1 接口信息

- 方法：`POST`
- 路径：`/storage/save`
- Content-Type：`application/json`

### 3.2 请求体

```json
{
  "user_id": "aaa_bbb",
  "target_path": "task1/result.json",
  "local_path": "/outputs/result.json"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID，用于解析目标桶 |
| `target_path` | string | 是 | 桶内目标相对路径，不包含固定前缀 |
| `local_path` | string | 是 | 服务端本地文件路径 |

### 3.3 `local_path` 规则

`local_path` 表示服务端当前已经存在的本地文件，支持两种写法：

1. 工作区虚拟路径，例如：

```text
/outputs/result.json
```

或：

```text
outputs/result.json
```

2. 工作区内绝对路径，例如：

```text
/Users/renhao/PycharmProjects/flow-deepagents-0408/workspace/outputs/result.json
```

限制：

- 必须是服务端工作区内的文件
- 不允许越界到工作区外部
- 文件必须真实存在

### 3.4 成功响应

状态码：`200 OK`

```json
{
  "bucket": "bbb",
  "path": "task1/result.json",
  "object_key": "corpus/output/piflow/task1/result.json",
  "source_path": "/Users/renhao/PycharmProjects/flow-deepagents-0408/workspace/outputs/result.json",
  "size": 1024
}
```

字段说明：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `bucket` | string | 实际写入的桶名 |
| `path` | string | 业务相对路径 |
| `object_key` | string | 实际对象 key |
| `source_path` | string | 服务端本地源文件路径 |
| `size` | number | 文件字节数 |

### 3.5 失败响应

1. 参数非法

状态码：`400 Bad Request`

```json
{
  "detail": "target path is invalid"
}
```

或：

```json
{
  "detail": "path escapes workspace: /../secret.txt"
}
```

2. 本地文件不存在

状态码：`404 Not Found`

```json
{
  "detail": "local file not found"
}
```

3. 对象存储写入失败

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to save file to object storage"
}
```

### 3.6 curl 示例

```bash
curl -X POST "http://127.0.0.1:8080/storage/save" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "aaa_bbb",
    "target_path": "task1/result.json",
    "local_path": "/outputs/result.json"
  }'
```

### 3.7 前端 fetch 示例

```javascript
async function saveToObjectStorage(userId, targetPath, localPath) {
  const response = await fetch("/storage/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      target_path: targetPath,
      local_path: localPath,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Save to object storage failed");
  }

  return response.json();
}
```

## 4. 查询对象存储目录

### 4.1 接口信息

- 方法：`POST`
- 路径：`/storage/list`
- Content-Type：`application/json`

### 4.2 请求体

```json
{
  "user_id": "aaa_bbb",
  "dir_path": "task1"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID，用于解析目标桶 |
| `dir_path` | string | 是 | 要展示的目录相对路径，根目录传空字符串 `""` |

### 4.3 成功响应

状态码：`200 OK`

```json
{
  "bucket": "bbb",
  "dir_path": "task1",
  "items": [
    {
      "name": "result.json",
      "path": "task1/result.json",
      "type": "file",
      "size": 1024,
      "last_modified": "2026-06-11T08:00:00+00:00"
    },
    {
      "name": "subdir",
      "path": "task1/subdir",
      "type": "directory",
      "size": null,
      "last_modified": null
    }
  ]
}
```

字段说明：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `bucket` | string | 当前查询的桶名 |
| `dir_path` | string | 当前查询目录 |
| `items` | array | 当前层级的文件/目录列表 |

`items` 中每个元素字段如下：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 当前层级名称 |
| `path` | string | 供前端继续查询或展示的相对路径 |
| `type` | string | `file` 或 `directory` |
| `size` | number \| null | 文件大小，目录为 `null` |
| `last_modified` | string \| null | ISO 时间字符串，目录可能为 `null` |

### 4.4 返回规则

- 只返回当前层级内容
- 不递归整棵目录树
- 前端点开某个目录时，把该目录的 `path` 再作为 `dir_path` 传入即可

例如：

1. 查询根目录

```json
{
  "user_id": "admin",
  "dir_path": ""
}
```

2. 返回中看到目录：

```json
{
  "name": "task1",
  "path": "task1",
  "type": "directory"
}
```

3. 点击后再次查询：

```json
{
  "user_id": "admin",
  "dir_path": "task1"
}
```

### 4.5 失败响应

1. 参数非法

状态码：`400 Bad Request`

```json
{
  "detail": "dir_path is invalid"
}
```

2. 对象存储查询失败

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to list object storage directory"
}
```

### 4.6 curl 示例

```bash
curl -X POST "http://127.0.0.1:8080/storage/list" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "dir_path": ""
  }'
```

### 4.7 前端 fetch 示例

```javascript
async function listObjectStorageDir(userId, dirPath = "") {
  const response = await fetch("/storage/list", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      dir_path: dirPath,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "List object storage directory failed");
  }

  return response.json();
}
```

## 5. 推荐前端接入方式

建议前端按下面方式接入：

1. 当后端任务已经在 workspace 生成结果文件后，前端调用 `POST /storage/save`
2. `local_path` 传后端结果文件在 workspace 中的路径
3. `target_path` 传业务展示路径，例如 `task1/result.json`
4. 文件写入桶后，前端调用 `POST /storage/list` 获取当前目录列表
5. 用户点击目录时，把目录 `path` 再作为新的 `dir_path` 继续查询

## 6. 和 workspace 接口的关系

对象存储接口不会替代现有 workspace 接口：

- `workspace/upload`：上传输入文件到本地工作区
- `workspace/download`：从本地工作区下载结果文件
- `storage/save`：把本地工作区已有文件保存到对象存储
- `storage/list`：查询对象存储中的目录内容

如果前端需要“先运行任务，再把产物保存到对象存储”，通常流程是：

1. 上传文件到 workspace
2. 运行任务
3. 拿到任务生成的本地结果路径
4. 调用 `POST /storage/save`
5. 调用 `POST /storage/list` 刷新对象存储目录
