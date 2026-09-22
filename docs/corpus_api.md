# Corpus API

Base Path: `/api/piflow/v1`

## 目录
- [POST /corpus/connector/list](#post-corpusconnectorlist) - 分页查询连接器及节点资源信息
- [POST /corpus/dataset/list](#post-corpusdatasetlist) - 分页查询数据集列表并支持条件筛选
- [GET /corpus/dataset/available-total](#get-corpusdatasetavailable-total) - 查询可用数据集总数
- [POST /corpus/dataset/detail](#post-corpusdatasetdetail) - 根据数据集 ID 获取数据集详情
- [GET /corpus/dataset/preview](#get-corpusdatasetpreview) - 按数据集来源返回预览或目录层级
- [POST /corpus/connector/save](#post-corpusconnectorsave) - 创建连接器
- [POST /corpus/connector/update](#post-corpusconnectorupdate) - 更新连接器
- [GET /corpus/connector/detail](#get-corpusconnectordetail) - 根据连接器 ID 获取详情
- [GET /corpus/connector/latency](#get-corpusconnectorlatency) - 探测连接器节点延迟
- [GET /corpus/connector/delete](#get-corpusconnectordelete) - 删除指定连接器
- [GET /corpus/connector/disable](#get-corpusconnectordisable) - 禁用指定连接器
- [GET /corpus/connector/enable](#get-corpusconnectorenable) - 启用指定连接器
- [GET /corpus/connector/tree](#get-corpusconnectortree) - 获取连接器拓扑树
- [Error](#error) - 错误返回说明

## `POST /corpus/connector/list`
列出连接器分页信息，仅返回连接器基础详情。

Request
```json
{"pageNum":1,"pageSize":10,"keyword":"地球"}
```

`keyword` 会原样透传为上游 `/dataset.connector.page` 请求的查询参数；为空时不传该参数。

Response
```json
{
  "code": 200,
  "result": {
    "items": [
      {
        "connector": {}
      }
    ],
    "pagination": {
      "pageNum": 1,
      "pageSize": 10,
      "total": 1
    }
  }
}
```

## `POST /corpus/dataset/list`
列出数据集分页明细，支持分页 + 可选条件查询。

Request
```json
{
  "pageNum": 1,
  "pageSize": 10,
  "id": "6a744595d38ea034d388c7b4",
  "title": "中国地震",
  "titleEn": "China Earthquake",
  "field": "地球科学",
  "subject": "地震学",
  "type": "语料",
  "corpusType": "文本",
  "keywords": "地震,目录",
  "keywordsEn": "earthquake,catalog",
  "description": "语料描述",
  "descriptionEn": "dataset description",
  "usage": "科研",
  "cstr": "ES-CORPUS-B138",
  "doi": "10.1000/example",
  "version": "1.0",
  "fileNumber": 10,
  "number": 1000,
  "size": "2GB",
  "rawFormat": "tar",
  "publisher": "出版社",
  "author": "作者",
  "temporal": "1900-2020",
  "geographicCoverage": "中国",
  "language": "zh",
  "source": "公开来源",
  "cover": "cover.png",
  "fundingProject": "项目A",
  "copyRight": "copyright",
  "sharingMethods": "下载",
  "publishAt": "2026-08-20T03:29:22.345Z",
  "receiveAt": "2026-08-20T03:29:22.345Z",
  "updateAt": "2026-08-20T03:29:22.345Z",
  "pushAt": "2026-08-20T03:29:22.345Z",
  "status": 0,
  "dataSetId": "string",
  "connectorId": "DS-NODE-1",
  "from": "connector-1",
  "fromName": "连接器节点1"
}
```

说明
- `pageNum`、`pageSize` 为必填分页参数。
- 其余字段均为可选筛选条件，未传时不参与查询。
- 请求体中的 `from` 直接透传给上游数据集分页接口作为查询条件。

Response
```json
{
  "code": 200,
  "result": {
    "items": [
      {
        "id": "6a744595d38ea034d388c7b4",
        "cstr": "ES-CORPUS-B138",
        "title": "dataset title",
        "connectorId": "DS-NODE-1",
        "fromName": "连接器节点1",
        "replicaCount": 2,
        "name": "中国地震台网中心",
        "connectors": [
          {
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
            "connectorOrganization": "中国地震台网中心",
            "name": "中国地震台网中心",
            "status": "可用",
            "sync": "2026-08-07 11:52",
            "recommended": true
          },
          {
            "connectorId": "DS-NODE-2",
            "fromName": "连接器节点2",
            "connectorOrganization": "国家地球系统科学数据中心",
            "name": "国家地球系统科学数据中心",
            "status": "不可用",
            "sync": "2026-08-08 09:15",
            "recommended": false
          }
        ]
      }
    ],
    "pagination": {
      "pageNum": 1,
      "pageSize": 10,
      "total": 1
    }
  }
}
```

说明
- `connectorId`、`fromName` 继续保留，表示当前返回结果中的主连接器，兼容旧调用方。
- `connectors` 数组优先使用上游 `fromList` 作为真实副本归属来源。
- `replicaCount` 表示真实副本数量，等于 `connectors` 数组长度。
- 副本项中的 `name` 是原先的机构名称字段，`status` 与连接器 `enabled` 对应，`sync`/`recommended` 来自连接器详情。
- 当连接器节点可通过 gRPC 探测到资源时，副本项会追加 `latency_ms`，表示调用节点资源探测 RPC 的往返延迟；资源探测失败时不追加该字段。
- `recommended` 会在同一数据集的可用副本中按 CPU 核数、内存、剩余磁盘依次比较，资源最丰富的节点为 `true`，最多只有一个。
- 当上游只返回单个连接器时，`connectors` 仍会返回一个元素。

## `GET /corpus/connector/latency`
探测指定连接器节点的 gRPC 往返延迟。

Request
```text
GET /corpus/connector/latency?id=DS-NODE-1
```

Response
```json
{
  "code": 200,
  "result": {
    "connectorId": "DS-NODE-1",
    "remote_grpc_target": "10.0.82.213:50061",
    "latency_ms": 12.345
  }
}
```

## `GET /corpus/dataset/available-total`
查询可用数据集总数，不接受筛选条件。

统计口径为：全部数据集总数减去禁用连接器对应的数据集总数。

Response
```json
{
  "code": 200,
  "result": {
    "total": 42
  }
}
```

## `POST /corpus/dataset/detail`
根据数据集 ID 获取数据集详情。

Request
```json
{"datasetId":"6a744595d38ea034d388c7b4"}
```

Response
```json
{
  "code": 200,
  "result": {
    "dataset": {
      "id": "6a744595d38ea034d388c7b4",
      "cstr": "ES-CORPUS-B138",
      "title": "dataset title",
      "connectorId": "DS-NODE-1",
      "fromName": "连接器节点1",
      "replicaCount": 2,
      "name": "中国地震台网中心",
      "connectors": [
        {
          "connectorId": "DS-NODE-1",
          "fromName": "连接器节点1",
          "connectorOrganization": "中国地震台网中心",
          "name": "中国地震台网中心",
          "status": "可用",
          "sync": "2026-08-07 11:52",
          "recommended": true
        },
        {
          "connectorId": "DS-NODE-2",
          "fromName": "连接器节点2",
          "connectorOrganization": "国家地球系统科学数据中心",
          "name": "国家地球系统科学数据中心",
          "status": "不可用",
          "sync": "2026-08-08 09:15",
          "recommended": false
        }
      ]
    }
  }
}
```

详情接口中的 `connectors`、`replicaCount` 与数据集列表接口含义一致；`connectorId`、`fromName` 仍表示主连接器，用于兼容原有调用方。

## `GET /corpus/dataset/preview`
按数据集来源返回普通预览数据或一个目录层级。完整路径为：

```text
GET /api/piflow/v1/corpus/dataset/preview?cstr={cstr}[&fileId={fileId}]
```

参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `cstr` | 是 | 数据集标识。无 `fileId` 时用于查询数据集详情并进行来源判断；目录查询时应为目录服务可识别的数据集 ID。 |
| `fileId` | 否 | 当前目录节点的 `fileId`。传入后表示前端请求该目录的下一层。 |

分流规则按以下优先级执行：

1. `fileId` 不为空：不查询数据集详情，直接请求上游 `GET /metacat.file.dir.query?cstr=...&fileId=...`，返回一个目录层级。
2. `fileId` 为空：先按 `cstr` 获取数据集详情。
   - 当详情的 `source` 等于 `地球系统数值模拟装置` 时，请求上游 `GET /metacat.file.dir.query?cstr=...`，返回目录根层。
   - 其他来源请求上游 `GET /corpus.dataset.preview?cstr=...`，返回普通数据集预览。

响应中的 `result.mode` 用于前端判定内容类型：`directory` 表示目录层级，`preview` 表示普通预览。`result.data` 保留对应上游接口的完整 JSON 响应。

普通预览上游的读取超时为 600 秒，目录查询及其他 Corpus 接口仍使用默认 30 秒。若服务前有 Nginx、Ingress 或网关，需将该接口链路上的读取超时（例如 Nginx `proxy_read_timeout`）配置为不少于 600 秒；否则上游尚未返回时，网关可能先返回 504。

### 普通预览示例

Request

```text
GET /api/piflow/v1/corpus/dataset/preview?cstr=dataset_001
```

Response

```json
{
  "code": 200,
  "result": {
    "mode": "preview",
    "data": {
      "code": 200,
      "message": "OK",
      "data": {}
    }
  }
}
```

### 目录递归示例

首次查询根目录：

```text
GET /api/piflow/v1/corpus/dataset/preview?cstr=1928844366999224320
```

展开根目录中 `fileId` 为 `4003697` 的节点：

```text
GET /api/piflow/v1/corpus/dataset/preview?cstr=1928844366999224320&fileId=4003697
```

目录响应示例：

```json
{
  "code": 200,
  "result": {
    "mode": "directory",
    "data": {
      "code": 200,
      "message": "OK",
      "data": [
        {
          "datasetId": "1928844366999224320",
          "fileId": "4003697",
          "isFile": false,
          "name": "GD010-Mesovortices",
          "type": "dir"
        }
      ]
    }
  }
}
```

前端只对 `isFile: false` 的节点继续请求本接口，并将该节点的 `fileId` 作为下一次请求的 `fileId`；`isFile: true` 表示文件叶子节点，不应再展开。

## `POST /corpus/connector/save`
创建连接器。

说明
- 代理到上游 `POST /dataset.connector.save`
- 也支持别名路径 `POST /dataset.connector.save`
- 请求体会原样透传到 `corpus_route.base_url`

Request
```json
{
  "name": "连接器节点1",
  "connectorId": "DS-NODE-1",
  "type": "MASTER",
  "protocol": "http:",
  "serviceUrl": "10.0.82.213:7004",
  "enabled": true,
  "status": 1
}
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": {
      "id": "689f0c1f2d3e4f0012345678",
      "name": "连接器节点1",
      "connectorId": "DS-NODE-1"
    }
  }
}
```

## `POST /corpus/connector/update`
更新连接器。

说明
- 代理到上游 `POST /dataset.connector.update`
- 也支持别名路径 `POST /dataset.connector.update`
- 请求体会原样透传到 `corpus_route.base_url`

Request
```json
{
  "id": "689f0c1f2d3e4f0012345678",
  "name": "连接器节点1-更新",
  "connectorId": "DS-NODE-1",
  "type": "MASTER",
  "protocol": "http:",
  "serviceUrl": "10.0.82.213:7004",
  "enabled": true,
  "status": 1
}
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": {
      "id": "689f0c1f2d3e4f0012345678",
      "name": "连接器节点1-更新",
      "connectorId": "DS-NODE-1"
    }
  }
}
```

## `GET /corpus/connector/detail`
根据连接器 ID 获取连接器详情。

说明
- 代理到上游 `GET /dataset.connector.detail?id=...`
- 也支持别名路径 `GET /dataset.connector.detail?id=...`

Request
```text
GET /api/piflow/v1/corpus/connector/detail?id=689f0c1f2d3e4f0012345678
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": {
      "id": "689f0c1f2d3e4f0012345678",
      "name": "连接器节点1",
      "connectorId": "DS-NODE-1",
      "type": "MASTER",
      "protocol": "http:",
      "serviceUrl": "10.0.82.213:7004",
      "enabled": true,
      "status": 1
    }
  }
}
```

## `GET /corpus/connector/delete`
删除连接器。

说明
- 代理到上游 `GET /dataset.connector.delete?id=...`
- 也支持别名路径 `GET /dataset.connector.delete?id=...`

Request
```text
GET /api/piflow/v1/corpus/connector/delete?id=689f0c1f2d3e4f0012345678
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": null
  }
}
```

## `GET /corpus/connector/disable`
禁用连接器。

说明
- 代理到上游 `GET /dataset.connector.disable?id=...`
- 也支持别名路径 `GET /dataset.connector.disable?id=...`

Request
```text
GET /api/piflow/v1/corpus/connector/disable?id=689f0c1f2d3e4f0012345678
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": null
  }
}
```

## `GET /corpus/connector/enable`
启用连接器。

说明
- 代理到上游 `GET /dataset.connector.enable?id=...`
- 也支持别名路径 `GET /dataset.connector.enable?id=...`

Request
```text
GET /api/piflow/v1/corpus/connector/enable?id=689f0c1f2d3e4f0012345678
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": null
  }
}
```

## `GET /corpus/connector/tree`
获取连接器拓扑树。

说明
- 代理到上游 `GET /dataset.connector.tree`
- 也支持别名路径 `GET /dataset.connector.tree`

Request
```text
GET /api/piflow/v1/corpus/connector/tree
```

Response
```json
{
  "code": 200,
  "result": {
    "code": 200,
    "message": "success",
    "data": {
      "name": "root",
      "children": [
        {
          "name": "MASTER",
          "children": [
            {
              "name": "连接器节点1",
              "connectorId": "DS-NODE-1"
            }
          ]
        }
      ]
    }
  }
}
```

说明
- 连接器创建/更新接口的请求体字段由上游 `corpus-route` 的 `DataSetConnector` 模型决定。
- 在本项目中，这些字段不会二次转换，而是透传到 `corpus_route.base_url`。

## Error
```json
{"detail":"..."}
```
