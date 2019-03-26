package cn.piflow.bundle.neo4j

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, PortEnum, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.neo4j.driver.v1._


class PutNeo4j extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Put data to Neo4j"
  override val inportList: List[String] =List(PortEnum.DefaultPort.toString)
  override val outportList: List[String] = List(PortEnum.NonePort.toString)

  var url : String =_
  var userName : String =_
  var password : String =_
  var labelName : String =""

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark: SparkSession = pec.get[SparkSession]()
    val inDf: DataFrame = in.read()

    val fileNames: Array[String] = inDf.columns

    var driver: Driver = GraphDatabase.driver(url,AuthTokens.basic(userName,password))
    var session: Session = null
    var transaction: Transaction = null
    var result: StatementResult = null
    var cypher: String = ""
    var fileData: String = ""
    var n = 0
    try {
      session = driver.session()
      transaction = session.beginTransaction()
      inDf.collect .foreach(row =>{
        n = n+1
        cypher = "create(a:"+labelName+"{"
        for(x <- (0 until fileNames.size)){
          cypher += (fileNames(x) + ":\"")
          fileData = row.getAs[String](fileNames(x))

          if( fileData != null){
            fileData = fileData.replace("\\","\\\\") .replace("\"","\\\"")
          }

          cypher += fileData
          cypher += """","""
        }
        cypher = cypher.substring(0,cypher.length-1)
        cypher += "})"
        transaction.run(cypher)
        transaction.success()
        if(n == 500){
          transaction.close()
          transaction = session.beginTransaction()
          n = 0
        }
      })
    }finally {
      transaction.close()
      session.close()
      driver.close()
    }
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    userName = MapUtil.get(map,"userName").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    labelName = MapUtil.get(map,"labelName").asInstanceOf[String]
}

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor().name("url").displayName("url").description("for example bolt://0.0.1.1:7687").defaultValue("").required(true)
    descriptor = url :: descriptor

    val userName=new PropertyDescriptor().name("userName").displayName("userName").description("the user").defaultValue("").required(true)
    descriptor = userName :: descriptor

    val password=new PropertyDescriptor().name("password").displayName("password").description("the password").defaultValue("").required(true)
    descriptor = password :: descriptor

    val labelName=new PropertyDescriptor().name("labelName").displayName("labelName").description("the name of the label").defaultValue("").required(true)
    descriptor = labelName :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/neo4j/PutNeo4j.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Neo4jGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}
