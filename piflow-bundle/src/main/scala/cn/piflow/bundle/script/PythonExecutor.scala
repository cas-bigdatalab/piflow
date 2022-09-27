package cn.piflow.bundle.script

import java.util.{Date, UUID}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util.{FileUtil, PropertyUtil, PythonScriptUtil}
import org.apache.spark.SparkFiles
import org.apache.spark.deploy.PythonRunner
import org.apache.spark.sql.SparkSession

class PythonExecutor extends ConfigurableStop{
  override val authorEmail: String = "xjzhu@cnic.cn"
  override val description: String = "Run python script by PythonRunner"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var arg1 : String = _
  var arg2 : String = _
  var arg3 : String = _

  override def setProperties(map: Map[String, Any]): Unit = {

    arg1 = MapUtil.get(map,"arg1").asInstanceOf[String]
    arg2 = MapUtil.get(map,"arg2").asInstanceOf[String]
    arg3 = MapUtil.get(map,"arg3").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val arg1 = new PropertyDescriptor()
      .name("arg1")
      .displayName("arg1")
      .description("The arg1 of python")
      .defaultValue("")
      .required(true)
      .language(Language.Python)

    val arg2 = new PropertyDescriptor()
      .name("arg2")
      .displayName("arg1")
      .description("The arg1 of python")
      .defaultValue("")
      .required(true)
      .language(Language.Python)

    val arg3 = new PropertyDescriptor()
      .name("arg3")
      .displayName("arg1")
      .description("The arg1 of python")
      .defaultValue("")
      .required(true)
      .language(Language.Python)

    descriptor = arg1 :: descriptor
    descriptor = arg3 :: descriptor
    descriptor = arg1 :: descriptor
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
    val appID = spark.sparkContext.applicationId
    val pyFilePath = "pythonExecutor/PythonExecutor.py"
    val pyFiles = "DataInputStream.py,DataOutputStream.py,ConfigurableStop.py"
    val hdfs = PropertyUtil.getPropertyValue("fs.defaultFS")

    //    val inputPath = hdfs + "/piflow/python/" + appID + "/inport/default"
    //    var outputPath = hdfs + "/piflow/python/" + appID + "/outport/default"
    val inputPath = "/piflow/python/" + appID + "/inport/default/"
    var outputPath = "/piflow/python/" + appID + "/outport/default/"

    val df = in.read()
    df.write.format("csv").mode("overwrite").option("set","\t").save(inputPath)

    PythonRunner.main(Array(pyFilePath, pyFiles, "-i " + inputPath, "-o " + outputPath))

    println("spark stop ,no restart -----a--------------")
    val outDF = spark.read.format("csv")
      .option("header",true)
      .option("mode","FAILFAST")
      .load(outputPath)
    outDF.show()
    out.write(outDF)

  }
}
