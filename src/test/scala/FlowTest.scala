import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  private def runFlow(processes: Map[String, Process]) {
    val flow = new Flow();
    processes.foreach(en => flow.addProcess(en._1, en._2));

    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addTrigger(DependencyTrigger.declareDependency("CopyTextFile", "CleanHouse"));
    flow.addTrigger(DependencyTrigger.declareDependency("CountWords", "CopyTextFile"));
    flow.addTrigger(DependencyTrigger.declareDependency("PrintCount", "CountWords"));
    flow.addTrigger(TimerTrigger.cron("0/5 * * * * ? ", "PrintMessage"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    val exe = Runner.run(flow, Map(classOf[SparkSession].getName -> spark));

    exe.start("CleanHouse");
    Thread.sleep(20000);
    exe.stop();
  }

  @Test
  def test1() {
    runFlow(Map(
      "CleanHouse" -> new CleanHouse(),
      "CopyTextFile" -> new CopyTextFile(),
      "CountWords" -> new CountWords(),
      "PrintCount" -> new PrintCount()));
  }

  @Test
  def testProcessError() {
    runFlow(Map(
      "CleanHouse" -> new CleanHouse(),
      "CopyTextFile" -> new Process() {
        def run(pc: ProcessContext): Unit = {
          throw new RuntimeException("this is a bad process!");
        }
      },
      "CountWords" -> new CountWords(),
      "PrintCount" -> new PrintCount()));
  }

  @Test
  def test2() {
    runFlow(Map(
      "CleanHouse" -> new CleanHouse(),
      "CopyTextFile" -> new CopyTextFile(),
      "CountWords" -> SparkETLTest.createProcessCountWords(),
      "PrintCount" -> SparkETLTest.createProcessPrintCount()));
  }
}

class CountWords extends Process {
  def run(pc: ProcessContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.textFile("./out/honglou.txt")
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    count.write.json("./out/wordcount");
    spark.close();
  }
}

class PrintMessage extends Process {
  def run(pc: ProcessContext): Unit = {
    println("*****hello******" + new Date());
  }
}

class CleanHouse extends Process {
  def run(pc: ProcessContext): Unit = {
    FileUtils.deleteDirectory(new File("./out/wordcount"));
    FileUtils.deleteQuietly(new File("./out/honglou.txt"));
  }
}

class CopyTextFile extends Process {
  def run(pc: ProcessContext): Unit = {
    val is = new FileInputStream(new File("/Users/bluejoe/testdata/honglou.txt"));
    val os = new FileOutputStream(new File("./out/honglou.txt"));
    IOUtils.copy(is, os);
  }
}

class PrintCount extends Process {
  def run(pc: ProcessContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.json("./out/wordcount").sort($"count".desc);
    count.show(40);
    spark.close();
  }
}