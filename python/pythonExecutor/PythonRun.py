import os
env_dist = os.environ

os.environ['PYTHONPATH'] = 'pyspark/venv/bin/python3'

from ConfigurableStop import *
from DataOutputStream import *


class PythonRun(ConfigurableStop):
    def __init__(self):
        ConfigurableStop.__init__(self)


    def perform(self):
        pandasDF = self.dataInputStream
        print(type(pandasDF))
        data = pandasDF.loc[0]
        data.show()

        self.dataOutputStream.write(pandasDF)

if __name__ == "__main__":

    for i in range(0, len(sys.argv)):
        print("paramaters ", i, sys.argv[i])

    newtest = PythonRun()
    newtest.perform()
