package cn.piflow.bundle.microorganism

import java.io._


import cn.piflow.bundle.microorganism.util.{CustomIOTools, Process}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.ImageUtil
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataInputStream, FSDataOutputStream, FileSystem, Path}
import org.apache.spark.sql.{DataFrame,  SparkSession}
import org.json.JSONObject


class GenBankData extends ConfigurableStop{
  val authorEmail: String = "ygang@cnic.cn"
  val description: String = " Parsing GenBank type data"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)


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

    val hdfsPathTemporary:String = hdfsUrl+"/microoCache/genbank/genbankcach.json"
    val path: Path = new Path(hdfsPathTemporary)
    if(fs.exists(path)){
      fs.delete(path)
    }
    fs.create(path).close()


    var fdosOut: FSDataOutputStream = fs.append(path)
    var jsonStr: String =""
    var bisIn: BufferedInputStream =null


    inDf.collect().foreach(row=>{
      pathStr = row.get(0).asInstanceOf[String]
      var fdis: FSDataInputStream = fs.open(new Path(pathStr))
      val br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))

      val sequenceIterator = CustomIOTools.IOTools.readGenbankDNA(br, null)

      var doc: JSONObject = null
      var count = 0
      while (sequenceIterator.hasNext) {
        count += 1
        doc = new JSONObject

        val seq = sequenceIterator.nextRichSequence()

        Process.processSingleSequence(seq, doc)


        bisIn = new BufferedInputStream(new ByteArrayInputStream((doc.toString+"\n").getBytes()))

        val buff: Array[Byte] = new Array[Byte](1048576)
        var num: Int = bisIn.read(buff)
        while (num != -1) {
          fdosOut.write(buff, 0, num)
          fdosOut.flush()
          num = bisIn.read(buff)
        }

        fdosOut.flush()
        bisIn = null

      }
    })

    fdosOut.close()
    println("start parser HDFSjsonFile")
    val df: DataFrame = spark.read.json(hdfsPathTemporary)

    df.schema.printTreeString()
    out.write(df)


  }


  def setProperties(map: Map[String, Any]): Unit = {
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/microorganism/GenbankData.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup.toString)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }


}
