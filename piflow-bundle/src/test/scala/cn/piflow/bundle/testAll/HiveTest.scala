package cn.piflow.bundle.testAll

import cn.piflow._
import cn.piflow.bundle.hive.{PutHiveStreaming, SelectHiveQL}
import org.apache.spark.sql.SparkSession
import org.junit.Test


class HiveTest {

  val selectHiveQLParameters : Map[String, String] = Map("hiveQL" -> "select * from sparktest.student")
  val putHiveStreamingParameters : Map[String, String] = Map("database" -> "sparktest", "table" -> "studenthivestreaming")

  @Test
  def testHive(): Unit = {

    val selectHiveQLStop = new SelectHiveQL
    selectHiveQLStop.setProperties(selectHiveQLParameters)

    val putHiveStreamingStop = new PutHiveStreaming
    putHiveStreamingStop.setProperties(putHiveStreamingParameters)

    val flow = new FlowImpl();

    flow.addStop("SelectHiveQL", selectHiveQLStop);
    flow.addStop("PutHiveStreaming", putHiveStreamingStop);
    flow.addPath(Path.from("SelectHiveQL").to("PutHiveStreaming"));


    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("piflow-hive-bundle")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars","/opt/project/piflow-jar-bundle/out/artifacts/piflow-jar-bundle/piflow-jar-bundle.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();

  }

}
