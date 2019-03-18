package cn.piflow.bundle.microorganism

import java.io._

import cn.piflow.bundle.microorganism.util.{CustomIOTools, Process}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.biojavax.bio.seq.{RichSequence, RichSequenceIterator}
import org.json.JSONObject

class RefseqData extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parse Refseq_genome data"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)



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

    val hdfsPathTemporary:String = hdfsUrl+"/Refseq_genomeParser_temporary.json"
    val path: Path = new Path(hdfsPathTemporary)

    if(fs.exists(path)){
      fs.delete(path)
    }

    fs.create(path).close()
    var fdos: FSDataOutputStream = fs.append(path)
    val buff: Array[Byte] = new Array[Byte](1048576)

    var jsonStr: String =""

    var bis: BufferedInputStream =null

    inDf.collect().foreach(row => {

      var n : Int =0
      pathStr = row.get(0).asInstanceOf[String]


      var fdis: FSDataInputStream = fs.open(new Path(pathStr))

      var br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))

      var sequences: RichSequenceIterator = CustomIOTools.IOTools.readGenbankProtein(br, null)

      while (sequences.hasNext) {
        n += 1
        var seq: RichSequence = sequences.nextRichSequence()
        var doc: JSONObject = new JSONObject
        Process.processSingleSequence(seq, doc)
        jsonStr = doc.toString
        println("start " + n)

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
        seq = null
        doc = null
      }

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

    println("start parser HDFSjsonFile")
    val df: DataFrame = session.read.json(hdfsPathTemporary)

    out.write(df)


  }

  override def setProperties(map: Map[String, Any]): Unit = {

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] ={
  var descriptor : List[PropertyDescriptor] = List()
  descriptor
}

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/RefseqData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
