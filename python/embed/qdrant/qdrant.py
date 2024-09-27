import typing as t
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings as hfe
from transformers import AutoConfig
from sys import argv
from helpers import *
from data_connect import DATAConnect
import sys
import warnings

# 默认参数值
DEFAULT_COLLECTION_NAME = "default_collection"
DEFAULT_BATCH_SIZE = 100
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_GRPC_PORT = 6334
DEFAULT_EMBED_MODEL = "all_MiniLM_L6_v2"
DEFAULT_DISTANCE_METRIC = "cosine"
DEFAULT_HEADERS = ""

def write_dict(collection_name: str, elements_dict: t.List[t.Dict[str, str]], client: QdrantClient, batch_size: int):
    embedFunc = hfe(model_name=embed_model)

    def _embedText(s: str) -> t.List[float]:
        return embedFunc.embed_documents(texts=[s])[0]

    points = []
    print("开始转化为向量嵌入了")
    for i in range(len(elements_dict)):
        content = elements_dict[i]
        vector = _embedText(str(content['text']))
        points.append(PointStruct(id=i, vector=vector, payload=content))

        if (i + 1) % batch_size == 0 or i == len(elements_dict) - 1:
            try:
                print(f"Uploading {len(points)} points to Qdrant")
                client.upsert(collection_name=collection_name, points=points)
                points.clear()
            except Exception as e:
                print(f"Error during upsert: {e}")

    print(f"{len(elements_dict)}条数据全部写入完成!")

# ## 选择嵌入模型
# def embed_change(name: str) -> str:
#     embed_models_path = "your/base/path/"  # 假设你有一个基础路径
#
#     # 使用字典映射模型名称到嵌入模型路径
#     model_mapping = {
#         "all_MiniLM_L6_v2": embed_models_path + "all_MiniLM",
#         "sentence-transformers/all-MiniLM-L6-v2": embed_models_path + "all_MiniLM",
#
#         "all-roberta-large-v1": embed_models_path + "all_RoBERTa_large",
#         "sentence-transformers/all-roberta-large-v1": embed_models_path + "all_RoBERTa_large",
#
#         "average_word_embeddings_glove.840B.300d": embed_models_path + "glove_avg_word",
#         "sentence-transformers/average_word_embeddings_glove.840B.300d": embed_models_path + "glove_avg_word",
#
#         "gte-small": embed_models_path + "gteSmallModel",
#         "thenlper/gte-small": embed_models_path + "gteSmallModel",
#
#         "sentence-t5-xl": embed_models_path + "sentence_t5",
#         "sentence-transformers/sentence-t5-xl": embed_models_path + "sentence_t5",
#
#         "snowflake-arctic-embed-m": embed_models_path + "snowflake_arctic",
#         "Snowflake/snowflake-arctic-embed-m": embed_models_path + "snowflake_arctic",
#
#         "sentence-transformers-e5-large-v2": embed_models_path + "ste_embaas_e5_large",
#         "embaas/sentence-transformers-e5-large-v2": embed_models_path + "ste_embaas_e5_large"
#     }
#
#     # 使用 .get() 方法查找模型对应的路径，若不存在则抛出异常
#     path = model_mapping.get(name)
#     if path is not None:
#         return path
#     else:
#         raise ValueError("Bad Model Name")

if __name__ == "__main__":
    # 获取组件配置参数,使用命令行参数或默认值进行赋值
    collection_name: str = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COLLECTION_NAME
    batch_size: int = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BATCH_SIZE
    host: str = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_HOST
    port: int = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_PORT
    grpc_port: int = int(sys.argv[5]) if len(sys.argv) > 5 else DEFAULT_GRPC_PORT
    embed_model = embed_change(sys.argv[6]) if len(sys.argv) > 6 else DEFAULT_EMBED_MODEL
    # embed_model = sys.argv[6] if len(sys.argv) > 6 else DEFAULT_EMBED_MODEL
    distance_metric = sys.argv[7] if len(sys.argv) > 7 else DEFAULT_DISTANCE_METRIC

    # distance_metric = "manhattan"
    # 距离度量方式选择.
    distance_switch = {
        'euclid': Distance.EUCLID,
        'cosine': Distance.COSINE,
        'dot': Distance.DOT,
        'manhattan': Distance.MANHATTAN
    }
    # 检查输入的距离度量是否有效
    if distance_metric in distance_switch:
        distance_metric = distance_switch[distance_metric]
        print(f"选择的距离度量方式是: {distance_metric}")
    else:
        # 获取距离度量，如果输入不在字典内，则默认选择 Distance.COSINE
        distance_metric = distance_switch.get(distance_metric, Distance.COSINE)
        print(f"不支持的距离度量方式: {distance_metric}, 系统默认选择了{distance_metric}余弦度量!!")


    dataConnect = DATAConnect()
    print("dataConnect = DATAConnect()成功！")

    # df = pd.read_parquet("./test2.parquet")
    df = dataConnect.dataInputStream(port="input_read")
    df.drop_duplicates(subset=["element_id"], inplace=True)
    print(df.head(5))

    # collection_name = "test_collection4"

    # embed_model = "/data/model/all-MiniLM-L12-v1"


    print(f"Parameters received: {collection_name}, {batch_size}, {host},{port}, {grpc_port},{embed_model},{distance_metric}")

    config = AutoConfig.from_pretrained(embed_model)
    output_dim = config.hidden_size
    print(f"该模型的输出向量维度为: {output_dim}!")

    # client = QdrantClient(host='localhost', port=6333)
    # #连接到Qdrant数据库。如果提供了host和port，则连接远程Qdrant实例。否则，将连接到本地实例。

    if host and port:
        # 如果提供了host和port，则连接远程Qdrant实例
        client = QdrantClient(
            host=host,
            port=port,
            # grpc_host=grpc_host if grpc_host else host,  # 如果没有提供grpc_host，则使用host
            grpc_port=grpc_port,  # 默认GRPC端口为6334
            prefer_grpc=True,  # 优先使用gRPC
            headers=DEFAULT_HEADERS
        )
        print(f"连接到远程Qdrant实例: {host}:{port}")
    else:
        # 如果没有提供host和port，连接到本地实例
        client = QdrantClient(path="./qdrant_local.db")  # 使用本地路径的嵌入式Qdrant数据库
        warnings.warn("由于缺少host或port参数，创建了一个本地临时Qdrant客户端，进程结束后数据库将被删除。")


    datas = []
    print("向量写入前")
    for i in range(len(df)):
        dic = {
            "filename": df.iloc[i].get("metadata", {}).get("filename", ""),
            "filetype": df.iloc[i].get("metadata", {}).get("filetype", ""),
            "languages": str(df.iloc[i].get("metadata", {}).get("languages", "")),
            "page_number": str(df.iloc[i].get("metadata", {}).get("page_number", "")),
            "text": str(df.iloc[i].get("text", "")),
            "type": df.iloc[i].get("type", "")
        }
        datas.append(dic)

    collections = [col.name for col in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=output_dim,
                distance=distance_metric
            )
        )

    write_dict(collection_name=collection_name, elements_dict=datas, client=client, batch_size=batch_size)
    client.close()
    print("向量写入结束")
