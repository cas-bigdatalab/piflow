//package cn.piflow.bundle.memcached
//
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import com.danga.MemCached.{MemCachedClient, SockIOPool}
//import org.apache.spark.rdd.RDD
//import org.apache.spark.sql.{DataFrame, Row, SparkSession}
//import org.apache.spark.sql.types.{StringType, StructField, StructType}
//
//import scala.collection.mutable
//import scala.collection.mutable.ArrayBuffer
//
//
//class GetMemcache extends ConfigurableStop{
//  override val authorEmail: String = "yangqidong@cnic.cn"
//  override val description: String = "Get data from memache"
//  val inportList: List[String] = List(Port.DefaultPort.toString)
//  val outportList: List[String] = List(Port.DefaultPort.toString)
//
//  var servers:String=_            //Server address and port number,If you have multiple servers, use "," segmentation.
//  var keyFile:String=_            //The field you want to use as a query condition
//  var weights:String=_            //Weight of each server
//  var maxIdle:String=_            //Maximum processing time
//  var maintSleep:String=_         //Main thread sleep time
//  var nagle:String=_              //If the socket parameter is true, the data is not buffered and sent immediately.
//  var socketTO:String=_           //Socket timeout during blocking
//  var socketConnectTO:String=_    //Timeout control during connection establishment
//  var schame:String=_            //The fields you want to get
//
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//    val session: SparkSession = pec.get[SparkSession]()
//    val inDF: DataFrame = in.read()
//
//    val mcc: MemCachedClient =getMcc()
//
//    val keyDF = inDF.select(keyFile).toDF()
//    val rs: Array[Row] = keyDF.collect()
//    val keys: Array[String] = rs.map(row => {
//      val str = row.toString()
//      str.substring(1,str.length-1)
//    })
//
//      var schameArr:Array[String] =Array()
//      if(schame.length>0){
//      val schameArrBuff: mutable.Buffer[String] = schame.split(",").map(x => x.trim).toBuffer
//      schameArrBuff.insert(0,keyFile)
//      schameArr = schameArrBuff.toArray
//    }
//
//    var allFileDatas: ArrayBuffer[ArrayBuffer[String]] =ArrayBuffer()
//    for(keyNum <- (0 until keys.size)){
//      val map: Map[String, String] = mcc.get(keys(keyNum)).asInstanceOf[Map[String,String]]
//
//      if(schame.size==0){
//        val arr: Array[String] = map.keySet.toArray
//        val buffer: mutable.Buffer[String] = arr.toBuffer
//        buffer.insert(0,keyFile)
//        schameArr = buffer.toArray
//      }
//
//      var values: ArrayBuffer[String] =ArrayBuffer()
//      values+=keys(keyNum)
//      for(x <- (1 until schameArr.size)){
//        values+=map.get(schameArr(x)).get
//      }
//      allFileDatas+=values
//    }
//
//    val rowList: List[Row] = allFileDatas.map(arr => {Row.fromSeq(arr)}).toList
//    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rowList)
//    val fields: Array[StructField] = schameArr.map(d=>StructField(d,StringType,nullable = true))
//    val s: StructType = StructType(fields)
//    val df: DataFrame = session.createDataFrame(rowRDD,s)
//
//    out.write(df)
//  }
//
//  def getMcc(): MemCachedClient = {
//    val pool: SockIOPool = SockIOPool.getInstance()
//    var serversArr:Array[String]=servers.split(",").map(x => x.trim)
//    pool.setServers(serversArr)
//
//    if(weights.length>0){
//      val weightsArr: Array[Integer] = "3".split(",").map(x=>{new Integer(x.toInt)})
//      pool.setWeights(weightsArr)
//    }
//    if(maxIdle.length>0){
//      pool.setMaxIdle(maxIdle.toInt)
//    }
//    if(maintSleep.length>0){
//      pool.setMaintSleep(maintSleep.toInt)
//    }
//    if(nagle.length>0){
//      pool.setNagle(nagle.toBoolean)
//    }
//    if(socketTO.length>0){
//      pool.setSocketTO(socketTO.toInt)
//    }
//    if(socketConnectTO.length>0){
//      pool.setSocketConnectTO(socketConnectTO.toInt)
//    }
//
//    pool.initialize()
//    val mcc: MemCachedClient = new MemCachedClient()
//    mcc
//  }
//
//  override def setProperties(map: Map[String, Any]): Unit = {
//    servers = MapUtil.get(map,"servers").asInstanceOf[String]
//    keyFile = MapUtil.get(map,"keyFile").asInstanceOf[String]
//    weights = MapUtil.get(map,"weights").asInstanceOf[String]
//    maxIdle = MapUtil.get(map,"maxIdle").asInstanceOf[String]
//    maintSleep = MapUtil.get(map,"maintSleep").asInstanceOf[String]
//    nagle = MapUtil.get(map,"nagle").asInstanceOf[String]
//    socketTO = MapUtil.get(map,"socketTO").asInstanceOf[String]
//    socketConnectTO = MapUtil.get(map,"socketConnectTO").asInstanceOf[String]
//    schame = MapUtil.get(map,"schame").asInstanceOf[String]
//  }
//
//
//  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
//    var descriptor : List[PropertyDescriptor] = List()
//
//    val servers=new PropertyDescriptor().name("servers").displayName("servers").description("Server address and port number,If you have multiple servers, use , segmentation.").defaultValue("").required(true)
//    descriptor = servers :: descriptor
//    val keyFile=new PropertyDescriptor().name("keyFile").displayName("keyFile").description("The field you want to use as a query condition").defaultValue("").required(true)
//    descriptor = keyFile :: descriptor
//    val weights=new PropertyDescriptor().name("weights").displayName("weights").description("Weight of each server,If you have multiple servers, use , segmentation.").defaultValue("").required(false)
//    descriptor = weights :: descriptor
//    val maxIdle=new PropertyDescriptor().name("maxIdle").displayName("maxIdle").description("Maximum processing time").defaultValue("").required(false)
//    descriptor = maxIdle :: descriptor
//    val maintSleep=new PropertyDescriptor().name("maintSleep").displayName("maintSleep").description("Main thread sleep time").defaultValue("").required(false)
//    descriptor = maintSleep :: descriptor
//    val nagle=new PropertyDescriptor().name("nagle").displayName("nagle").description("If the socket parameter is true, the data is not buffered and sent immediately.").defaultValue("").required(false)
//    descriptor = nagle :: descriptor
//    val socketTO=new PropertyDescriptor().name("socketTO").displayName("socketTO").description("Socket timeout during blocking").defaultValue("").required(false)
//    descriptor = socketTO :: descriptor
//    val socketConnectTO=new PropertyDescriptor().name("socketConnectTO").displayName("socketConnectTO").description("Timeout control during connection establishment").defaultValue("").required(false)
//    descriptor = socketConnectTO :: descriptor
//    val schame=new PropertyDescriptor().name("schame").displayName("schame").description("The fields you want to get.If you have multiple servers, use , segmentation.").defaultValue("").required(true)
//    descriptor = schame :: descriptor
//
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/memcache/GetMemcache.png")
//  }
//
//  override def getGroup(): List[String] = {
//    List(StopGroup.Memcache.toString)
//  }
//
//  override def initialize(ctx: ProcessContext): Unit = {
//
//  }
//
//}
