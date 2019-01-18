package cn.piflow.bundle.microorganism

import java.io.{BufferedInputStream, BufferedReader, ByteArrayInputStream, InputStreamReader}

import cn.piflow.bundle.microorganism.util.ParserGff3Data
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.biojavax.bio.seq.{RichSequence, RichSequenceIterator}
import org.json.JSONObject

class Ensembl_gff3Parser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parsing ensembl type data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] ={
    var descriptor : List[PropertyDescriptor] = List()
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("microorganism/png/Ensembl.png")
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
    var pathStr: String = ""
    var hdfsUrl:String=""
    try{
      pathStr =inDf.take(1)(0).get(0).asInstanceOf[String]
      val pathARR: Array[String] = pathStr.split("\\/")

      for (x <- (0 until 3)){
        hdfsUrl+=(pathARR(x) +"/")
      }
    }catch {
      case e:Exception => throw new Exception("Path error")
    }

    configuration.set("fs.defaultFS",hdfsUrl)
    var fs: FileSystem = FileSystem.get(configuration)

    val hdfsPathTemporary:String = hdfsUrl+"/Refseq_genomeParser_temporary.json"
    val path: Path = new Path(hdfsPathTemporary)

    if(fs.exists(path)){
      fs.delete(path)
    }

    fs.create(path).close()
    var fdos: FSDataOutputStream = fs.append(path)
    val buff: Array[Byte] = new Array[Byte](1048576)

    val parser: ParserGff3Data = new ParserGff3Data

    var bis: BufferedInputStream =null
    var fdis: FSDataInputStream =null
    var br: BufferedReader = null
    var sequences: RichSequenceIterator = null
    var doc: JSONObject = null
    var seq: RichSequence = null
    var jsonStr: String = ""
    var n:Int=0
    inDf.collect().foreach(row => {
      pathStr = row.get(0).asInstanceOf[String]
      println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   start parser ^^^" + pathStr)
      fdis = fs.open(new Path(pathStr))
      br = new BufferedReader(new InputStreamReader(fdis))
      var eachStr:String=null

      while((eachStr = br.readLine()) != null && eachStr != null){
        doc = parser.parserGff3(eachStr)
        jsonStr = doc.toString
        if(jsonStr.length > 2){
          n +=1
          println("start   " + n + "   String")
          if (n == 1) {
            bis = new BufferedInputStream(new ByteArrayInputStream(("[" + jsonStr).getBytes()))
          } else {
            bis = new BufferedInputStream(new ByteArrayInputStream(("," + jsonStr).getBytes()))
          }
          var count: Int = bis.read(buff)
          while (count != -1) {
            fdos.write(buff, 0, count)
            fdos.flush()
            count = bis.read(buff)
          }
          fdos.flush()

          bis = null
          doc = null
          seq = null
          jsonStr = ""
        }

      }
      sequences = null
      br = null
      fdis =null
      pathStr = null
    })
    bis = new BufferedInputStream(new ByteArrayInputStream(("]").getBytes()))

    var count: Int = bis.read(buff)
    while (count != -1) {
      fdos.write(buff, 0, count)
      fdos.flush()
      count = bis.read(buff)
    }
    fdos.flush()
    bis.close()
    fdos.close()

    val df: DataFrame = session.read.json(hdfsPathTemporary)

    out.write(df)
  }
}
