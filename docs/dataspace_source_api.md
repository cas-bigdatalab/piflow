# Dataspace Source API

面向前端的 Dataspace 数据源类型展示、数据源创建、更新、删除、校验、详情查询和目录浏览接口说明。

接口定义见 [server.py](/Users/renhao/PycharmProjects/flow-deepagents-0408/server.py)。

## 1. 总览

当前提供 9 个接口：

- `POST /datasource/catalog/list`
- `POST /datasource/catalog/detail`

- `POST /dataspace/source/create`
- `POST /dataspace/source/update`
- `POST /dataspace/source/delete`
- `POST /dataspace/source/list`
- `POST /dataspace/source/detail`
- `POST /dataspace/source/directory/list`
- `POST /dataspace/source/validate`

## 2. 业务规则

### 2.1 数据源类型目录说明

当前系统内置且仅内置一种可用数据源类型：

- `dataspace` / `DataSpace`

前端应先通过数据源类型目录接口获取“当前支持哪些数据源类型”以及“添加该类型时需要填写哪些字段”，再决定是否进入具体的数据源实例创建流程。

### 2.2 前端输入字段

前端初始化 Dataspace 数据源时，只需要填写这些字段：

- `base_url`
- `app_id`
- `auth_code`
- `space_name`
- `ftp_user`
- `ftp_password`
- `logo`（可选）

### 2.3 后端自动补全字段

后端会在创建或校验时自动补全：

- `space_id`
- `ftp_link`
- `webdav_link`
- `root_path`

其中：

- `space_id`：通过 Dataspace 开放接口自动解析
- `root_path`：优先从 `ftpLink` 提取，例如 `ftp://10.0.90.47/ITOrktzbo184` 会得到 `/ITOrktzbo184`

### 2.4 logo 规则

- 如果前端传入了 `logo`，优先使用前端值
- 如果前端未传 `logo` 或为空，自动回退到 `spaceInfo.spaceLogo`

### 2.5 敏感字段返回规则

后端不会把以下字段原样返回前端：

- `auth_code`
- `ftp_password`

接口响应中只返回：

- `auth_code_masked`
- `ftp_password_masked`

### 2.6 validate 与 create 的区别

- `create`：校验通过后会入库，生成 `source_id`
- `validate`：只做校验，不入库，不产生数据源实例

## 3. 查询可用数据源类型列表

### 3.1 接口信息

- 方法：`POST`
- 路径：`/datasource/catalog/list`
- Content-Type：`application/json`

### 3.2 请求体

当前接口无需请求体。

前端可以发送空对象：

```json
{}
```

### 3.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "items": [
      {
        "type_code": "dataspace",
        "type_name": "DataSpace",
        "category": "file",
        "description": "Dataspace 数据空间类型，用于访问空间目录并进行文件下载与上传。",
        "logo": "",
        "enabled": true,
        "sort_order": 1,
        "capabilities": [
          "list",
          "download",
          "upload"
        ],
        "init_fields": [
          {
            "name": "name",
            "label": "数据源名称",
            "type": "string",
            "required": true,
            "default": "",
            "placeholder": "请输入数据源实例名称",
            "secret": false,
            "options": [],
            "description": "用于区分不同 Dataspace 数据源实例的自定义名称"
          },
          {
            "name": "base_url",
            "label": "服务地址",
            "type": "string",
            "required": true,
            "default": "",
            "placeholder": "请输入 Dataspace 服务地址",
            "secret": false,
            "options": [],
            "description": "Dataspace 开放接口服务地址"
          },
          {
            "name": "app_id",
            "label": "应用ID",
            "type": "string",
            "required": true,
            "default": "",
            "placeholder": "请输入应用ID",
            "secret": false,
            "options": [],
            "description": "Dataspace 开放接口应用ID"
          }
        ],
        "extra_meta": {
          "builtin": true,
          "instance_api_prefix": "/dataspace/source",
          "supports_validation": true
        },
        "created_at": "2026-07-27T10:00:00+08:00",
        "updated_at": "2026-07-27T10:00:00+08:00"
      }
    ]
  }
}
```

说明：

- 当前列表只会返回系统已启用且可用的数据源类型
- 现阶段仅内置 `DataSpace` 一种类型
- `init_fields` 用于前端动态生成“添加数据源”表单

### 3.4 失败响应

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to list datasource catalog"
}
```

