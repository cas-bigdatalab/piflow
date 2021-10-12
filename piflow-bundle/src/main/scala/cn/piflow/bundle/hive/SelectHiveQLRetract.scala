package cn.piflow.bundle.hive

import cn.piflow.{JobContext, JobInputStream, JobOutputStream, ProcessContext}
import cn.piflow.conf.{ConfigurableStop, Language, Port, StopGroup}
import cn.piflow.conf.bean.PropertyDescriptor
import cn.piflow.conf.util.{ImageUtil, MapUtil}
import org.apache.flink.streaming.api.scala._
import org.apache.flink.table.api._
import org.apache.flink.table.api.scala._
import org.apache.flink.table.catalog.hive.HiveCatalog
import org.apache.flink.types.Row


class SelectHiveQLRetract extends ConfigurableStop{
  override val authorEmail: String = "qinghua.liao@outlook.com"
  override val description: String = "Execute select clause of hiveQL with RetractStream"
  override val inportList: List[String] = List(Port.DefaultPort)
  override val outportList: List[String] = List(Port.DefaultPort)

  var hiveQL:String = _
  var  database: String = _

  val name            = "myhive"
  val defaultDatabase = "mydatabase"
  val hiveConfDir     = "/piflow-configure/hive-conf"

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit ={

    val env = pec.get[StreamExecutionEnvironment]()
    val settings = EnvironmentSettings.newInstance().useBlinkPlanner().build()

    val tableEnv = StreamTableEnvironment.create(env, settings)

    val hive = new HiveCatalog(name, defaultDatabase, hiveConfDir)

    tableEnv.registerCatalog("myhive", hive)

    tableEnv.useCatalog("myhive")

    import org.apache.flink.table.api.SqlDialect

    tableEnv.getConfig().setSqlDialect(SqlDialect.HIVE)

    tableEnv.useDatabase(database)

    val resultTable = tableEnv.sqlQuery(hiveQL)

    val RetractResultStream: DataStream[(Boolean, Row)] = tableEnv
      .toRetractStream[Row](resultTable)

    out.write(RetractResultStream)

    env.execute("select hiveQL test job with RetractStream")
  }

  override def setProperties(map: Map[String, Any]): Unit = {
    hiveQL = MapUtil.get(map,"hiveQL").asInstanceOf[String]
  }

  override def getPropertyDescriptor(): List[PropertyDescriptor] = {
    var descriptor : List[PropertyDescriptor] = List()
    val hiveQL = new PropertyDescriptor()
      .name("hiveQL")
      .displayName("HiveQL")
      .defaultValue("")
      .allowableValues(Set(""))
      .description("Execute select clause of hiveQL")
      .required(true)
      .language(Language.Text)
      .example("select * from test.user1")
    descriptor = hiveQL :: descriptor
    val database=new PropertyDescriptor()
      .name("database")
      .displayName("DataBase")
      .description("The database name which the hiveQL will execute on")
      .defaultValue("")
      .required(true)
      .example("test")
    descriptor = database :: descriptor

    descriptor
  }

  override def getIcon(): Array[Byte] = {
    ImageUtil.getImage("icon/hive/SelectHiveQL.png")
  }

  override def getGroup(): List[String] = {
    List(StopGroup.HiveGroup)
  }

  override def initialize(ctx: ProcessContext): Unit = {

  }

}

