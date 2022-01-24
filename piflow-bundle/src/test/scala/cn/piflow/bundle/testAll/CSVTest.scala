package cn.piflow.bundle.testAll


import cn.piflow.bundle.csv.CsvParser
import cn.piflow.bundle.json.JsonSave
import cn.piflow.{FlowImpl, Path, Runner}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class CSVTest {

  @Test
  def testCSVHeaderRead(): Unit ={

    val csvParserParameters  = Map(
      "csvPath" -> "hdfs://10.0.86.89:9000/xjzhu/student.csv",
      "header" -> "true",
      "delimiter" -> ",",
      "schema" -> "")
    val jsonSaveParameters = Map(
      "jsonPath" -> "hdfs://10.0.86.89:9000/xjzhu/student_csv2json")

    val csvParserStop = new CsvParser
    csvParserStop.setProperties(csvParserParameters)

    val jsonPathStop =new JsonSave
    jsonPathStop.setProperties(jsonSaveParameters)

    val flow = new FlowImpl();

    flow.addStop("CSVParser", csvParserStop);
    flow.addStop("JsonSave", jsonPathStop);
    flow.addPath(Path.from("CSVParser").to("JsonSave"));

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
  def testCSVSchemaRead(): Unit ={

    val csvParserParameters : Map[String, String] = Map(
      "csvPath" -> "hdfs://10.0.86.89:9000/xjzhu/student_schema.csv",
      "header" -> "false",
      "delimiter" -> ",",
      "schema" -> "id,name,gender,age"
    )
    val jsonSaveParameters = Map(
      "jsonPath" -> "hdfs://10.0.86.89:9000/xjzhu/student_schema_csv2json")


    val csvParserStop = new CsvParser
    csvParserStop.setProperties(csvParserParameters)

    val jsonSaveStop = new JsonSave
    jsonSaveStop.setProperties(jsonSaveParameters)

    val flow = new FlowImpl();

    flow.addStop("CSVParser", csvParserStop);
    flow.addStop("JsonSave", jsonSaveStop);
    flow.addPath(Path.from("CSVParser").to("JsonSave"));

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
