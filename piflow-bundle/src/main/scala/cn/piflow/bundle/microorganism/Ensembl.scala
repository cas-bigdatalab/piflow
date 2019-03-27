package cn.piflow.bundle.microorganism

import java.io._

import cn.piflow.bundle.microorganism.util.ParserGff3Data
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.biojavax.bio.seq.{RichSequence, RichSequenceIterator}
import org.json.JSONObject

class Ensembl extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parse ensembl data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var cachePath:String = _
  def setProperties(map: Map[String, Any]): Unit = {
    cachePath=MapUtil.get(map,key="cachePath").asInstanceOf[String]
  }
  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val cachePath = new PropertyDescriptor().name("cachePath").displayName("cachePath").defaultValue("/ensembl").required(true)
    descriptor = cachePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/Ensembl.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    val session = pec.get[SparkSession]()
    val inDf: DataFrame = in.read()

    val configuration: Configuration = new Configuration()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary = hdfsUrl+cachePath+"/ensemblCache/ensemblCache.json"

    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()

    val hdfsWriter: OutputStreamWriter = new OutputStreamWriter(fs.append(path))

    val parser: ParserGff3Data = new ParserGff3Data
    var fdis: FSDataInputStream =null
    var br: BufferedReader = null
    var doc: JSONObject = null
    var count:Int = 0
    inDf.collect().foreach(row => {
      pathStr = row.get(0).asInstanceOf[String]

      fdis = fs.open(new Path(pathStr))
      br = new BufferedReader(new InputStreamReader(fdis))
      var eachStr:String=null

      while((eachStr = br.readLine()) != null && eachStr != null ){
        doc = parser.parserGff3(eachStr)

        if(doc.toString.length > 2){
          count += 1
          doc.write(hdfsWriter)
          hdfsWriter.write("\n")
        }
      }

      br.close()
      fdis.close()
    })

    hdfsWriter.close()

    out.write(session.read.json(hdfsPathTemporary))
  }
}
