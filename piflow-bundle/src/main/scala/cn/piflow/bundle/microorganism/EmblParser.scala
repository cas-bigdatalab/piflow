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

class EmblParser extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Parsing EMBL type data"
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

    var jsonStr: String =""

    var bis: BufferedInputStream =null

    //    var df: DataFrame =null
    //    var d: DataFrame =null
    //    var jsonRDD: RDD[String] =null

    inDf.collect().foreach(row => {

      var n : Int =0
      pathStr = row.get(0).asInstanceOf[String]

      println("#############################################")
      println("start parser ^^^" + pathStr)
      println("#############################################")

//      if(pathStr.equals("hdfs://10.0.88.70:9000/yqd/weishengwu/refseq/bacteria.1.genomic.gbff")) {


        var fdis: FSDataInputStream = fs.open(new Path(pathStr))
        //        var fdis: FSDataInputStream = fs.open(new Path("hdfs://10.0.88.70:9000/yqd/weishengwu/refseq/bacteria.1.1.genomic.fna.gz"))

        //        var gzipout: GZIPInputStream = new GZIPInputStream(fdis)

        //        var br: BufferedReader = new BufferedReader(new InputStreamReader(gzipout))

        var br: BufferedReader = new BufferedReader(new InputStreamReader(fdis))

        var sequences: RichSequenceIterator = CustomIOTools.IOTools.readEMBLDNA (br, null)

        while (sequences.hasNext) {
          n += 1
          var seq: RichSequence = sequences.nextRichSequence()
          var doc: JSONObject = new JSONObject
          Process.processEMBL_EnsemblSeq(seq, doc)
          jsonStr = doc.toString
          println("start " + n)

          if (n == 1) {
            bis = new BufferedInputStream(new ByteArrayInputStream(("[" + jsonStr).getBytes()))
          } else {
            bis = new BufferedInputStream(new ByteArrayInputStream(("," + jsonStr).getBytes()))
          }

          val buff: Array[Byte] = new Array[Byte](1048576)

          var count: Int = bis.read(buff)
          while (count != -1) {
            fdos.write(buff, 0, count)
            fdos.flush()
            count = bis.read(buff)
          }

          /*   if(n==1){
            jsonRDD = session.sparkContext.makeRDD(jsonStr :: Nil)
            df = session.read.json(jsonRDD)
          }else{
            jsonRDD = session.sparkContext.makeRDD(jsonStr :: Nil)
            d = session.read.json(jsonRDD)
            df = df.union(d.toDF(df.columns:_*))
          }*/

          fdos.flush()
          bis = null
          seq = null
          doc = null
          //          jsonRDD = null
          //          d = null
        }
        bis = new BufferedInputStream(new ByteArrayInputStream(("]").getBytes()))
        val buff: Array[Byte] = new Array[Byte](1048576)

        var count: Int = bis.read(buff)
        while (count != -1) {
          fdos.write(buff, 0, count)
          fdos.flush()
          count = bis.read(buff)
        }
        fdos.flush()
//      }
    })

    fdos.close()

    println("start parser HDFSjsonFile")
    val df: DataFrame = session.read.json(hdfsPathTemporary)

    println("############################################################")
    //    println(df.count())
    df.show(20)
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
    ImageUtil.getImage("/microorganism/EMBL_Logo.svg")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.MicroorganismGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
