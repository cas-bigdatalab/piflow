package cn.piflow.bundle.testAll

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.junit.Test

import scala.util.parsing.json.JSON

class JsonFolderTest {

  @Test
  def testFlow(): Unit ={

//测试数据
/*    {
      "name": "BeJson",
      "url": "http://www.bejson.com",
      "page": 88,
      "isNonProfit": true,
      "address": {
        "street": "科技园路.",
        "city": "江苏苏州",
        "country": "中国"
      },
      "links": [
      {
        "name": "Google",
        "url": "http://www.google.com"
      },
      {
        "name": "Baidu",
        "url": "http://www.baidu.com"
      },
      {
        "name": "SoSo",
        "url": "http://www.SoSo.com"
      }
      ]
    }*/



    //parse flow json
    val file = "src/main/resources/JsonFolderTest.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]
    println(map)

    //create flow
    val flowBean = FlowBean(map)
    val flow = flowBean.constructFlow()


    //execute flow
    val spark = SparkSession.builder()
      .master("spark://10.0.86.89:7077")
      .appName("piflow-hive-bundle")
      .config("spark.driver.memory", "1g")
      .config("spark.executor.memory", "2g")
      .config("spark.cores.max", "2")
      .config("spark.jars","/opt/project/gitwork/out/artifacts/piflow_bundle/piflow_bundle.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .start(flow);

    process.awaitTermination();
    val pid = process.pid();
    println(pid + "!!!!!!!!!!!!!!!!!!!!!")
    spark.close();
  }
  @Test
  def testFlow2json() = {

    //parse flow json
    val file = "src/main/resources/flow.json"
    val flowJsonStr = FileUtil.fileReader(file)
    val map = OptionUtil.getAny(JSON.parseFull(flowJsonStr)).asInstanceOf[Map[String, Any]]

    //create flow
    val flowBean = FlowBean(map)
    val flowJson = flowBean.toJson()
    println(flowJson)
  }

}
