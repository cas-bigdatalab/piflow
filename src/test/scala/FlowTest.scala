import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  private def _testFlow1(processCountWords: Process) {
    val flow = new FlowImpl();
    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    flow.addProcess("CountWords", processCountWords);
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addTrigger(DependencyTrigger.dependency("CopyTextFile", "CleanHouse"));
    flow.addTrigger(DependencyTrigger.dependency("CountWords", "CopyTextFile"));
    flow.addTrigger(DependencyTrigger.dependency("PrintCount", "CountWords"));
    flow.addTrigger(TimerTrigger.cron("0/5 * * * * ? ", "PrintMessage"));

    val runner = new RunnerImpl();
    val exe = runner.run(flow, "CleanHouse");

    Thread.sleep(20000);
    exe.stop();
  }

  @Test
  def test1() {
    _testFlow1(new CountWords());

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
  }

  @Test
  def test2() {
    val fg = new SparkETLProcess();
    val node1 = fg.createNode(DoLoad(TextFile("./out/honglou.txt")));
    val node2 = fg.createNode(DoMap(
      """
      function(s){
        return s.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", "");
      }"""));

    val node3 = fg.createNode(DoFlatMap(
      """
      function(s){
        return s.zip(s.drop(1)).map(t => "" + t._1 + t._2);
      }"""));

    val node4 = fg.createNode(DoWrite(JsonFile("./out/wordcount")));
    fg.pipe(node1, node2, node3, node4);

    _testFlow1(fg);
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