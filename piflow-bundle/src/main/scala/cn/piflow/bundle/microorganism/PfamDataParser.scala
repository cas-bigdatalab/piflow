package cn.piflow.bundle.microorganism

import java.io.{BufferedInputStream, BufferedReader, ByteArrayInputStream, InputStreamReader}

import cn.piflow.bundle.microorganism.util.{CustomIOTools, Pfam, Process}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.biojavax.bio.seq.{RichSequence, RichSequenceIterator}
import org.json.JSONObject

class PfamDataParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "pfam type data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)


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

    var bis: BufferedInputStream =null
    var fdis: FSDataInputStream =null
    var br: BufferedReader = null
    var sequences: RichSequenceIterator = null
    var doc: JSONObject = null
    var seq: RichSequence = null
    var hasAnotherSequence : Boolean=true
    var jsonStr: String = ""
    var n:Int=0
    inDf.collect().foreach(row => {
      pathStr = row.get(0).asInstanceOf[String]
      println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   start parser ^^^" + pathStr)
      fdis = fs.open(new Path(pathStr))
      br = new BufferedReader(new InputStreamReader(fdis))

      while( hasAnotherSequence  &&  n < 1000 ){
        n += 1

        doc = new JSONObject()
        hasAnotherSequence = Pfam.process(br,doc)

        jsonStr = doc.toString
        println("start " + n + "String\\\n" /*+ jsonStr*/)

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

    //    println("start parser HDFSjsonFile   --------------------")
    val df: DataFrame = session.read.json(hdfsPathTemporary)

    println("############################################################")
    println(df.count())
    df.show(20)
    df.printSchema()
    println("############################################################")
    out.write(df)
  }


  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] ={
    var descriptor : List[PropertyDescriptor] = List()
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("/microorganism/pfam.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
