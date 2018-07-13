package cn.piflow.bundle

import cn.piflow.bundle.json.{JsonPathParser, JsonSave}
import cn.piflow.{FlowImpl, Path, Runner}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class JsonTest {

  @Test
  def testJsonPathParser(): Unit ={

    val JsonPathParserParameters = Map("jsonPath"->"hdfs://10.0.86.89:9000/xjzhu/student.json", "tag"->"student")
    val JsonSavePathParameters = Map("jsonSavePath" -> "hdfs://10.0.86.89:9000/xjzhu/example_json_save")

    val flow = new FlowImpl();

    val jsonPathParserStop = new JsonPathParser()
    jsonPathParserStop.setProperties(JsonPathParserParameters)

    val jsonSaveStop = new JsonSave()
    jsonSaveStop.setProperties(JsonSavePathParameters)

    flow.addStop("JsonPathParser", jsonPathParserStop)
    flow.addStop("JsonSave", jsonSaveStop)
    flow.addPath(Path.from("JsonPathParser").to("JsonSave"));

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


  @Test
  def testJsonStringParser(): Unit ={

  }

}
