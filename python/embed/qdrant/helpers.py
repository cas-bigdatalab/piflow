import itertools, pandas as pd
import os

embed_models_path = os.environ.get("embed_model","/data/models/")

if(embed_models_path == "embed_models_path"):
    embed_models_path = "/data/models/"
    
# 如果embed_models_path不以'/'结尾，则加上'/'  
if not embed_models_path.endswith('/'):  
    embed_models_path += '/'

def chunk_generator(lis:list, batch_size:int = 100):
    lis = iter(lis)
    chunk = tuple(itertools.islice(lis, batch_size))
    while chunk: # amogus
        yield chunk
        chunk = tuple(itertools.islice(lis, batch_size))

def transpose(data:tuple[dict]) -> dict[str,list]:
    df = pd.DataFrame(data)
    retD = {}
    for c in df.columns:
        retD[c] = df[c].to_list()
    return retD

def embed_change(name:str) -> str:
    match name:
        case "all_MiniLM_L6_v2":
            return embed_models_path + "all_MiniLM"
        case "sentence-transformers/all-MiniLM-L6-v2":
            return embed_models_path + "all_MiniLM"
        
        case "all-roberta-large-v1":
            return embed_models_path + "all_RoBERTa_large"
        case "sentence-transformers/all-roberta-large-v1":
            return embed_models_path + "all_RoBERTa_large"
        
        case "average_word_embeddings_glove.840B.300d":
            return embed_models_path + "glove_avg_word"
        case "sentence-transformers/average_word_embeddings_glove.840B.300d":
            return embed_models_path + "glove_avg_word"
        
        case "gte-small":
            return embed_models_path + "gteSmallModel"
        case "thenlper/gte-small":
            return embed_models_path + "gteSmallModel"
        
        case "sentence-t5-xl":
            return embed_models_path + "sentence_t5"
        case "sentence-transformers/sentence-t5-xl":
            return embed_models_path + "sentence_t5"
        
        case "snowflake-arctic-embed-m":
            return embed_models_path + "snowflake_arctic"
        case "Snowflake/snowflake-arctic-embed-m":
            return embed_models_path + "snowflake_arctic"
        
        case "sentence-transformers-e5-large-v2":
            return embed_models_path + "ste_embaas_e5_large"
        case "embaas/sentence-transformers-e5-large-v2":
            return embed_models_path + "ste_embaas_e5_large"
        
        case _:
            raise ValueError("Bad Model Name")
        

# remove duplicate rows
# def purge(data:pd.DataFrame) -> pd.DataFrame:
#     return data.drop_duplicates()