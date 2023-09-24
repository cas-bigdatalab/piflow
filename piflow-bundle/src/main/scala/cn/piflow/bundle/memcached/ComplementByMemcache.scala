//package cn.piflow.bundle.memcached
//
//import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
//import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
//import cn.piflow.conf.bean.PropertyDescriptor
//import cn.piflow.conf.util.{ImageUtil, MapUtil}
//import com.danga.MemCached.{MemCachedClient, SockIOPool}
//import org.apache.spark.rdd.RDD
//import org.apache.spark.sql.types.{StringType, StructField, StructType}
//import org.apache.spark.sql.{DataFrame, Row, SparkSession}
//
//import scala.collection.mutable
//
//class ComplementByMemcache extends ConfigurableStop {
//  override val authorEmail: String = "yangqidong@cnic.cn"
//  override val description: String = "Complement by Memcache"
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
//  var replaceField:String=_            //The fields you want to get
//
//
//  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
//    val session: SparkSession = pec.get[SparkSession]()
//    val inDF: DataFrame = in.read()
//
//    val mcc: MemCachedClient =getMcc()
//
//    val replaceFields: mutable.Buffer[String] = replaceField.split(",").map(x => x.trim).toBuffer
//
//    val rowArr: Array[Row] = inDF.collect()
//    val fileNames: Array[String] = inDF.columns
//    val data: Array[Map[String, String]] = rowArr.map(row => {
//      var rowStr: String = row.toString().substring(1,row.toString().length-1)
//      val dataARR: Array[String] = rowStr.split(",").map(x => x.trim)
//      var map: Map[String, String] = Map()
//      for (x <- (0 until fileNames.size)) {
//        map += (fileNames(x) -> dataARR(x))
//      }
//      map
//    })
//
//    val finalData: Array[Map[String, String]] = data.map(eachData => {
//      var d: Map[String, String] = eachData
//      val anyRef: AnyRef = mcc.get(d.get(keyFile).get)
//      if(anyRef.getClass.toString.equals("class scala.Some")){
//        val map: Map[String, String] = anyRef.asInstanceOf[Map[String, String]]
//        for (f <- replaceFields) {
//          d += (f -> map.get(f).get.toString)
//        }
//      }
//      d
//    })
//
//    var arrKey: Array[String] = Array()
//    val rows: List[Row] = finalData.toList.map(map => {
//      arrKey = map.keySet.toArray
//      val values: Iterable[AnyRef] = map.values
//      val seq: Seq[AnyRef] = values.toSeq
//      val seqSTR: Seq[String] = values.toSeq.map(x=>x.toString)
//      val row: Row = Row.fromSeq(seqSTR)
//      row
//    })
//    val rowRDD: RDD[Row] = session.sparkContext.makeRDD(rows)
//
//    val fields: Array[StructField] = arrKey.map(d=>StructField(d,StringType,nullable = true))
//    val schema: StructType = StructType(fields)
//    val df: DataFrame = session.createDataFrame(rowRDD,schema)
//
//    out.write(df)
//  }
//
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
//    replaceField = MapUtil.get(map,"replaceField").asInstanceOf[String]
//
//  }
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
//    val replaceField=new PropertyDescriptor().name("replaceField").displayName("replaceField").description("The field you want to replace .  use , segmentation.").defaultValue("").required(true)
//    descriptor = replaceField :: descriptor
//
//    descriptor
//  }
//
//  override def getIcon(): Array[Byte] = {
//    ImageUtil.getImage("icon/memcache/ComplementByMemcache.png")
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
