package cn.piflow.bundle

import cn.piflow.bundle.jdbc.{JDBCRead, JDBCWrite}
import cn.piflow.{FlowImpl, Path, Runner}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class JDBCTest {

  @Test
  def testMysqlRead(): Unit ={


    val jdbcReadParameters = Map(
      "url" -> "jdbc:mysql://10.0.86.90/sparktest",
      "driver"->"com.mysql.jdbc.Driver",
      "sql"->"select student.id, name, gender, age, score from student, student_score where student.id = student_score.id",
      "user"->"root",
      "password"->"root")

    val jdbcWriteParameters = Map("writeDBtable" -> "student_full")

    val jDBCReadStop = new JDBCRead()
    jDBCReadStop.setProperties(jdbcReadParameters)

    val jDBCWriteStop = new JDBCWrite()
    jDBCWriteStop.setProperties(jdbcWriteParameters)

    val flow = new FlowImpl();
    flow.addStop("JDBCRead", jDBCReadStop);
    flow.addStop("JDBCWrite", jDBCWriteStop);
    flow.addPath(Path.from("JDBCRead").to("JDBCWrite"));

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
