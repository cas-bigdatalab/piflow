package cn.piflow.bundle.Hbase



import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.hbase.{HBaseConfiguration, HTableDescriptor}
import org.apache.hadoop.hbase.client.{HBaseAdmin, Result, Scan}
import org.apache.hadoop.hbase.io.ImmutableBytesWritable
import org.apache.hadoop.hbase.mapreduce.TableInputFormat
import org.apache.hadoop.hbase.protobuf.ProtobufUtil
import org.apache.hadoop.hbase.util.{Base64, Bytes}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.SparkSession

class GetHbase extends ConfigurableStop {

  val authorEmail: String = "ygang@cnic.cn"
  override val inportList: List[String] = List(PortEnum.NonePort.toString)
  override val outportList: List[String] = List(PortEnum.DefaultPort.toString)
  override val description: String = "get data from hbase "



  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]()
    val sc = spark.sparkContext

    val tableName = "person"
    val configuration: Configuration = HBaseConfiguration.create()
    // 使用 configuration 配置参数
    configuration.set("hbase.zookeeper.quorum",
      "10.0.86.89,10.0.86.90,10.0.86.91")
    //configuration.set("hbase.zookeeper.quorum","master,slave1,slave2")
    configuration.set("hbase.zookeeper.property.clientPort","2181")
    configuration.set("hbase.defaults.for.version.skip","true")
    configuration.set(TableInputFormat.INPUT_TABLE,tableName)

    //    configuration.set("spark.serializer","org.apache.spark.serializer.KrySerializer")



    val kvRdd: RDD[(ImmutableBytesWritable, Result)] = sc.newAPIHadoopRDD(configuration, classOf[TableInputFormat],classOf[ImmutableBytesWritable],classOf[Result])

    kvRdd.foreach(println)
    kvRdd.foreach(x=>{
      val result = x._2
      println(s"sname:${Bytes.toString(result.getValue("name".getBytes()
        ,"name".getBytes()))}")
    })




    //println(kvRdd.count())


    //    var scan = new Scan()
    //    scan.addFamily(Bytes.toBytes("row1"))
    //    scan.setCacheBlocks(false)
    //    val proto = ProtobufUtil.toScan(scan)
    //
    //    val scanToString = Base64.encodeBytes(proto.toByteArray)
    //    configuration.set(TableInputFormat.SCAN,scanToString)

    //val hbaseRdd =sc.newAPIHadoopRDD(configuration, classOf[TableInputFormat],classOf[ImmutableBytesWritable],classOf[Result])


    // println(hbaseRdd.count())
  }


  def initialize(ctx: ProcessContext): Unit = {

  }

  def setProperties(map : Map[String, Any]): Unit = {
    //    es_nodes=MapUtil.get(map,key="es_nodes").asInstanceOf[String]
    //    port=MapUtil.get(map,key="port").asInstanceOf[String]
    //    es_index=MapUtil.get(map,key="es_index").asInstanceOf[String]
    //    es_type=MapUtil.get(map,key="es_type").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val es_nodes = new PropertyDescriptor().name("es_nodes").displayName("REDIS_HOST").defaultValue("").required(true)
    val port = new PropertyDescriptor().name("port").displayName("PORT").defaultValue("").required(true)
    val es_index = new PropertyDescriptor().name("es_index").displayName("ES_INDEX").defaultValue("").required(true)
    val es_type = new PropertyDescriptor().name("es_type").displayName("ES_TYPE").defaultValue("").required(true)


    descriptor = es_nodes :: descriptor
    descriptor = port :: descriptor
    descriptor = es_index :: descriptor
    descriptor = es_type :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hbase/GetHbase.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HbaseGroup.toString)
  }

}
