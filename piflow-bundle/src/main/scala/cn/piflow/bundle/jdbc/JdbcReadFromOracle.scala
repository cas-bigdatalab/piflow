package cn.piflow.bundle.jdbc

import java.sql.{Connection, DriverManager, PreparedStatement, ResultSet}

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql._
import org.apache.spark.sql.types.{StringType, StructField, StructType}

import scala.collection.mutable.ArrayBuffer

class JdbcReadFromOracle extends ConfigurableStop{

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "read from oracle."
  val inportList: List[String] = List(PortEnum.NonePort.toString)
  val outportList: List[String] = List(PortEnum.DefaultPort.toString)

  var url:String = _
  var user:String = _
  var password:String = _
  var sql:String = _
  var fileNamesString:String=_


  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session = pec.get[SparkSession]()

    Class.forName("oracle.jdbc.driver.OracleDriver")
    val con: Connection = DriverManager.getConnection(url,user,password)
    val pre: PreparedStatement = con.prepareStatement(sql)
    val rs: ResultSet = pre.executeQuery()


    val filedNames: Array[String] = fileNamesString.split(",")
    var rowsArr:ArrayBuffer[ArrayBuffer[String]]=ArrayBuffer()
    while (rs.next()){
      var rowArr:ArrayBuffer[String]=ArrayBuffer()
      for(fileName <- filedNames){
        rowArr+=rs.getString(fileName)
      }
      rowsArr+=rowArr
    }

    val fields: Array[StructField] = filedNames.map(d=>StructField(d,StringType,nullable = true))
    val schema: StructType = StructType(fields)

    val rows: List[Row] = rowsArr.toList.map(arr => {
      val row: Row = Row.fromSeq(arr)
      row
    })
    val rdd: RDD[Row] = session.sparkContext.makeRDD(rows)
    val df: DataFrame = session.createDataFrame(rdd,schema)

    println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    df.show(20)
    println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

    out.write(df)




  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
    fileNamesString = MapUtil.get(map,"fileNamesString").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor().name("url").displayName("url").description("The Url, for example jdbc:mysql://127.0.0.1/dbname").defaultValue("").required(true)
    descriptor = url :: descriptor

    val user=new PropertyDescriptor().name("user").displayName("user").description("The user name of database").defaultValue("").required(true)
    descriptor = user :: descriptor

    val password=new PropertyDescriptor().name("password").displayName("password").description("The password of database").defaultValue("").required(true)
    descriptor = password :: descriptor

    val sql=new PropertyDescriptor().name("sql").displayName("sql").description("The sql you want").defaultValue("").required(true)
    descriptor = sql :: descriptor

    val fileNamesString=new PropertyDescriptor().name("fileNamesString").displayName("fileNamesString").description("The name of the field of your SQL statement query, such as: ID, name").defaultValue("").required(true)
    descriptor = fileNamesString :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("JDBC/oracle.jpeg")
  }

  override def getGroup(): List[String] = {
    List(StopGroupEnum.JdbcGroup.toString)
  }


}
