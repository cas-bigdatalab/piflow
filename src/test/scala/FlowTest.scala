import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  @Test
  def test1() {
    val chain = new FlowImpl();
    chain.addProcess("CleanHouse", new CleanHouse());
    chain.addProcess("CopyTextFile", new CopyTextFile());
    chain.addProcess("CountWords", new CountWords());
    chain.addProcess("PrintCount", new PrintCount());
    chain.addProcess("PrintMessage", new PrintMessage());

    chain.trigger("CopyTextFile", SequenceTriggerBuilder.after("CleanHouse"));
    chain.trigger("CountWords", SequenceTriggerBuilder.after("CopyTextFile"));
    chain.trigger("PrintCount", SequenceTriggerBuilder.after("CountWords"));
    chain.trigger("PrintMessage", TimerTriggerBuilder.cron("* * * * * ?"));

    val runner = new RunnerImpl();
    val exe = runner.run(chain, "CleanHouse");

    Thread.sleep(10000);
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