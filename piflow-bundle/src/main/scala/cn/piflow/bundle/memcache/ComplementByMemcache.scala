package cn.piflow.bundle.memcache

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import com.danga.MemCached.{MemCachedClient, SockIOPool}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}

import scala.collection.mutable
import scala.collection.mutable.ArrayBuffer

class ComplementByMemcache extends ConfigurableStop {
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Supplement to Memcache query data"
  val inportList: List[String] = List(PortEnum.DefaultPort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var servers:String=_            //服务器地址和端口号Server address and port number,If you have multiple servers, use "," segmentation.
  var keyFile:String=_            //你想用来作为查询条件的字段The field you want to use as a query condition
  var weights:String=_            //每台服务器的权重Weight of each server
  var maxIdle:String=_            //最大处理时间Maximum processing time
  var maintSleep:String=_         //主线程睡眠时间Main thread sleep time
  var nagle:String=_              //socket参数，若为true，则写数据时不缓冲立即发送If the socket parameter is true, the data is not buffered and sent immediately.
  var socketTO:String=_           //socket阻塞时候的超时时间Socket timeout during blocking
  var socketConnectTO:String=_    //连接建立时的超时控制Timeout control during connection establishment
  var replaceField:String=_            //你想得到的字段The fields you want to get


  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session: SparkSession = pec.get[SparkSession]()
    val inDF: DataFrame = in.read()

    val mcc: MemCachedClient =getMcc()

    //获得输出df的描述信息
    val replaceFields: mutable.Buffer[String] = replaceField.split(",").toBuffer

    //获取inDF中所有数据到数组，用于更改数据
    val rowArr: Array[Row] = inDF.collect()
    val fileNames: Array[String] = inDF.columns
    val data: Array[Map[String, String]] = rowArr.map(row => {
      var rowStr: String = row.toString().substring(1,row.toString().length-1)
      val dataARR: Array[String] = rowStr.split(",")
      var map: Map[String, String] = Map()
      for (x <- (0 until fileNames.size)) {
        map += (fileNames(x) -> dataARR(x))
      }
      map
    })

    //查询memcache中数据，并按用户需求替换df中数据
    val finalData: Array[Map[String, String]] = data.map(eachData => {
      var d: Map[String, String] = eachData
      val anyRef: AnyRef = mcc.get(d.get(keyFile).get)
      //当从memcache中得到数据时，替换
      if(anyRef.getClass.toString.equals("class scala.Some")){
        val map: Map[String, String] = anyRef.asInstanceOf[Map[String, String]]
        for (f <- replaceFields) {
          d += (f -> map.get(f).get.toString)
        }
      }
      d
    })

    //将schame和数据转换为df
    var arrKey: Array[String] = Array()
    val rows: List[Row] = finalData.toList.map(map => {
      arrKey = map.keySet.toArray
      val values: Iterable[AnyRef] = map.values
      val seq: Seq[AnyRef] = values.toSeq
      val seqSTR: Seq[String] = values.toSeq.map(x=>x.toString)
      val row: Row = Row.fromSeq(seqSTR)
      row
    })
    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows)

    val fields: Array[StructField] = arrKey.map(d=>StructField(d,StringType,nullable = true))
    val schema: StructType = StructType(fields)
    val df: DataFrame = session.createDataFrame(rowRDD,schema)

    println("############################################################")
    df.show()
    println("############################################################")

    out.write(df)
  }


  //得到全局唯一实例
  def getMcc(): MemCachedClient = {
    //获取连接池实例对象
    val pool: SockIOPool = SockIOPool.getInstance()
    //    链接到数据库
    var serversArr:Array[String]=servers.split(",")
    pool.setServers(serversArr)

    if(weights.length>0){
      val weightsArr: Array[Integer] = "3".split(",").map(x=>{new Integer(x.toInt)})
      pool.setWeights(weightsArr)
    }
    if(maxIdle.length>0){
      pool.setMaxIdle(maxIdle.toInt)
    }
    if(maintSleep.length>0){
      pool.setMaintSleep(maintSleep.toInt)
    }
    if(nagle.length>0){
      pool.setNagle(nagle.toBoolean)
    }
    if(socketTO.length>0){
      pool.setSocketTO(socketTO.toInt)
    }
    if(socketConnectTO.length>0){
      pool.setSocketConnectTO(socketConnectTO.toInt)
    }

    pool.initialize()
    //建立全局唯一实例
    val mcc: MemCachedClient = new MemCachedClient()
    mcc
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    servers = MapUtil.get(map,"servers").asInstanceOf[String]
    keyFile = MapUtil.get(map,"keyFile").asInstanceOf[String]
    weights = MapUtil.get(map,"weights").asInstanceOf[String]
    maxIdle = MapUtil.get(map,"maxIdle").asInstanceOf[String]
    maintSleep = MapUtil.get(map,"maintSleep").asInstanceOf[String]
    nagle = MapUtil.get(map,"nagle").asInstanceOf[String]
    socketTO = MapUtil.get(map,"socketTO").asInstanceOf[String]
    socketConnectTO = MapUtil.get(map,"socketConnectTO").asInstanceOf[String]
    replaceField = MapUtil.get(map,"replaceField").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val servers=new PropertyDescriptor().name("servers").displayName("servers").description("Server address and port number,If you have multiple servers, use , segmentation.").defaultValue("").required(true)
    descriptor = servers :: descriptor
    val keyFile=new PropertyDescriptor().name("keyFile").displayName("keyFile").description("The field you want to use as a query condition").defaultValue("").required(true)
    descriptor = keyFile :: descriptor
    val weights=new PropertyDescriptor().name("weights").displayName("weights").description("Weight of each server,If you have multiple servers, use , segmentation.").defaultValue("").required(false)
    descriptor = weights :: descriptor
    val maxIdle=new PropertyDescriptor().name("maxIdle").displayName("maxIdle").description("Maximum processing time").defaultValue("").required(false)
    descriptor = maxIdle :: descriptor
    val maintSleep=new PropertyDescriptor().name("maintSleep").displayName("maintSleep").description("Main thread sleep time").defaultValue("").required(false)
    descriptor = maintSleep :: descriptor
    val nagle=new PropertyDescriptor().name("nagle").displayName("nagle").description("If the socket parameter is true, the data is not buffered and sent immediately.").defaultValue("").required(false)
    descriptor = nagle :: descriptor
    val socketTO=new PropertyDescriptor().name("socketTO").displayName("socketTO").description("Socket timeout during blocking").defaultValue("").required(false)
    descriptor = socketTO :: descriptor
    val socketConnectTO=new PropertyDescriptor().name("socketConnectTO").displayName("socketConnectTO").description("Timeout control during connection establishment").defaultValue("").required(false)
    descriptor = socketConnectTO :: descriptor
    val replaceField=new PropertyDescriptor().name("replaceField").displayName("replaceField").description("The field you want to replace .  use , segmentation.").defaultValue("").required(true)
    descriptor = replaceField :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("memcache/Memcache.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.Memcache.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}
