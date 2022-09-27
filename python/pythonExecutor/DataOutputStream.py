import os
#os.environ['PYTHONPATH'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_PYTHON'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_DRIVER_PYTHON'] = './pyspark/venv/bin/python3'
import sys
import argparse
from pyspark.sql import SparkSession
from hdfs.client import Client
import pandas as pd

class DataOutputStream:

    def __init__(self, hdfs_url, outputFilePath):
        self.hdfs_url = hdfs_url
        self.outputFilePath = outputFilePath

    def write(self, DataFrame):
        client = Client('http://'+self.hdfs_url)
        client.makedirs(self.outputFilePath, '777')
        client.write(self.outputFilePath +'demo.csv', DataFrame.to_csv(index=False, sep=','), overwrite=True, encoding='utf-8')

        # DataFrame.write.mode("overwrite")\
        #     .option("header","true")\
        #     .option("delimiter",",")\
        #     .csv(self.outputPath)





