package cn.piflow.bundle

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.junit.Test

import scala.util.parsing.json.JSON

class HttpTest {
  @Test
  def testFlow(): Unit ={

    //parse flow json
    val file = "src/main/resources/http.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()

    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("piflow-hive-bundle-xx")
      .config("spark.driver.memory", "4g")
      .config("spark.executor.memory", "4g")
      .config("spark.cores.max", "4")
      .config("spark.jars","/root/piflow/piflow/out/artifacts/piflow_jar/piflow-jar.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }
}
