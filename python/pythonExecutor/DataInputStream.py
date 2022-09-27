import os
#os.environ['PYTHONPATH'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_PYTHON'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_DRIVER_PYTHON'] = './pyspark/venv/bin/python3'
import sys
import argparse
from pyspark.sql import SparkSession
from pyhdfs import HdfsClient
import pandas as pd

class DataInputStream:

    def __init__(self, hdfsUrl, inputFilePath):
        self.inputFilePath = inputFilePath
        self.hdfsUrl = hdfsUrl

    def read(self):
        client = HdfsClient(hosts=self.hdfsUrl)
        flag = client.get_content_summary(self.inputFilePath).get('directoryCount')
        df = pd.DataFrame()
        if flag == 0 : df = df.append(pd.read_table(client.open(self.inputFilePath)))
        else: df = df.append(pd.concat([pd.read_table(client.open(self.inputFilePath+i)) for i in client.listdir(self.inputFilePath) if i.endswith('.csv')]))
        print(df.head(3))
        # sparkDataFrame = self.spark.read\
        #     .option("inferSchema","true")\
        #     .option("header","true")\
        #     .csv(self.inputPath)
        return df




