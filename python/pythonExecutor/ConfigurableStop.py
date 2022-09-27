import os
#os.environ['PYTHONPATH'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_PYTHON'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_DRIVER_PYTHON'] = './pyspark/venv/bin/python3'
import sys
import argparse
import findspark
findspark.init()
import atexit
findspark.init()
from DataInputStream import *
from DataOutputStream import *
from pyspark.sql import SparkSession
from pyhdfs import HdfsClient
import pandas as pd
import py4j
from py4j.java_gateway import JavaGateway

class ConfigurableStop:

    argparser = argparse.ArgumentParser(description="ParserMainEntrance")
    argparser.add_argument('--input', '-i', help="input path", default=list(), required=True)
    argparser.add_argument('--output', '-o', help="output path", default=list(), required=True)
    arglist = argparser.parse_args()

    def __init__(self):
        #print("hello ConfigurableStop!")
        #self.spark = SparkSession.newSession()
        # self.spark = SparkSession.builder.getOrCreate()

        # self.input="hdfs://10.0.90.155:9000/piflow/python/application_1652954785551_0255/inport/default"
        # self.dataInputStream = DataInputStream(self.spark, self.input)
        # self.dataOutputStream = DataOutputStream(self.spark, self.output)

        self.output = self.arglist.output.strip()
        self.input = self.arglist.input.strip()

        print(self.input)
        print(self.output)
        self.hdfsUrl = '10.0.82.108:9870'

        self.dataInputStream = DataInputStream(self.hdfsUrl, self.input).read()
        self.dataOutputStream = DataOutputStream(self.hdfsUrl, self.output)


    def perform(self):
        print("hello ConfigurableStop!")


if __name__== "__main__":
    test = ConfigurableStop()
    test.perform()