## 4. 查询单个数据源类型详情

### 4.1 接口信息

- 方法：`POST`
- 路径：`/datasource/catalog/detail`
- Content-Type：`application/json`

### 4.2 请求体

```json
{
  "type_code": "dataspace"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type_code` | string | 是 | 数据源类型编码，当前固定为 `dataspace` |

### 4.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "catalog": {
      "type_code": "dataspace",
      "type_name": "DataSpace",
      "category": "file",
      "description": "Dataspace 数据空间类型，用于访问空间目录并进行文件下载与上传。",
      "logo": "",
      "enabled": true,
      "sort_order": 1,
      "capabilities": [
        "list",
        "download",
        "upload"
      ],
      "init_fields": [
        {
          "name": "name",
          "label": "数据源名称",
          "type": "string",
          "required": true,
          "default": "",
          "placeholder": "请输入数据源实例名称",
          "secret": false,
          "options": [],
          "description": "用于区分不同 Dataspace 数据源实例的自定义名称"
        },
        {
          "name": "base_url",
          "label": "服务地址",
          "type": "string",
          "required": true,
          "default": "",
          "placeholder": "请输入 Dataspace 服务地址",
          "secret": false,
          "options": [],
          "description": "Dataspace 开放接口服务地址"
        },
        {
          "name": "app_id",
          "label": "应用ID",
          "type": "string",
          "required": true,
          "default": "",
          "placeholder": "请输入应用ID",
          "secret": false,
          "options": [],
          "description": "Dataspace 开放接口应用ID"
        },
        {
          "name": "auth_code",
          "label": "授权码",
          "type": "password",
          "required": true,
          "default": "",
          "placeholder": "请输入授权码",
          "secret": true,
          "options": [],
          "description": "Dataspace 开放接口授权码"
        },
        {
          "name": "space_name",
          "label": "数据空间名称",
          "type": "string",
          "required": true,
          "default": "",
          "placeholder": "请输入数据空间名称",
          "secret": false,
          "options": [],
          "description": "系统将根据空间名称自动解析 space_id"
        },
        {
          "name": "ftp_user",
          "label": "FTP用户名",
          "type": "string",
          "required": true,
          "default": "",
          "placeholder": "请输入FTP用户名",
          "secret": false,
          "options": [],
          "description": "用于访问 Dataspace FTP 目录"
        },
        {
          "name": "ftp_password",
          "label": "FTP密码",
          "type": "password",
          "required": true,
          "default": "",
          "placeholder": "请输入FTP密码",
          "secret": true,
          "options": [],
          "description": "用于访问 Dataspace FTP 目录"
        },
        {
          "name": "logo",
          "label": "Logo",
          "type": "string",
          "required": false,
          "default": "",
          "placeholder": "可选，未填写时默认使用空间Logo",
          "secret": false,
          "options": [],
          "description": "可选的 Base64 Logo 字符串"
        }
      ],
      "extra_meta": {
        "builtin": true,
        "instance_api_prefix": "/dataspace/source",
        "supports_validation": true
      },
      "created_at": "2026-07-27T10:00:00+08:00",
      "updated_at": "2026-07-27T10:00:00+08:00"
    }
  }
}
```

### 4.4 失败响应

1. 类型不存在

状态码：`404 Not Found`

```json
{
  "detail": "datasource catalog not found: xxx"
}
```

2. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to get datasource catalog detail"
}
```

## 5. 创建 Dataspace 数据源

### 5.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/create`
- Content-Type：`application/json`

### 5.2 请求体

