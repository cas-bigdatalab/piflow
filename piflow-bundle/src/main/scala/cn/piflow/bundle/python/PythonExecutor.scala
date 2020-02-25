package cn.piflow.bundle.python

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.python.core.{PyFunction, PyInteger, PyObject}
import org.python.util.PythonInterpreter

/**
  * Created by xjzhu@cnic.cn on 2/24/20
  */
class PythonExecutor extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Execute python script"
  override val inportList: List[String] = List(PortEnum.DefaultPort)
  override val outportList: List[String] = List(PortEnum.DefaultPort)

  var script : String = _

  override def setProperties(map: Map[String, Any]): Unit = {
    script = MapUtil.get(map,"script").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val script = new PropertyDescriptor().name("script").displayName("script").description("The code of python").defaultValue("").required(true)
    descriptor = script :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/python/python.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Python)
  }
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
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
    val interpreter = new PythonInterpreter()
    interpreter.exec(script)
    /*val proc1 = Runtime.getRuntime().exec("python " + script)
    proc1.waitFor()*/
  }
}
