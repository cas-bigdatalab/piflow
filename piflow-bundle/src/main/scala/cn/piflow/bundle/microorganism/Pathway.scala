package cn.piflow.bundle.microorganism

import java.io.{BufferedReader, InputStreamReader, OutputStreamWriter}

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.JSONObject


class Pathway extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parse Pathway data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)


  var cachePath:String = _
  def setProperties(map: Map[String, Any]): Unit = {
    cachePath=MapUtil.get(map,key="cachePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val cachePath = new PropertyDescriptor().name("cachePath").displayName("cachePath").description("Temporary Cache File Path")
      .defaultValue("/pathway").required(true)
    descriptor = cachePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/Pathway.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Algorithms_OntologyAnnotations)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val inDf: DataFrame = in.read()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]

    val configuration: Configuration = new Configuration()
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)


    val hdfsPathTemporary = hdfsUrl+cachePath+"/pathwayCache/pathwayCache.json"
    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()
    val hdfsWriter: OutputStreamWriter = new OutputStreamWriter(fs.append(path))

    var fdis: FSDataInputStream = null
    var br: BufferedReader = null
    var doc: JSONObject = null
    var hasAnotherSequence:Boolean = true

    inDf.collect().foreach(row => {
      pathStr = row.get(0).asInstanceOf[String]

      fdis = fs.open(new Path(pathStr))
      br = new BufferedReader(new InputStreamReader(fdis))
      var count = 0
      while (hasAnotherSequence) {
          count += 1
          doc = new JSONObject
          hasAnotherSequence = util.KeggPathway.process(br, doc)

          doc.write(hdfsWriter)
          hdfsWriter.write("\n")
        }
      br.close()
      fdis.close()
    })
    hdfsWriter.close()

    val df: DataFrame = pec.get[SparkSession]().read.json(hdfsPathTemporary)
    df.schema.printTreeString()
    println(df.count)

    out.write(df)

  }
}