```json
{
  "name": "测试空间实例",
  "base_url": "https://10.0.90.47",
  "app_id": "614646",
  "auth_code": "ZGNkMWRlMjVhZjg4NDY4OTk0MmY0MDUwNzA1NGM3ZDU=",
  "space_name": "空间导入相关任务优化测试空间",
  "ftp_user": "15117913512@126.com",
  "ftp_password": "Cc289836256&",
  "logo": ""
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 数据源实例名称，允许用户自定义 |
| `base_url` | string | 是 | Dataspace 服务地址 |
| `app_id` | string | 是 | Dataspace 应用 ID |
| `auth_code` | string | 是 | Dataspace 授权码 |
| `space_name` | string | 是 | 空间名称 |
| `ftp_user` | string | 是 | FTP 用户名 |
| `ftp_password` | string | 是 | FTP 密码 |
| `logo` | string | 否 | Base64 图片字符串；为空时自动回退到 `spaceInfo.spaceLogo` |

### 5.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "source": {
      "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
      "name": "测试空间实例",
      "base_url": "https://10.0.90.47",
      "app_id": "614646",
      "auth_code_masked": "ZGN***U=",
      "space_name": "空间导入相关任务优化测试空间",
      "space_id": "2073250022174072832",
      "ftp_user": "15117913512@126.com",
      "ftp_password_masked": "Cc2***6&",
      "ftp_link": "ftp://10.0.90.47/ITOrktzbo184",
      "webdav_link": "http://10.0.90.47/webDAV/ITOrktzbo184",
      "root_path": "/ITOrktzbo184",
      "logo": "data:image/png;base64,...",
      "created_at": "2026-07-23T16:00:00+08:00",
      "updated_at": "2026-07-23T16:00:00+08:00"
    }
  }
}
```

### 5.4 失败响应

1. 参数错误、空间解析失败、FTP 校验失败

状态码：`400 Bad Request`

```json
{
  "detail": "space not found by name: xxx"
}
```

2. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to create dataspace source"
}
```

## 6. 更新 Dataspace 数据源

### 6.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/update`
- Content-Type：`application/json`

### 6.2 请求体

更新请求需要携带已有的 `source_id`，其余字段与创建接口一致：

```json
{
  "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
  "name": "测试空间实例",
  "base_url": "https://10.0.90.47",
  "app_id": "614646",
  "auth_code": "ZGNkMWRlMjVhZjg4NDY4OTk0MmY0MDUwNzA1NGM3ZDU=",
  "space_name": "空间导入相关任务优化测试空间",
  "ftp_user": "15117913512@126.com",
  "ftp_password": "Cc289836256&",
  "logo": ""
}
```

更新前后端会重新校验 Dataspace 接口、空间信息和 FTP 连接，并刷新后端自动补全的 `space_id`、`ftp_link`、`webdav_link`、`root_path` 和 `logo` 字段。

### 6.3 成功响应

成功响应格式与创建接口一致，返回更新后的数据源实例：

```json
{
  "code": 200,
  "result": {
    "source": {
      "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
      "name": "测试空间实例",
      "space_name": "空间导入相关任务优化测试空间",
      "space_id": "2073250022174072832",
      "updated_at": "2026-07-27T10:00:00+08:00"
    }
  }
}
```

### 6.4 失败响应

- 参数错误、空间解析失败或 FTP 校验失败：`400 Bad Request`
- 数据源不存在：`404 Not Found`
- 服务内部异常：`500 Internal Server Error`

```json
{
  "detail": "dataspace source not found: xxx"
}
```

## 7. 删除 Dataspace 数据源

### 7.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/delete`
- Content-Type：`application/json`

### 7.2 请求体

```json
{
  "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11"
}
```

### 7.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11"
  }
}
```

删除只移除数据源实例注册信息，不删除 Dataspace 远端空间或其中的文件。

### 7.4 失败响应

- 数据源不存在：`404 Not Found`
- 服务内部异常：`500 Internal Server Error`

```json
{
  "detail": "dataspace source not found: xxx"
}
```

## 8. 查询 Dataspace 数据源列表

### 6.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/list`
- Content-Type：`application/json`

### 6.2 请求体

当前接口无需请求体。

前端可以发送空对象：

```json
{}
```

### 6.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "items": [
      {
        "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
        "name": "测试空间实例",
        "base_url": "https://10.0.90.47",
        "database_name": "空间导入相关任务优化测试空间",
        "logo": "data:image/png;base64,...",
        "created_at": "2026-07-23T16:00:00+08:00",
        "updated_at": "2026-07-23T16:00:00+08:00",
        "type_code": "dataspace"
      }
    ]
  }
}
```

### 6.4 失败响应

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to list dataspace sources"
}
```

