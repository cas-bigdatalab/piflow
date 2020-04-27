package cn.piflow.bundle.neo4j

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.neo4j.driver.v1._


class PutNeo4j extends ConfigurableStop{
  override val authorEmail: String = "yangqidong@cnic.cn"
  override val description: String = "Write DataFrame to neo4j,automatically get the fields name"
  override val inportList: List[String] =List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

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

    val url=new PropertyDescriptor()
      .name("url")
      .displayName("Url")
      .description("The url of neo4j")
      .defaultValue("")
      .required(true)
      .example("bolt://0.0.1.1:7687")
    descriptor = url :: descriptor

    val userName=new PropertyDescriptor()
      .name("userName")
      .displayName("UserName")
      .description("The user of neo4j")
      .defaultValue("")
      .required(true)
      .example("neo4j")
    descriptor = userName :: descriptor

    val password=new PropertyDescriptor()
      .name("password")
      .displayName("Password")
      .description("The password of neo4j")
      .defaultValue("")
      .required(true)
      .example("123456")
    descriptor = password :: descriptor

    val labelName=new PropertyDescriptor()
      .name("labelName")
      .displayName("LabelName")
      .description("The name of the label")
      .defaultValue("")
      .required(true)
      .example("user")
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
