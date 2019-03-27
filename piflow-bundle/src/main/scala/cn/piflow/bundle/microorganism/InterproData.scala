package cn.piflow.bundle.microorganism

import java.io._

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.{JSONObject, XML}


class InterproData extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse Interpro data"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var cachePath:String = _

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext
    val inDf= in.read()

    val configuration: Configuration = new Configuration()
    var pathStr: String =inDf.take(1)(0).get(0).asInstanceOf[String]
    val pathARR: Array[String] = pathStr.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){
      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary = hdfsUrl+cachePath+"/interproCache/interproCache.json"

    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()

    val hdfsWriter: OutputStreamWriter = new OutputStreamWriter(fs.append(path))

    inDf.collect().foreach(row => {
      pathStr = row.get(0).asInstanceOf[String]

      var fdis: FSDataInputStream = fs.open(new Path(pathStr))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))
      var line: String = null
      var xml = ""
      var  i = 0
      while (i<26){
        br.readLine()
        i+=1
      }
      var count = 0
      var abstraction:String = null
      var doc: JSONObject = null
      while ((line = br.readLine()) != null && line !=null ){
        xml += line
        if (line .indexOf("</interpro>") != -1){
          count += 1
          doc = XML.toJSONObject(xml).getJSONObject("interpro")

          val id = doc.getString("id")
          if (doc.has("abstract")){
            abstraction = doc.get("abstract").toString
            doc.put("abstract",abstraction)
          }
          if (doc.get("pub_list") == ""){
            doc.remove("pub_list")
          }

          doc.write(hdfsWriter)
          hdfsWriter.write("\n")

          xml = ""
        }
      }
      br.close()
      fdis.close()
    })

    hdfsWriter.close()

    println("start parser HDFSjsonFile")
    val df: DataFrame = spark.read.json(hdfsPathTemporary)

    out.write(df)

  }

  def setProperties(map: Map[String, Any]): Unit = {
    cachePath=MapUtil.get(map,key="cachePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val cachePath = new PropertyDescriptor().name("cachePath").displayName("cachePath").defaultValue("/interpro").required(true)
    descriptor = cachePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/InterproData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
