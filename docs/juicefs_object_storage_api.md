# JuiceFS Object Storage API

## 1. 统一规则

- `user_id` 继续按下划线切桶：`aaa_bbb -> bucket=bbb`
- 不带下划线时使用 `admin`
- 若桶不存在，后端自动创建
- 实际对象前缀固定为：`corpus/{bucket}/corpus/output/piflow/`
- `target_path`、`dir_path` 只传相对路径，不包含固定前缀

---

## 2. 文件推送

### 接口

- `POST /storage/juicefs/save`

### 请求体

```json
{
  "user_id": "aaa_bbb",
  "target_path": "task1/result.json",
  "local_path": "/outputs/result.json"
}
```

### 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `target_path` | string | 是 | 目标相对路径 |
| `local_path` | string | 是 | 服务端本地文件路径 |

### 成功响应

```json
{
  "code": 200,
  "result": {
    "user_id": "aaa_bbb",
    "desktop_id": "aaa_bbb",
    "path": "task1/result.json",
    "object_key": "corpus/bbb/corpus/output/piflow/task1/result.json",
    "source_path": "/Users/renhao/PycharmProjects/flow-deepagents-0408/workspace/users/aaa_bbb/outputs/result.json",
    "size": 1024
  }
}
```

### 说明

- 如果 `bbb` 桶不存在，会自动创建
- `object_key` 由后端拼接，不需要前端传入

---

## 3. 获取文件列表

### 接口

- `POST /storage/juicefs/list`

### 请求体

```json
{
  "user_id": "aaa_bbb",
  "dir_path": "task1"
}
```

### 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `dir_path` | string | 是 | 查询目录，相对路径，根目录传 `""` |

### 成功响应

```json
{
  "code": 200,
  "result": {
    "user_id": "aaa_bbb",
    "desktop_id": "aaa_bbb",
    "dir_path": "task1",
    "prefix": "corpus/bbb/corpus/output/piflow/task1/",
    "items": [
      {
        "name": "result.json",
        "path": "task1/result.json",
        "type": "file",
        "size": 1024,
        "last_modified": "2026-07-21T10:00:00+08:00"
      }
    ]
  }
}
```

### 说明

- 如果 `bbb` 桶不存在，会自动创建
- 只返回当前层级内容

---

## 4. 创建文件夹

### 接口

- `POST /storage/juicefs/mkdir`

### 请求体

```json
{
  "user_id": "aaa_bbb",
  "dir_path": "task1/subdir"
}
```

### 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `dir_path` | string | 是 | 要创建的相对目录 |

### 成功响应

```json
{
  "code": 200,
  "result": {
    "user_id": "aaa_bbb",
    "desktop_id": "aaa_bbb",
    "dir_path": "task1/subdir",
    "object_key": "corpus/bbb/corpus/output/piflow/task1/subdir/",
    "created": true
  }
}
```

### 说明

- 如果 `bbb` 桶不存在，会自动创建
- 目录通过空对象占位实现

---

## 5. 错误码

- `400`：参数非法、路径为空、路径越界
- `404`：`save` 时本地文件不存在
- `500`：S3 网关写入/查询失败
