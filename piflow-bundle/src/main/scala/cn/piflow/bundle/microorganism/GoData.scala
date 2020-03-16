package cn.piflow.bundle.microorganism

import java.io._
import java.util.Iterator
import java.util.regex.{Matcher, Pattern}

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.json.JSONObject


class GoData extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = "Parse Go data"
  val inportList: List[String] = List(Port.DefaultPort.toString)
  val outportList: List[String] = List(Port.DefaultPort.toString)

  var cachePath:String = _

  var tv:Pattern = Pattern.compile("(\\S+):\\s(.+)")
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

    val hdfsPathTemporary = hdfsUrl+cachePath+"/godataCache/godataCache.json"

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
      var  i =0
      while (i<30){
        br.readLine()
        i+=1
      }
      var obj = new JSONObject()
      var count= 0
      while ((line = br.readLine()) !=null && line !=null  && count<10){
        val m: Matcher = tv.matcher(line)
        if (line.startsWith("[")){
          if (line .equals("[Term]")){
            obj.append("stanza_name","Term")
          } else if (line.equals("[Typedef]")){
            obj.append("stanza_name","Typedef")
          } else if (line.equals("[Instance]")){
            obj.append("stanza_name","Instance")
          }
        } else if (m.matches()){
          obj.append(m.group(1),m.group(2))
        } else if ( line.equals("")){
          val keyIterator: Iterator[String] = obj.keys()
          while (keyIterator.hasNext){
            val key = keyIterator.next()
            var value = ""
            for (i <- 0 until obj.getJSONArray(key).length() ){
              value += (";" + obj.getJSONArray(key).get(i).toString)
            }
            obj.put(key,value.substring(1))
          }
          count += 1

          obj.write(hdfsWriter)
          hdfsWriter.write("\n")

          obj= new JSONObject()
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
    val cachePath = new PropertyDescriptor().name("cachePath").displayName("cachePath").description("Temporary Cache File Path")
      .defaultValue("/goData").required(true)
    descriptor = cachePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/GoData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
