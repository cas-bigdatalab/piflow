package cn.piflow.bundle.neo4j

import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import cn.piflow.conf.{ConfigurableStop, Port, StopGroup}
import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import org.neo4j.driver.v1._

import scala.collection.mutable


class RunCypher extends ConfigurableStop{
  override val authorEmail: String = "anhong12@cnic.cn"
  override val description: String = "Run cql on neo4j"
  override val inportList: List[String] =List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var url : String =_
  var userName : String =_
  var password : String =_
  var cql : String = ""

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {

    var driver: Driver = GraphDatabase.driver(url, AuthTokens.basic(userName, password))
    var session: Session = null

    try {
      session = driver.session()
      session.run(cql)
    } finally {
      session.close()
      driver.close()
    }
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    url = MapUtil.get(map,"url").asInstanceOf[String]
    userName = MapUtil.get(map,"userName").asInstanceOf[String]
    password = MapUtil.get(map,"password").asInstanceOf[String]
    cql = MapUtil.get(map,"cql").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()

    val url=new PropertyDescriptor().name("url").displayName("url").description("for example bolt://0.0.1.1:7687").defaultValue("").required(true)
    descriptor = url :: descriptor

    val userName=new PropertyDescriptor().name("userName").displayName("userName").description("the user").defaultValue("").required(true)
    descriptor = userName :: descriptor

    val password=new PropertyDescriptor().name("password").displayName("password").description("the password").defaultValue("").required(true)
    descriptor = password :: descriptor

    val cql=new PropertyDescriptor().name("cql").displayName("cql").description(" the Cypher").defaultValue("").required(true)
    descriptor = cql :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/neo4j/RunCypher.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.Neo4jGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }
}