## 9. 查询 Dataspace 数据源详情

### 7.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/detail`
- Content-Type：`application/json`

### 7.2 请求体

```json
{
  "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_id` | string | 是 | Dataspace 数据源实例 ID |

### 7.3 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "source": {
      "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
      "name": "测试空间实例",
      "base_url": "https://10.0.90.47",
      "app_id": "614646",
      "auth_code_masked": "ZGN***U=",
      "space_name": "空间导入相关任务优化测试空间",
      "space_id": "2073250022174072832",
      "ftp_user": "15117913512@126.com",
      "ftp_password_masked": "Cc2***6&",
      "ftp_link": "ftp://10.0.90.47/ITOrktzbo184",
      "webdav_link": "http://10.0.90.47/webDAV/ITOrktzbo184",
      "root_path": "/ITOrktzbo184",
      "logo": "data:image/png;base64,...",
      "created_at": "2026-07-23T16:00:00+08:00",
      "updated_at": "2026-07-23T16:00:00+08:00"
    }
  }
}
```

### 7.4 失败响应

1. 数据源不存在

状态码：`404 Not Found`

```json
{
  "detail": "dataspace source not found: xxx"
}
```

2. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to get dataspace source detail"
}
```

## 10. 查询 Dataspace 目录

### 8.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/directory/list`
- Content-Type：`application/json`

### 8.2 请求体

```json
{
  "source_id": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
  "path": "subdir_a"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_id` | string | 是 | Dataspace 数据源实例 ID |
| `path` | string | 否 | 相对 `root_path` 的目录路径；空字符串表示根目录 |

### 8.3 path 规则

`path` 始终是相对 Dataspace 根目录的路径。

例如，若数据源的 `root_path` 为：

```text
/ITOrktzbo184
```

则：

- `path=""` 对应远程目录 `/ITOrktzbo184`
- `path="a"` 对应远程目录 `/ITOrktzbo184/a`
- `path="a/b"` 对应远程目录 `/ITOrktzbo184/a/b`

前端不需要也不应该自己拼接 `root_path`。

### 8.4 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "sourceId": "f42d6a2f7c8a42c2a1d8e6b8a98f0f11",
    "spaceName": "空间导入相关任务优化测试空间",
    "spaceId": "2073250022174072832",
    "remotePath": "/ITOrktzbo184/subdir_a",
    "entries": [
      {
        "name": "data.csv",
        "type": "file",
        "size": "1024",
        "modify": "20260723153000",
        "raw": {
          "type": "file",
          "size": "1024",
          "modify": "20260723153000"
        }
      },
      {
        "name": "images",
        "type": "dir",
        "size": null,
        "modify": null,
        "raw": {
          "type": "dir"
        }
      }
    ]
  }
}
```

### 8.5 失败响应

1. 数据源不存在、FTP 登录失败、目录不存在

状态码：`400 Bad Request`

```json
{
  "detail": "failed to list ftp directory host=10.0.90.47 path=/ITOrktzbo184/subdir_a: 550 Failed to change directory."
}
```

2. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to list dataspace source directory"
}
```

## 11. 校验 Dataspace 数据源连接

### 9.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/validate`
- Content-Type：`application/json`

### 9.2 请求体

```json
{
  "base_url": "https://10.0.90.47",
  "app_id": "614646",
  "auth_code": "ZGNkMWRlMjVhZjg4NDY4OTk0MmY0MDUwNzA1NGM3ZDU=",
  "space_name": "空间导入相关任务优化测试空间",
  "ftp_user": "15117913512@126.com",
  "ftp_password": "Cc289836256&"
}
```

字段说明与 `create` 保持一致。

### 9.3 校验内容

后端会依次验证：

1. `base_url/app_id/auth_code` 是否能访问 Dataspace 开放接口
2. `space_name` 是否能正确解析到 `space_id`
3. 是否能拿到空间详情并解析 `ftp_link/root_path`
4. `ftp_user/ftp_password` 是否能够列出该空间根目录

