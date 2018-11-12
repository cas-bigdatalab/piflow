package cn.piflow.bundle.mongodb

import java.util

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroupEnum}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import com.mongodb.client.{FindIterable, MongoCollection, MongoCursor, MongoDatabase}
import com.mongodb.{MongoClient, MongoCredential, ServerAddress}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.types.{StringType, StructField, StructType}
import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.bson.Document

import scala.collection.mutable.ArrayBuffer


class GetMongo extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "get data from mongodb"
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var addresses:String=_
  var credentials:String=_
  var dataBase:String=_
  var collection:String=_
  var sql:String=_

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session: SparkSession = pec.get[SparkSession]()
//注入链接地址
    var addressesArr: util.ArrayList[ServerAddress] = new util.ArrayList[ServerAddress]()
    val ipANDport: Array[String] = addresses.split(",")
    for(x <- (0 until ipANDport.size)){
      if(x%2==0){
        addressesArr.add(new ServerAddress(ipANDport(x),ipANDport(x+1).toInt))
      }
    }

//注入链接凭证
    var credentialsArr: util.ArrayList[MongoCredential] = new util.ArrayList[MongoCredential]()
    if(credentials.length!=0){
      val name_database_password: Array[String] = credentials.split(",")
      for(x <- (0 until name_database_password.size)){
        if(x%3==0){
          credentialsArr.add(MongoCredential.createScramSha1Credential(name_database_password(x),name_database_password(x+1),name_database_password(x+2).toCharArray))
        }
      }
    }

//链接到数据库和表
    val client: MongoClient = new MongoClient(addressesArr,credentialsArr)
    val db: MongoDatabase = client.getDatabase(dataBase)
    val col: MongoCollection[Document] = db.getCollection(collection)

//获取表内全部数据   得到迭代器
    val documents: FindIterable[Document] = col.find()
    val dataIterator: MongoCursor[Document] = documents.iterator()
    var document: Document =null
//记录字段名字
    var fileNamesArr: Array[String] =Array()
//记录所有数据
    var rowArr:ArrayBuffer[ArrayBuffer[String]]=ArrayBuffer()
//遍历数据
    while (dataIterator.hasNext){
      //记录每一条数据
      var dataArr:ArrayBuffer[String]=ArrayBuffer()
      document = dataIterator.next()
      val fileNamesSet: util.Set[String] = document.keySet()
      fileNamesArr = fileNamesSet.toArray.map(_.asInstanceOf[String])
      for(x <- (1 until fileNamesArr.size)){
        dataArr+=document.get(fileNamesArr(x)).toString
      }
      rowArr+=dataArr
    }

//生成df
    var names:ArrayBuffer[String]=ArrayBuffer()
    for(n <- (1 until fileNamesArr.size )){
      names += fileNamesArr(n)
    }
    val fields: Array[StructField] = names.toArray.map(d=>StructField(d.toString,StringType,nullable = true))
    val schema: StructType = StructType(fields)

    val rows: ArrayBuffer[Row] = rowArr.map(r => {
      Row.fromSeq(r.toSeq)
    })
    val rdd: RDD[Row] = session.sparkContext.makeRDD(rows)
    val df: DataFrame = session.createDataFrame(rdd,schema)

    df.createTempView(collection)
    if(sql.length==0){
      sql="select * from "+collection
    }
    val finalDF: DataFrame = session.sql(sql).toDF()

    println("######################################")
    finalDF.show(20)
    println("######################################")

    out.write(finalDF)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    addresses = MapUtil.get(map,"addresses").asInstanceOf[String]
    credentials = MapUtil.get(map,"credentials").asInstanceOf[String]
    dataBase = MapUtil.get(map,"dataBase").asInstanceOf[String]
    collection = MapUtil.get(map,"collection").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]

  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val addresses=new PropertyDescriptor().name("addresses").displayName("addresses").description("Database connection address, you need to fill in: IP1, port 1, IP2, port 2").defaultValue("").required(true)
    descriptor = addresses :: descriptor
    val credentials=new PropertyDescriptor().name("credentials").displayName("credentials").description("To connect credentials, you need to write like this: user name 1, table name 1, password 1, username 2, table name 2, password 2").defaultValue("").required(false)
    descriptor = credentials :: descriptor
    val dataBase=new PropertyDescriptor().name("dataBase").displayName("dataBase").description("data base").defaultValue("").required(true)
    descriptor = dataBase :: descriptor
    val collection=new PropertyDescriptor().name("collection").displayName("collection").description("form").defaultValue("").required(true)
    descriptor = collection :: descriptor
    val sql=new PropertyDescriptor().name("sql").displayName("sql").description("We take the collection you need as a form, and you can find what you want.").defaultValue("").required(false)
    descriptor = sql :: descriptor
    descriptor
  }
  override def getIcon(): Array[Byte] =  {
    ImageUtil.getImage("mongoDB/mongodb.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.Mongodb.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = { }

}
