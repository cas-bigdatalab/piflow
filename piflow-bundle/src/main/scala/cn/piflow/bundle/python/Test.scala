package cn.piflow.bundle.python

import java.util
import java.util.Properties

import jep.Jep


object Test {

  def main(args: Array[String]): Unit = {

    val script =
      """
        |import sys
        |import os
        |
        |import numpy as np
        |from scipy import linalg
        |import pandas as pd
        |
        |import matplotlib
        |matplotlib.use('Agg')
        |import matplotlib.pyplot as plt
        |
        |import seaborn as sns
        |
        |import timeit
        |import numpy.random as np_random
        |from numpy.linalg import inv, qr
        |from random import normalvariate
        |
        |import pylab
        |
        |if __name__ == "__main__":
        |	print("Hello PiFlow")
        |	try:
        |		print("\n mock data：")
        |		nsteps = 1000
        |		draws = np.random.randint(0,2,size=nsteps)
        |		print("\n " + str(draws))
        |		steps = np.where(draws > 0, 1, -1)
        |		walk = steps.cumsum()
        |		print("Draw picture")
        |		plt.title('Random Walk')
        |		limit = max(abs(min(walk)), abs(max(walk)))
        |		plt.axis([0, nsteps, -limit, limit])
        |		x = np.linspace(0,nsteps, nsteps)
        |		plt.plot(x, walk, 'g-')
        |		plt.savefig('/opt/python.png')
        |	except Exception as e:
        |		print(e)
        |
        |
        |
      """.stripMargin
    /*val script =
      """
        |import sys
        |import os
        |
        |if __name__ == "__main__":
        |    print("Hello PiFlow")
      """.stripMargin*/
    /*val props = new Properties()
    props.put("python.home","/usr/bin/python3")
    val preprops = System.getProperties

    PythonInterpreter.initialize(preprops,props,Array[String]())*/
    /*val interpreter = new PythonInterpreter()
    interpreter.exec(script)*/

    val jep = new Jep()
    //jep.runScript("/opt/python.py")
    jep.runScript("/opt/project/piflow/piflow-bundle/src/main/python/Test.py")
    //val df = jep.getValue("result")

    val a=2
    val b=3
    jep.eval(s"c = add($a,$b)")
    val ans = jep.getValue("c")
    println(ans)

    val hashMapClassType = new util.HashMap[String, String]()
    val listClassType = List()

    val jstr = "{'fruit':['apple', 'pear','strawberry'],'count':[3,2,5],'price':[10,9,8]}"
    jep.eval(s"df = getDataFrame($jstr)")
    val df1 = jep.getValue("df",listClassType.getClass())

    println(df1)
    //val ans2 = jep.invoke("add", a,b).asInstanceOf[Int]
    //println(ans2)




    //val score = jep.getValue("score[0]").asInstanceOf[Double]
    //val accuracy = jep.getValue("score[1]").asInstanceOf[Double]
    //println(s"score is $score and accuracy is $accuracy")
    println("finished!")

  }

}
