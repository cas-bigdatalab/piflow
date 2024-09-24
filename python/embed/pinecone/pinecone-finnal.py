from langchain_huggingface import HuggingFaceEmbeddings as hfe
import os
from data_connect import DATAConncet  # 引入 data_connect 中的 DATAConncet 类
import pandas as pd
from helpers import *# 从 helpers.py 引入 embed_change 函数
import sys
from pinecone import Pinecone, ServerlessSpec  # 引入 Pinecone 和 ServerlessSpec
import numpy as np

# 支持的 metric 类型
SUPPORTED_METRICS = {"euclidean", "cosine", "dotproduct"}


def init_pinecone_index(api_key: str,
                        index_name: str = "hhh",
                        dimension: int = 384,  # 外部传入 dimension
                        metric: str = "cosine",
                        cloud: str = "aws", region: str = "us-east-1"):
    # 检查传入的 metric 是否支持
    if metric not in SUPPORTED_METRICS:
        print(f"不支持这种 metric: {metric}，已修改为默认的 metric: 'cosine'")
        metric = "cosine"  # 设置为默认 metric

    # 初始化 Pinecone 客户端
    pc = Pinecone(api_key=api_key)

    # 如果索引不存在，则创建索引
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,  # 通过外部参数传入 dimension
            metric=metric,  # 使用用户传入或默认的距离度量标准
            spec=ServerlessSpec(
                cloud=cloud,  # 指定云平台
                region=region  # 指定区域
            )
        )
    # 返回连接到的索引
    return pc.Index(index_name)


def vectorize_texts(df: pd.DataFrame, index, embed_provider: str, batch_size: int = 100):
    # 初始化嵌入模型
    embed_func = hfe(model_name=embed_provider)

    # 批量存储向量
    vectors_to_insert = []

    for idx, record in df.iterrows():  # 迭代 DataFrame 每一行
        element_id = record.get('element_id', 'N/A')
        print(f"Processing Element ID: {element_id}")

        # 只对 `text` 字段进行向量化
        if 'text' in record:
            # 使用 embed_documents 来替代 encode，直接获取嵌入向量
            text_vector = embed_func.embed_documents([str(record['text'])])[0]  # 返回的是一个列表，取第一个元素
            vectors_to_insert.append((element_id, text_vector, {  # 不需要再调用 .tolist()
                "element_id": element_id,
                "type": record.get('type', 'N/A')  # 作为元数据存储
            }))

        # 处理 `metadata` 字段，将元数据直接存储
        metadata = {}
        if 'metadata' in record:
            metadata = {
                "filename": record['metadata'].get('filename', 'N/A'),
                "filetype": record['metadata'].get('filetype', 'N/A'),
                # 确保 languages 是 list 或 str，而不是 ndarray
                "languages": record['metadata'].get('languages', 'N/A')
                if not isinstance(record['metadata'].get('languages'), np.ndarray)
                else record['metadata'].get('languages').tolist(),
                "page_number": record['metadata'].get('page_number', 'N/A')
            }
            # 将 metadata 作为元数据存储，但不向量化
            vectors_to_insert[-1][2].update(metadata)  # 把元数据加入最新的向量

        # 检查是否达到批量大小限制
        if len(vectors_to_insert) >= batch_size:
            # 批量插入到 Pinecone 中
            index.upsert(vectors=vectors_to_insert)
            print(f"Batch inserted {len(vectors_to_insert)} vectors")
            vectors_to_insert = []  # 清空列表以便继续下一批处理

    # 插入剩余的向量
    if vectors_to_insert:
        index.upsert(vectors=vectors_to_insert)
        print(f"Batch inserted {len(vectors_to_insert)} vectors (final batch)")


if __name__ == "__main__":
    # 从命令行或外部配置中获取 Pinecone 连接信息和模型名称，设置默认值
    api_key = sys.argv[1]  # Pinecone API key

    # 可选的命令行参数，有默认值
    embed_provider = embed_change(sys.argv[2]) if len(sys.argv) > 2 else "all_MiniLM_L6_v2"  # 嵌入模型名称
    index_name = sys.argv[3] if len(sys.argv) > 3 else "document-embeddings"  # 索引名称
    dimension = int(sys.argv[4]) if len(sys.argv) > 4 else 384  # 向量维度
    metric = sys.argv[5] if len(sys.argv) > 5 else "cosine"  # 距离度量方法
    cloud = sys.argv[6] if len(sys.argv) > 6 else "aws"  # 云平台
    region = sys.argv[7] if len(sys.argv) > 7 else "us-east-1"  # 区域
    batch_size = int(sys.argv[8]) if len(sys.argv) > 8 else 100  # 批量大小

    print(f"Parameters received: {api_key}, {embed_provider}, {index_name},{dimension}, {metric},{cloud},{region},{batch_size}")
    # 初始化数据库并创建或连接到索引
    index = init_pinecone_index(api_key, index_name, dimension, metric, cloud, region)

    # 使用 data_connect 中的方法从 HDFS 获取数据
    dataConnect = DATAConncet()

    # 从 HDFS 读取数据
    df = dataConnect.dataInputStream(port="input_read")
    df.drop_duplicates(subset=["element_id"], inplace=True)

    vectorize_texts(df,index,embed_provider,batch_size=batch_size)
