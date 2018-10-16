package cn.piflow.bundle

import cn.piflow.Runner
import cn.piflow.conf.bean.FlowBean
import cn.piflow.conf.util.{FileUtil, OptionUtil}
import org.apache.spark.sql.SparkSession
import org.junit.Test

import scala.util.parsing.json.JSON

class EsTest {

  @Test
  def testFetchEs():Unit ={
    val file = "src/main/resources/esGet.json"
    //解析json
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
      .config("spark.jars", "/opt/project/piflow-master/out/artifacts/piflow_bundle/piflow_bundle.jar")
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow)

    process.awaitTermination()
    spark.close()

  }





  @Test
  def testPutEs(): Unit = {

    val file = "src/main/resources/es.json"
    //解析json
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
      .config("spark.jars", "/opt/project/piflow-master/out/artifacts/piflow_bundle/piflow_bundle.jar")
      //.config("spark.jars","/root/.m2/repository/org/elasticsearch/elasticsearch-spark-20_2.11/5.6.3/elasticsearch-spark-20_2.11-5.6.3.jar")
      .config("es.index.auto.create", "true")  //开启自动创建索引
      .config("es.nodes","10.0.86.239")    //es的节点
      .config("es.port","9200")                //端口号
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow)

    process.awaitTermination()
    spark.close()

  }

  @Test
  def queryEs(): Unit = {
    val file = "src/main/resources/esQurry.json"
    //解析json
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
      .config("spark.jars", "/opt/project/piflow-master/out/artifacts/piflow_bundle/piflow_bundle.jar")
      .config("es.index.auto.create", "true")  //开启自动创建索引
      .config("es.nodes","10.0.86.239")    //es的节点
      .config("es.port","9200")                //端口号
      .enableHiveSupport()
      .getOrCreate()

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow)

    process.awaitTermination()
    spark.close()


  }

}
