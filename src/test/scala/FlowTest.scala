import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  @Test
  def test1() {
    val flow = new FlowImpl();
    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    flow.addProcess("CountWords", new CountWords());
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());

    flow.schedule("CopyTextFile", SequenceTriggerBuilder.after("CleanHouse"));
    flow.schedule("CountWords", SequenceTriggerBuilder.after("CopyTextFile"));
    flow.schedule("PrintCount", SequenceTriggerBuilder.after("CountWords"));
    flow.schedule("PrintMessage", TimerTriggerBuilder.cron("0/30 * * * * ? "));

    val runner = new RunnerImpl();
    val exe = runner.run(flow, "CleanHouse");

    Thread.sleep(20000);
    exe.stop();
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