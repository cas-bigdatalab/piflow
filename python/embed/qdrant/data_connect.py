from pyhdfs import HdfsClient
from hdfs.client import Client
import pandas as pd
import os
import uuid
import shutil


class DATAConnect:
    def __init__(self):
        env_dist = os.environ
        self.HdfsClientHost = env_dist.get("hdfs_url")
        print(self.HdfsClientHost)
        self.client_read = HdfsClient(self.HdfsClientHost)
        self.client_wirte = Client('http://'+self.HdfsClientHost)

    def dataInputStream(self, port="1"):
        df = pd.DataFrame()
        with open('/app/inputPath.txt','r', encoding='utf-8') as f:
            input_path_dir = f.readline().strip("\n")
            input_path = input_path_dir+port+'/'
           
            print("--------------------")
            print(input_path)
            print("--------------------")

            
            # flag = self.client_read.get_content_summary(input_path).get('directoryCount')
            # if flag == 0 : df = pd.concat([df, pd.read_table(self.client_read.open(input_path))]) 
            # else: df = pd.concat([df,pd.concat([pd.read_table(self.client_read.open(input_path+i)) for i in self.client_read.listdir(input_path) if i.endswith('.parquet')])])
            # print(df.head(5))
            # 初始化一个空的 DataFrame 用于存储所有结果 
            
            # 使用 client_read 的方法列出目录中的文件，并检查扩展名  
            _path_id = str(uuid.uuid4())
            _COPYPATH:str = "/data/piflow/tmp/"+_path_id
            os.makedirs(_COPYPATH, exist_ok=True)
            for i in self.client_read.listdir(input_path):

                FILEPATH:str = _COPYPATH+"/copy.parquet"
                if i.endswith('.parquet'):
                    # 构建完整的文件路径
                    file_path = input_path + i
                    # 使用 pd.read_parquet 读取文件
                    print("CURRENT_DIRECTORY:", os.getcwd())
                    self.client_read.copy_to_local(file_path, FILEPATH)
                    temp_df = pd.read_parquet(FILEPATH) # self.client_read.open(file_path))
                    # 将读取的 DataFrame 追加到主 DataFrame
                    df = pd.concat([df, temp_df], ignore_index=True)
            shutil.rmtree(_COPYPATH)
        print(df.head(5))
        return df
    
    def dataOutputStream(self, df, port="1"):
        with open('/app/outputPath.txt','r', encoding='utf-8') as f:
            output_path_dir= f.readline().strip("\n")
            output_path= output_path_dir + port

            print("--------------------")
            print(output_path)
            print("--------------------")

            self.client_wirte.makedirs(output_path, '777')
            self.client_wirte.write(output_path +'/demo.csv', df.to_csv(index=False, sep=','), overwrite=True, encoding='utf-8')


    def putFileToHdfs(self,  hdfs_path, local_path, isDelete=False):        
        # 如果文件已存在，自动删除，默认为 False
        # if isDelete : self.client_wirte.delete(hdfs_path)      
        # hdfs 路径会自动创建
        self.client_wirte.upload(hdfs_path, local_path)

    def downloadFileFromHdfs(self, hdfs_path, local_path, overwrite=False):
        # 自动创建文件夹
        parentDir = os.path.dirname(local_path)
        print(parentDir)
        # 判断本地文件夹是否存在
        isExists = os.path.exists(parentDir)
        # 不存在，自动创建
        if not isExists : os.makedirs(parentDir)

        # 本地路径不会自动创建
        self.client_wirte.download(hdfs_path, local_path, overwrite)
    #文件夹下载
    def downloadFolderFromHdfs(self, hdfs_path, local_path, overwrite=False):
        # 自动创建文件夹
        parentDir = os.path.dirname(local_path)
        print(parentDir)
        # 判断本地文件夹是否存在
        isExists = os.path.exists(parentDir)
        # 不存在，自动创建
        if not isExists : os.makedirs(parentDir)

        # 本地路径不会自动创建
        # 本地路径少一级才会正确下载，如 hdfs_path=/a/b/  parentDir=/a
        self.client_wirte.download(hdfs_path, parentDir, overwrite)
