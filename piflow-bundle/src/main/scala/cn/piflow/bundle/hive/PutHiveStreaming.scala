package cn.piflow.bundle.hive

import cn.piflow._
import cn.piflow.conf._
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.flink.streaming.api.scala._
import org.apache.flink.table.api._
import org.apache.flink.table.api.scala._
import org.apache.flink.table.catalog.hive.HiveCatalog


class PutHiveStreaming extends ConfigurableStop{
  override val authorEmail: String = "qinghua.liao@outlook.com"
  override val description: String = "Save data to hive"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var  database: String = _
  var table:String = _

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    //0.Create the execution environment for the flow
    val env = pec.get[StreamExecutionEnvironment]()
    val settings = EnvironmentSettings.newInstance().useBlinkPlanner().build()
    //create a TableEnvironment for specific planner streaming
    val tableEnv = StreamTableEnvironment.create(env, settings)

    //Read data from upstream
    val inDF = in.read()
    //transform DataStream to Table
    val resultTable: Table = tableEnv.fromDataStream(inDF)
    //create view resultTable
    tableEnv.createTemporaryView("resultTable", resultTable)

    //connect hive by flink
    val name            = "myhive"
    val defaultDatabase = "mydatabase"
    val hiveConfDir     = "/piflow-configure/hive-conf"

    val hive = new HiveCatalog(name, defaultDatabase, hiveConfDir)
    tableEnv.registerCatalog("myhive", hive)

    // set the HiveCatalog as the current catalog of the session
    tableEnv.useCatalog("myhive")
    tableEnv.useDatabase(database)

    //save data to hive
    tableEnv.executeSql("insert into " + database + "." + table +  " select * from " + resultTable)
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    database = MapUtil.get(map, "database").asInstanceOf[String]
    table = MapUtil.get(map, "table").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor: List[PropertyDescriptor] = List()
    val database = new PropertyDescriptor()
      .name("database")
      .displayName("DataBase")
      .description("The database name")
      .defaultValue("")
      .required(true)
    descriptor = database :: descriptor

    val table = new PropertyDescriptor()
      .name("table")
      .displayName("Table")
      .description("The table name")
      .defaultValue("")
      .required(true)
      .example("stream")
    descriptor = table :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/PutHiveStreaming.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup.toString)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}

