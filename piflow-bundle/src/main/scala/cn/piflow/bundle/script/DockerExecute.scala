package cn.piflow.bundle.script

import cn.piflow.bundle.util.DockerStreamUtil
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.util.PropertyUtil
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.SparkSession


class DockerExecute extends ConfigurableStop{

  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "docker runs Python"
  val inportList: List[String] = List(Port.AnyPort)
  val outportList: List[String] = List(Port.AnyPort)

  var outports : List[String] = _
  var inports : List[String] = _

  var ymlContent:String =_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val appID: String = spark.sparkContext.applicationId
    val uuid: String = System.currentTimeMillis().toString

    val stringBuffer = new StringBuffer()

    PropertyUtil.getPropertyValue("hdfs.cluster").split(";").foreach(x => {
      stringBuffer.append(System.lineSeparator() + "      - \"" + x + "\"")
    })

    ymlContent = ymlContent.replace("piflow_hdfs_url", PropertyUtil.getPropertyValue("hdfs.web.url"))
      .replace("piflow_extra_hosts", stringBuffer.toString)

    println(ymlContent)
    
    DockerStreamUtil.execRuntime("mkdir app")
    val ymlName = uuid+".yml"

    println("执行命令：=============================执行创建app文件夹命令=================")
    DockerStreamUtil.execRuntime(s"echo '${ymlContent}'> app/${ymlName}")

    val dockerShellString=s"docker-compose -f app/${ymlName} up"
    val dockerDownShellString=s"docker-compose -f app/${ymlName} down"

    val inputPath = "/piflow/docker/" + appID + s"/inport_${uuid}/"
    val outputPath = "/piflow/docker/" + appID + s"/outport_${uuid}/"

    val inputPathStringBuffer = new StringBuffer()

    if(!(inports.contains("Default") || inports.contains("DefaultPort"))){
      inports.foreach(x => {
        println("输入端口：============================="+x+"=================")
        val hdfsSavePath = inputPath + x
        inputPathStringBuffer.append(hdfsSavePath + ",")
        in.read(x).write.format("csv").mode("overwrite")
          .option("delimiter", "\t")
          .option("header", true).save(hdfsSavePath)
      })

      println("执行命令：======================输入路径写入app/inputPath.txt 文件========================")
      DockerStreamUtil.execRuntime(s"echo ${inputPath}> app/inputPath.txt")
    }
    if(!(outports.contains("Default") || outports.contains("DefaultPort"))){
      println("执行命令：======================输出路径写入app/outputPath.txt 文件========================")
      DockerStreamUtil.execRuntime(s"echo ${outputPath}> app/outputPath.txt")
    }

    println("执行命令：======================创建镜像命令========================")
    DockerStreamUtil.execRuntime(dockerShellString)

    if(!(outports.contains("Default") || outports.contains("DefaultPort"))){
      outports.foreach(x => {
        println("输出端口：============================="+x+"=================")
        val outDF = spark.read.format("csv")
          .option("header", true)
          .option("mode", "FAILFAST")
          .load(outputPath + x)
        out.write(x, outDF)
      })
    }

    DockerStreamUtil.execRuntime(dockerDownShellString)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    val outportStr = MapUtil.get(map, "outports").asInstanceOf[String]
    outports = outportStr.split(",").map(x => x.trim).toList
    val inportStr = MapUtil.get(map, "inports").asInstanceOf[String]
    inports = inportStr.split(",").map(x => x.trim).toList

    ymlContent =MapUtil.get(map, key = "ymlContent").asInstanceOf[String]

  }

  override def initialize(ctx: ProcessContext): Unit = {

  }


  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val inports = new PropertyDescriptor()
      .name("inports")
      .displayName("Inports")
      .description("Inports string are separated by commas")
      .defaultValue("")
      .required(true)
    descriptor = inports :: descriptor


    val outports = new PropertyDescriptor().name("outports")
      .displayName("outports")
      .description("Output ports string with comma")
      .defaultValue("")
      .required(true)
    descriptor = outports :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/script/ShellExecutor.png")
  }

  override def getGroup(): List[String] = {
    List()
  }


}
