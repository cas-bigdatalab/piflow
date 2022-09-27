import os
print("hello PythonExecutor!!!!!!!!!!!!!!!!!!")
env_dist = os.environ
for key in env_dist:
    print(key + ':' + env_dist[key])

os.environ['PYTHONPATH'] = 'pyspark/venv/bin/python3'
# os.environ['PYTHONHOME'] = './pyspark/venv/bin'

print ("After PYTHONPATH" + os.environ['PYTHONPATH'] + '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

env_dist1 = os.environ
for key in env_dist1:
    print(key + ':' + env_dist1[key])

#os.environ['PYSPARK_PYTHON'] = './pyspark/venv/bin/python3'
#os.environ['PYSPARK_DRIVER_PYTHON'] = './pyspark/venv/bin/python3'
import sys
import argparse
from ConfigurableStop import *
from DataInputStream import *
from DataOutputStream import *

class PythonExecutor(ConfigurableStop):
    def __init__(self):
        ConfigurableStop.__init__(self)
        # DataOutputStream.__init__(self)
        # DataInputStream.__init__(self)
        #print("hello PythonExecutor!")

    def perform(self):
        pandasDF = self.dataInputStream
        print(type(pandasDF))
        print("show DataFrame by Spark!")
        print("show DataFrame by pandas!")
        # newSparkDF = self.spark.createDataFrame(pandasDF)
        self.dataOutputStream.write(pandasDF)


if __name__== "__main__":
    print ("test-------------")
    print(1,2, end=' 3------456 ')
    print(len(sys.argv))
    for i in range(0, len(sys.argv)):
        print("paramaters ",i, sys.argv[i])
    test = PythonExecutor()
    test.perform()