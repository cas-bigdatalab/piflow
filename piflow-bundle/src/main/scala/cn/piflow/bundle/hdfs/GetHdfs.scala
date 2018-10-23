package cn.piflow.bundle.hdfs

import cn.piflow._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import org.apache.spark.sql.SparkSession


class GetHdfs extends ConfigurableStop{
  override val authorEmail: String = "ygang@cmic.com"
  override val description: String = "write dataframe data from hdfs"

  var hdfsUrl : String=_
  var hdfsPath :String= _
  var types :String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc= spark.sparkContext
    import spark.implicits._

    println(hdfsPath+"gggggggggggggggggggggggg ---getHdfs---txt")

    val path = hdfsUrl+hdfsPath

//    val array = hdfsPath.split(",")
//
//    val buffer = new StringBuffer()
//    for (i<- 0 until array.length) {
//      if (i== array.length-1){
//        buffer.append(hdfsUrl+array(i))
//      } else {
//        buffer.append(hdfsUrl+array(i)+",")
//      }
//    }
    // println(buffer.toString)

      if (types == "json") {
        val rdd = spark.read.json(path)
        rdd.show()
        rdd.schema.printTreeString()
        out.write(rdd)

      } else if (types == "csv") {

        val rdd = spark.read.csv(path)
        rdd.show()
        rdd.schema.printTreeString()
        out.write(rdd)

      }else if (types == "parquet") {
        val rdd = spark.read.csv(path)
        rdd.show()
        rdd.schema.printTreeString()
        out.write(rdd)

      }
      else {
        val rdd = sc.textFile(path)
        val outDf = rdd.toDF("txt")
        outDf.schema.printTreeString()
        outDf.show()
        out.write(outDf)

    }




//    val rdd = spark.read.text("hdfs://10.0.86.89:9000/yg/test/hdf1.txt")
//    rdd.show()
//    rdd.schema.printTreeString()
  //  println( rdd.count())
    // val rdd = ssc.read.load("hdfs://10.0.86.89:9000/yg/test/hdf1.txt")


  }
  override def setProperties(map: Map[String, Any]): Unit = {
    hdfsUrl = MapUtil.get(map,key="hdfsUrl").asInstanceOf[String]
    hdfsPath = MapUtil.get(map,key="hdfsPath").asInstanceOf[String]
    types = MapUtil.get(map,key="types").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hdfsPath = new PropertyDescriptor().name("hdfsPath").displayName("hdfsPath").defaultValue("").required(true)
    val hdfsUrl = new PropertyDescriptor().name("hdfsUrl").displayName("hdfsUrl").defaultValue("").required(true)
    val types = new PropertyDescriptor().name("types").displayName("types").defaultValue("txt,parquet,csv,json").required(true)
    descriptor = types :: descriptor
    descriptor = hdfsPath :: descriptor
    descriptor = hdfsUrl :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("hdfs.jpg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.HdfsGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

  override val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)
}
