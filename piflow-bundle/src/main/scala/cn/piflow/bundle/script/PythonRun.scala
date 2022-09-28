package cn.piflow.bundle.script

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}


import org.apache.spark.deploy.PythonRunner
import org.apache.spark.sql.SparkSession

class PythonRun extends ConfigurableStop{
  override val authorEmail: String = ""
  override val description: String = ""
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var arg_1 : String = _
  var arg_2 : String = _
  var arg_3 : String = _

  override def setProperties(map: Map[String, Any]): Unit = {

    arg_1 = MapUtil.get(map,"arg_1").asInstanceOf[String]
    arg_2 = MapUtil.get(map,"arg_2").asInstanceOf[String]
    arg_3 = MapUtil.get(map,"arg_3").asInstanceOf[String]
  }


  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val arg_1 = new PropertyDescriptor()

    val arg_2 = new PropertyDescriptor()

    val arg_3 = new PropertyDescriptor()

    descriptor = arg_1 :: descriptor
    descriptor = arg_2 :: descriptor
    descriptor = arg_3 :: descriptor
    descriptor
  }
  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/python.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.ScriptGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val spark = pec.get[SparkSession]()
    val ID = spark.sparkContext.applicationId
    val pyPath = "pythonExecutor/PythonRun.py"
    val pyFileshelp = "DataInputStream.py,DataOutputStream.py,ConfigurableStop.py"

    val inputPath = "/piflow/python/" + ID + "/inport/default/"
    var outputPath = "/piflow/python/" + ID + "/outport/default/"

    val dataFrame = in.read()
    dataFrame.write.format("csv").mode("overwrite").option("set","\t").save(inputPath)

    PythonRunner.main(Array(pyPath, pyFileshelp, "-i " + inputPath, "-o " + outputPath))

    val outDataFrame = spark.read.format("csv")
      .option("mode","FAILFAST")
      .option("header",true)
      .load(outputPath)
    outDataFrame.show()
    out.write(outDataFrame)

  }

}