### 9.4 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "valid": true,
    "space_name": "空间导入相关任务优化测试空间",
    "space_id": "2073250022174072832",
    "ftp_link": "ftp://10.0.90.47/ITOrktzbo184",
    "webdav_link": "http://10.0.90.47/webDAV/ITOrktzbo184",
    "root_path": "/ITOrktzbo184",
    "logo": "data:image/png;base64,..."
  }
}
```

### 9.5 失败响应

1. 空间、接口或 FTP 权限校验失败

状态码：`400 Bad Request`

```json
{
  "detail": "space not found by name: xxx"
}
```

或：

```json
{
  "detail": "failed to list ftp directory host=10.0.90.47 path=/ITOrktzbo184: 530 Login incorrect."
}
```

2. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to validate dataspace source"
}
```

## 12. 从用户工作空间上传文件到 Dataspace

### 12.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/workspace/file/upload`
- Content-Type：`application/json`

### 12.2 请求体

```json
{
  "user_id": "renhao",
  "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
  "workspace_path": "/temp/demo/test.csv",
  "target_dir": "import/data"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户工作空间标识 |
| `source_id` | string | 是 | 已保存的 Dataspace 数据源实例 ID |
| `workspace_path` | string | 是 | 用户工作空间内的相对文件路径，且必须是单个文件 |
| `target_dir` | string | 否 | Dataspace 空间内的目标目录，相对 `root_path`；为空时表示直接上传到空间根目录 |

### 12.3 行为说明

后端处理流程：

1. 根据 `user_id + workspace_path` 定位用户工作空间中的本地文件
2. 校验该路径存在且是文件
3. 保留原文件名
4. 将文件上传到 Dataspace 的 `target_dir/原文件名`
5. 上传成功后自动调用 `2.12 /api/ds.open/space/fl.syn` 执行空间文件刷新同步

例如：

- `workspace_path="/temp/demo/test.csv"`
- `target_dir="import/data"`

则最终会上传到 Dataspace 相对路径：

```text
import/data/test.csv
```

### 12.4 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "user_id": "renhao",
    "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
    "workspace_path": "/temp/demo/test.csv",
    "target_dir": "/import/data",
    "uploaded": {
      "sourceId": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
      "spaceName": "空间导入相关任务优化测试空间",
      "spaceId": "2073250022174072832",
      "remotePath": "/ITOrktzbo184/import/data/test.csv",
      "localPath": "/.../workspace/users/renhao/temp/demo/test.csv"
    }
  }
}
```

### 12.5 失败响应

1. 参数错误、路径非法、文件不存在、目标数据源不可用

状态码：`400 Bad Request`

```json
{
  "detail": "workspace_path is required"
}
```

或：

```json
{
  "detail": "path belongs to another user"
}
```

或：

```json
{
  "detail": "failed to upload ftp file host=10.0.90.47 path=/ITOrktzbo184/import/data/test.csv: ..."
}
```

2. 文件不存在

状态码：`404 Not Found`

```json
{
  "detail": "workspace file not found"
}
```

3. 服务内部异常

状态码：`500 Internal Server Error`

```json
{
  "detail": "failed to upload workspace file to dataspace"
}
```

## 13. 前端接入建议

建议前端按以下顺序接入：

1. 先调用 `POST /datasource/catalog/list` 获取可用数据源类型
2. 用户选择 `DataSpace` 后，可调用 `POST /datasource/catalog/detail` 获取完整字段定义
3. 前端根据 `init_fields` 动态渲染 Dataspace 表单
4. 用户填写 Dataspace 表单
5. 调用 `POST /dataspace/source/validate` 做预校验
6. 校验成功后，调用 `POST /dataspace/source/create`
7. 通过 `POST /dataspace/source/list` 展示数据源实例列表
8. 编辑已有实例时调用 `POST /dataspace/source/update`
9. 删除已有实例时调用 `POST /dataspace/source/delete`
10. 通过 `POST /dataspace/source/directory/list` 浏览目录树
11. 若要把用户工作空间文件上传到 Dataspace，可调用 `POST /dataspace/source/workspace/file/upload`
12. 若要把用户工作空间中的一组文件/目录批量上传到 Dataspace，可调用 `POST /dataspace/source/workspace/path/upload`
13. 选中的 `source_id + relative_path` 传给 `DataspaceFileSourceStop`

## 14. 按 source_id 校验已保存数据源

