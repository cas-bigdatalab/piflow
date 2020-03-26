package cn.piflow.bundle.test

import cn.piflow.bundle.csv.CsvParser
import org.junit.Test

class StopGroupTest {

  @Test
  def testCSVGroup(): Unit ={

    val csvParserParameters  = Map(
      "csvPath" -> "hdfs://10.0.86.89:9000/xjzhu/student.csv",
      "header" -> "true",
      "delimiter" -> ",",
      "schema" -> "")

    val csvParserStop = new CsvParser
    csvParserStop.setProperties(csvParserParameters)
    println(csvParserStop.getGroup().toString)
  }

  @Test
  def testFindAllGroup() = {

    //val group = StopGroup.findAllGroup()
    //group.foreach(println)
  }
}
