package cn.piflow.bundle.http

import java.io.InputStream
import java.net.{HttpURLConnection, URL}

import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.{FSDataOutputStream, FileSystem, Path}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

class FileDownHDFS extends ConfigurableStop{
  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Download network files to HDFS"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var url_str:String =_
  var savePath:String=_

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()

    val url=new URL(url_str)
    val uc:HttpURLConnection=url.openConnection().asInstanceOf[HttpURLConnection]
    uc.setDoInput(true)
    uc.connect()
    val inputStream:InputStream=uc.getInputStream()

    val buffer=new Array[Byte](1024*1024*10)
    var byteRead= -1



    val configuration: Configuration = new Configuration()


    //          "savePath":"hdfs://10.0.88.70:9000/yqd/hdfstest/dblp.xml.gz"
    //    val hdfsUrl = "hdfs://10.0.88.70:9000"

    val pathARR: Array[String] = savePath.split("\\/")
    var hdfsUrl:String=""
    for (x <- (0 until 3)){

      hdfsUrl+=(pathARR(x) +"/")
    }
    configuration.set("fs.defaultFS",hdfsUrl)
    //    configuration.set("dfs.nameservices", "nameservice1")
    //        configuration.set("dfs.ha.namenodes.nameservice1", "nn1,nn2");
    //        configuration.set("dfs.namenode.rpc-address.nameservice1.nn1", "xxx:8020");
    //        configuration.set("dfs.namenode.rpc-address.nameservice1.nn2", "xxx:8020");
    //        configuration.set("dfs.client.failover.proxy.provider.nameservice1"
    //                ,"org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider");

    //        configuration.addResource("classpath:/hadoop/core-site.xml");
    //        configuration.addResource("classpath:/hadoop/hdfs-site.xml");
    //        configuration.addResource("classpath:/hadoop/mapred-site.xml");



    val fs = FileSystem.get(configuration)
    val fdos: FSDataOutputStream = fs.create(new Path(savePath))


    while(((byteRead=inputStream.read(buffer)) != -1) && (byteRead != -1)){
      fdos.write(buffer,0,byteRead)
      fdos.flush()
    }

    inputStream.close()
    fdos.close()


    var seq:Seq[String]=Seq(savePath)
    val row: Row = Row.fromSeq(seq)
    val list:List[Row]=List(row)
    val rdd: RDD[Row] = spark.sparkContext.makeRDD(list)
    val fields: Array[StructField] =Array(StructField("savePath",StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = spark.createDataFrame(rdd,schema)

    out.write(df)


  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map: Map[String, Any]): Unit = {
    url_str=MapUtil.get(map,key="url_str").asInstanceOf[String]
    savePath=MapUtil.get(map,key="savePath").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val url_str = new PropertyDescriptor().name("url_str").displayName("URL").description("Network address of file").defaultValue("").required(true)
    val savePath = new PropertyDescriptor().name("savePath").displayName("savePath").description("The HDFS path and name you want to save, such as hdfs://10.0.86.89:9000/a/a.gz").defaultValue("").required(true)
    descriptor = url_str :: descriptor
    descriptor = savePath :: descriptor
    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("http.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HttpGroup.toString)
  }


}
