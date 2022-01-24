package cn.piflow.bundle.testAll

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.junit.Test

import scala.util.parsing.json.JSON

class FtpNewTest {
  @Test
  def ftpNew(): Unit = {

    // parse flow json
    val file = "src/main/resources/ftpNew.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    //    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("DblpParserTest")
      .config("spark.driver.memory", "4g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "3")
      .config("spark.jars", "/opt/work/111/piflow-master/out/artifacts/piflow_bundle/piflow-bundle.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

}
