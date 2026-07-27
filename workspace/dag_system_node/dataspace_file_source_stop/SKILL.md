---
name: dataspace_file_source_stop
description: Dataspace 文件输入源算子。用于根据 Dataspace 数据源实例 ID 和空间内相对路径下载单个文件，并将该文件作为工作流输入提供给下游算子。该算子没有上游输入，必须作为 DAG 的起始节点使用。
name_zh: Dataspace 文件输入源算子
input_params:
  - name: datasource_id
    type: string
    required: true
    description: Dataspace 数据源实例 ID
  - name: relative_path
    type: string
    required: true
    description: 需要下载的 Dataspace 空间内相对文件路径
output_params:
  - name: output
    type: string
    description: 下载后的本地文件引用，提供给下游算子使用
tag: 输入
node_category: system
publisher: COMMUNITY
---

# dataspace_file_source_stop

用于作为 DAG 的起始节点，从 Dataspace 空间下载指定文件，并向下游节点暴露 `output` 输出槽位供引用。
