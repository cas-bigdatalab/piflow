package cn.piflow.bundle.jdbc

import java.io._
import java.sql.{Blob, Clob, Connection, Date, DriverManager, NClob, PreparedStatement, ResultSet, SQLXML}

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql._
import org.apache.spark.sql.types._

import scala.collection.mutable.ArrayBuffer

class JdbcReadFromOracle extends ConfigurableStop{

  val authorEmail: String = "yangqidong@cnic.cn"
  val description: String = "Read from oracle"
  val inportList: List[String] = List(Port.DefaultPort)
  val outportList: List[String] = List(Port.DefaultPort)

  var url:String = _
  var user:String = _
  var password:String = _
  var sql:String = _
  var schema:String=_


  def toByteArray(in: InputStream): Array[Byte] = {
    var byteArray:Array[Byte]=new Array[Byte](1024*1024)
    val out: ByteArrayOutputStream = new ByteArrayOutputStream()
    var n:Int=0
    while ((n=in.read(byteArray)) != -1 && (n != -1)){
      out.write(byteArray,0,n)
    }
    val arr: Array[Byte] = out.toByteArray
    out.close()
    arr
  }

  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val session = pec.get[SparkSession]()

    Class.forName("oracle.jdbc.driver.OracleDriver")
    val con: Connection = DriverManager.getConnection(url,user,password)
    val pre: PreparedStatement = con.prepareStatement(sql)
    val rs: ResultSet = pre.executeQuery()


    val filedNames: Array[String] = schema.split(",").map(x => x.trim)
    var rowsArr:ArrayBuffer[ArrayBuffer[Any]]=ArrayBuffer()
    var rowArr:ArrayBuffer[Any]=ArrayBuffer()
    while (rs.next()){
      rowArr.clear()
      for(fileName <- filedNames){
        val name_type: Array[String] = fileName.split("\\.")
        val name: String = name_type(0)
        val typestr: String = name_type(1)
        if(typestr.toUpperCase.equals("BLOB")){
          val blob: Blob = rs.getBlob(name)
          var byteArr : Array[Byte] =Array()
          if(blob != null){
            val stream: InputStream = blob.getBinaryStream
            byteArr = toByteArray(stream)
            stream.close()
          }
          rowArr+=byteArr
        }else if(typestr.toUpperCase.equals("CLOB") || typestr.toUpperCase.equals("XMLTYPE")){
          val clob: Clob = rs.getClob(name)
          var byteArr : Array[Byte] =Array()
          if(clob != null){
            val stream: InputStream = clob.getAsciiStream
            byteArr = toByteArray(stream)
            stream.close()
          }
          rowArr+=byteArr
        }else if(typestr.toUpperCase.equals("NCLOB")){
          val nclob: NClob = rs.getNClob(name)
          var byteArr : Array[Byte] =Array()
          if(nclob != null){
            val stream: InputStream = nclob.getAsciiStream
            byteArr = toByteArray(stream)
            stream.close()
          }
          rowArr+=byteArr
        }else if(typestr.toUpperCase.equals("DATE")){
          val date: Date = rs.getDate(name)
          rowArr+=date
        }else if(typestr.toUpperCase.equals("NUMBER")){
          val int: Int = rs.getInt(name)
          rowArr+=int
        }else{
          rowArr+=rs.getString(name)
        }
      }
      rowsArr+=rowArr
    }

    var nameArrBuff:ArrayBuffer[String]=ArrayBuffer()
    var typeArrBuff:ArrayBuffer[String]=ArrayBuffer()
    filedNames.foreach(x => {
      nameArrBuff+=x.split("\\.")(0)
      typeArrBuff+=x.split("\\.")(1)
    })
    var num:Int=0
    val fields: ArrayBuffer[StructField] = nameArrBuff.map(x => {
      var sf: StructField = null
      val typeName: String = typeArrBuff(num)
      if (typeName.toUpperCase.equals("BLOB") || typeName.toUpperCase.equals("CLOB") || typeName.toUpperCase.equals("NCLOB") || typeName.toUpperCase.equals("XMLTYPE")) {
        sf = StructField(x, DataTypes.createArrayType(ByteType), nullable = true)
      }else if( typeName.toUpperCase.equals("DATE")) {
        sf = StructField(x, DateType, nullable = true)
      }else if( typeName.toUpperCase.equals("NUMBER")) {
        sf = StructField(x, IntegerType, nullable = true)
      }else if( typeName.toUpperCase.equals("XMLTYPE")) {
        sf = StructField(x, IntegerType, nullable = true)
      }else {
        sf = StructField(x, StringType, nullable = true)
      }
      num+=1
      sf
    })

    val schemaNew: StructType = StructType(fields)
    val rows: List[Row] = rowsArr.toList.map(arr => {

      val row: Row = Row.fromSeq(arr)
      row
    })
    val rdd: RDD[Row] = session.sparkContext.makeRDD(rows)
    val df: DataFrame = session.createDataFrame(rdd,schemaNew)

    out.write(df)
  }

  def initialize(ctx: ProcessContext): Unit = {

  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    user = MapUtil.get(map,"user").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    sql = MapUtil.get(map,"sql").asInstanceOf[String]
    schema = MapUtil.get(map,"schema").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The Url, for example jdbc:oracle:thin:@192.168.0.1:1521/newdb")
      .defaultValue("")
      .required(true)
      .example("jdbc:oracle:thin:@192.168.0.1:1521/newdb")
    descriptor = url :: descriptor

    val user=new PropertyDescriptor()
      .name("user")
      .displayName("User")
      .description("The user name of database")
      .defaultValue("")
      .required(true)
      .example("root")
    descriptor = user :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of database")
      .defaultValue("")
      .required(true)
      .example("123456")
    descriptor = password :: descriptor

    val sql=new PropertyDescriptor()
      .name("sql")
      .displayName("Sql")
      .description("The sql you want")
      .defaultValue("")
      .required(true)
      .language(Language.Sql)
      .example("select * from type")
    descriptor = sql :: descriptor

    val schema=new PropertyDescriptor()
      .name("schema")
      .displayName("Schema")
      .description("The name of the field of your SQL statement query, such as: ID.number, name.varchar")
      .defaultValue("")
      .required(true)
      .example("ID.number, name.varchar")
    descriptor = schema :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/jdbc/jdbcReadFromOracle.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.JdbcGroup)
  }


}
