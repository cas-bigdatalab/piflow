package cn.piflow.bundle.hive

import org.apache.flink.api.scala.ExecutionEnvironment
import org.apache.flink.streaming.api.scala.StreamExecutionEnvironment
import org.apache.flink.table.api.scala.StreamTableEnvironment
import org.apache.flink.table.api.{EnvironmentSettings, Table}
import org.apache.flink.table.catalog.hive.HiveCatalog
import org.junit.Test

class TestMainFunction {
  @Test
  def testFlow(): Unit = {

    val  database: String = database;
    val table:String = table;

    val env = StreamExecutionEnvironment.getExecutionEnvironment
    val settings = EnvironmentSettings.newInstance().useBlinkPlanner().build()
    //create a TableEnvironment for specific planner streaming
    val tableEnv = StreamTableEnvironment.create(env, settings)

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
    tableEnv.executeSql("insert into stu select 11,'wangwu'")
  }

}
