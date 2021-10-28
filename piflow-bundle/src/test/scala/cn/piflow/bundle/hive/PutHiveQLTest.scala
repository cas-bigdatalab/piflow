package cn.piflow.bundle.hive

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.flink.streaming.api.scala.StreamExecutionEnvironment
import org.apache.flink.table.api.EnvironmentSettings
import org.apache.flink.table.api.scala.StreamTableEnvironment
import org.apache.flink.table.catalog.hive.HiveCatalog
import org.junit.Test
import org.h2.tools.Server

import scala.util.parsing.json.JSON

class PutHiveQLTest {

  @Test
  def testFlow(): Unit = {

    //parse flow json
    val file = "src/main/resources/flow/hive/PutHiveQL.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort", "50001").start()

    val name            = "myhive"
    val defaultDatabase = "mydatabase"
    val hiveConfDir     = "/piflow-configure/hive-conf"

    //execute flow
    val env = StreamExecutionEnvironment.getExecutionEnvironment
    val settings = EnvironmentSettings.newInstance().useBlinkPlanner().build()
    //create a TableEnvironment for specific planner streaming
    val tableEnv = StreamTableEnvironment.create(env, settings)

    val hive = new HiveCatalog(name, defaultDatabase, hiveConfDir)
    tableEnv.registerCatalog("myhive", hive)

    // set the HiveCatalog as the current catalog of the session
    tableEnv.useCatalog("myhive")

    val process = Runner.create()
      .bind(classOf[StreamExecutionEnvironment].getName,env)
      .bind("checkpoint.path", "")
      .bind("debug.path","")
      .start(flow)

    process.awaitTermination()
    val pid = process.pid()
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
  }

}