### 14.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/validate/by-id`
- Content-Type：`application/json`

### 14.2 请求体

```json
{
  "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b"
}
```

### 14.3 校验内容

后端先根据 `source_id` 读取已保存的数据源，再执行与 `POST /dataspace/source/validate` 相同的 Dataspace 接口和 FTP 连通性校验。

### 14.4 成功响应

```json
{
  "code": 200,
  "result": {
    "valid": true,
    "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
    "space_name": "空间导入相关任务优化测试空间",
    "space_id": "2073250022174072832",
    "ftp_link": "ftp://10.0.90.47/ITOrktzbo184",
    "webdav_link": "http://10.0.90.47/webDAV/ITOrktzbo184",
    "root_path": "/ITOrktzbo184",
    "logo": "data:image/png;base64,..."
  }
}
```

### 14.5 失败响应

```json
{
  "detail": "dataspace source not found: ..."
}
```

## 15. 注意事项

- 当前数据源类型目录只内置 `DataSpace` 一种类型
- `/datasource/catalog/*` 用于展示“有哪些可用数据源类型”及其字段定义
- `validate` 不会入库，`create` 才会入库
- `validate/by-id` 用于校验已入库的 Dataspace 数据源是否仍然可用
- `/dataspace/source/workspace/file/upload` 只接受单个文件路径，不接受目录路径
- `/dataspace/source/workspace/path/upload` 接受一组用户工作空间路径，路径中可以混合文件和目录；目录会递归展开为文件后上传
- 文件上传到 Dataspace 成功后，后端会自动调用 `2.12 /api/ds.open/space/fl.syn` 做一次刷新同步
- `path` 一律相对 `root_path`
- 当前目录浏览实际走 FTP，不依赖 Dataspace `fileList` 开放接口

## 16. 从用户工作空间批量上传文件/目录到 Dataspace

### 16.1 接口信息

- 方法：`POST`
- 路径：`/dataspace/source/workspace/path/upload`
- Content-Type：`application/json`

### 16.2 请求体

```json
{
  "user_id": "renhao",
  "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
  "workspace_paths": [
    "/temp/demo/test.csv",
    "/outputs/report_bundle"
  ],
  "target_dir": "import/data"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户工作空间标识 |
| `source_id` | string | 是 | 已保存的 Dataspace 数据源实例 ID |
| `workspace_paths` | string[] | 是 | 用户工作空间内的一组路径，支持文件和目录混合输入 |
| `target_dir` | string | 否 | Dataspace 空间内的目标目录，相对 `root_path`；为空时表示直接上传到空间根目录 |

### 16.3 行为说明

后端处理流程：

1. 根据 `user_id + workspace_paths` 逐个定位用户工作空间中的本地路径
2. 文件直接加入上传列表；目录递归展开为目录下所有文件
3. 每个文件都保留其相对于用户工作空间根目录的层级结构
4. 将每个文件上传到 Dataspace 的 `target_dir/相对用户工作空间路径`
5. 返回成功项和失败项，便于前端逐项展示

例如：

- `workspace_paths=["/temp/demo/test.csv", "/outputs/report_bundle"]`
- `target_dir="import/data"`

则可能上传到 Dataspace 相对路径：

```text
import/data/temp/demo/test.csv
import/data/outputs/report_bundle/summary.md
import/data/outputs/report_bundle/figures/plot.png
```

### 16.4 成功响应

状态码：`200 OK`

```json
{
  "code": 200,
  "result": {
    "user_id": "renhao",
    "source_id": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
    "target_dir": "/import/data",
    "uploaded": [
      {
        "workspace_path": "/temp/demo/test.csv",
        "target_path": "/import/data/temp/demo/test.csv",
        "uploaded": {
          "sourceId": "6d8a2f0a8c5c4f4ab2ef9fb86e0a8d2b",
          "spaceName": "空间导入相关任务优化测试空间",
          "spaceId": "2073250022174072832",
          "remotePath": "/ITOrktzbo184/import/data/temp/demo/test.csv",
          "localPath": "/.../workspace/users/renhao/temp/demo/test.csv"
        }
      }
    ],
    "failed": [],
    "total": 1
  }
}
```
