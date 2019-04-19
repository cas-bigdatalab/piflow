import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date
import java.util.concurrent.TimeUnit

import cn.piflow._
import cn.piflow.lib._
import cn.piflow.lib.io._
import cn.piflow.util.ScriptEngine
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  @Test
  def testProcess() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("CopyTextFile", new CopyTextFile());
    flow.addStop("CountWords", new CountWords());
    flow.addStop("PrintCount", new PrintCount());
    flow.addStop("PrintMessage", new PrintMessage());

    flow.addPath(Path.of("CleanHouse" -> "CopyTextFile" -> "CountWords" -> "PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();


    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testStopProcess() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("CopyTextFile", new CopyTextFile());
    flow.addStop("CountWords", new CountWords());
    flow.addStop("PrintCount", new PrintCount());
    flow.addStop("PrintMessage", new PrintMessage());

    flow.addPath(Path.of("CleanHouse" -> "CopyTextFile" -> "CountWords" -> "PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    Thread.sleep(100);
    process.stop();
    spark.close();
  }

  @Test
  def testInterruptProcess() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("CopyTextFile", new CopyTextFile());
    flow.addStop("CountWords", new CountWords());
    flow.addStop("PrintCount", new PrintCount());
    flow.addStop("PrintMessage", new PrintMessage());

    flow.addPath(Path.of("CleanHouse" -> "CopyTextFile" -> "CountWords" -> "PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination(100, TimeUnit.MILLISECONDS);
    process.stop();
    spark.close();
  }

  @Test
  def testPipedProcess() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("PipedReadTextFile", new PipedReadTextFile());
    flow.addStop("PipedCountWords", new PipedCountWords());
    flow.addStop("PipedPrintCount", new PipedPrintCount());

    flow.addPath(Path.from("CleanHouse").to("PipedReadTextFile").to("PipedCountWords").to("PipedPrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testProcessCheckPoint() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("PipedReadTextFile", new PipedReadTextFile());
    flow.addStop("PipedCountWords", new PipedCountWords());
    flow.addStop("PipedPrintCount", new PipedPrintCount());

    flow.addPath(Path.from("CleanHouse").to("PipedReadTextFile").to("PipedCountWords").to("PipedPrintCount"));
    flow.addCheckPoint("PipedReadTextFile");

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "/tmp/piflow/checkpoints/")
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testMergeProcess() {
    val flow = new FlowImpl();

    flow.addStop("flow1", new TestDataGeneratorStop(Seq("a", "b", "c")));
    flow.addStop("flow2", new TestDataGeneratorStop(Seq("1", "2", "3")));
    flow.addStop("zip", new ZipStop());
    flow.addStop("print", new PrintDataFrameStop());

    flow.addPath(Path.from("flow1").via("" -> "data1").to("zip").to("print"));
    flow.addPath(Path.from("flow2").via("" -> "data2").to("zip"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testForkProcess() {
    val flow = new FlowImpl();

    flow.addStop("flow", new TestDataGeneratorStop(Seq("a", "b", "c", "d")));
    flow.addStop("fork", new ForkStop());
    flow.addStop("print1", new PrintDataFrameStop());
    flow.addStop("print2", new PrintDataFrameStop());

    flow.addPath(Path.from("flow").to("fork").via("data1" -> "").to("print1"));
    flow.addPath(Path.from("fork").via("data2" -> "").to("print2"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testFlowAsProcess() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    flow.addStop("CopyTextFile", new CopyTextFile());
    flow.addStop("CountWords", createProcessCountWords());
    flow.addStop("PrintCount", createProcessPrintCount());
    flow.addStop("PrintMessage", new PrintMessage());

    flow.addPath(Path.from("CleanHouse").to("CopyTextFile").to("CountWords").to("PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  @Test
  def testProcessError() {
    val flow = new FlowImpl();

    flow.addStop("CleanHouse", new CleanHouse());
    //CopyTextFile process will throw an error
    flow.addStop("CopyTextFile", new Stop() {
      def initialize(ctx: ProcessContext): Unit = {

      }

      def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
        throw new RuntimeException("this is a bad process!");
      }
    });
    //CountWords should not be executed because CopyTextFile is failed
    flow.addStop("CountWords", new CountWords());
    flow.addStop("PrintCount", new PrintCount());
    flow.addStop("PrintMessage", new PrintMessage());

    flow.addPath(Path.from("CleanHouse").to("CopyTextFile"));
    flow.addPath(Path.from("CopyTextFile").to("CountWords"));
    flow.addPath(Path.from("CountWords").to("PrintCount"));

    //flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(flow);

    process.awaitTermination();
    spark.close();
  }

  val SCRIPT_1 =
    """
		function (row) {
			return $.Row(row.get(0).replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""));
		}
    """;
  val SCRIPT_2 =
    """
		function (row) {
			var arr = $.Array();
			var str = row.get(0);
			var len = str.length;
			for (var i = 0; i < len - 1; i++) {
				arr.add($.Row(str.substring(i, i + 2)));
			}

			return arr;
		}
    """;

  def createProcessCountWords() = {
    val processCountWords = new FlowImpl();
    //SparkProcess = loadStream + transform... + writeStream
    processCountWords.addStop("LoadStream", new LoadStream(TextFile("../out/honglou.txt", FileFormat.TEXT)));
    processCountWords.addStop("DoMap", new DoMap(ScriptEngine.logic(SCRIPT_1)));
    processCountWords.addStop("DoFlatMap", new DoFlatMap(ScriptEngine.logic(SCRIPT_2)));
    processCountWords.addStop("ExecuteSQL", new ExecuteSQL(
      "select value, count(*) count from table1 group by value order by count desc",
      "" -> "table1"));
    processCountWords.addStop("WriteStream", new WriteStream(new TextFile("../out/wordcount", FileFormat.JSON)));
    processCountWords.addPath(Path.from("LoadStream").to("DoMap").to("DoFlatMap").to("ExecuteSQL").to("WriteStream"));

    new FlowAsStop(processCountWords);
  }

  def createProcessPrintCount() = {
    val processPrintCount = new FlowImpl();

    processPrintCount.addStop("LoadStream", new LoadStream(TextFile("../out/wordcount", FileFormat.JSON)));
    processPrintCount.addStop("ExecuteSQL", new ExecuteSQL(
      "select value from table1 order by count desc",
      "" -> "table1"));
    processPrintCount.addStop("PrintConsole", new WriteStream(Console(40)));
    processPrintCount.addPath(Path.from("LoadStream").to("ExecuteSQL").to("PrintConsole"));

    new FlowAsStop(processPrintCount);
  }
}

class PrintMessage extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    println("*****hello******" + new Date());
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class CleanHouse extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    FileUtils.deleteDirectory(new File("../out/wordcount"));
    FileUtils.deleteQuietly(new File("../out/honglou.txt"));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class CopyTextFile extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val is = new FileInputStream(new File("../testdata/honglou.txt"));
    val tmpfile = File.createTempFile(this.getClass.getSimpleName, "");
    val os = new FileOutputStream(tmpfile);
    IOUtils.copy(is, os);
    tmpfile.renameTo(new File("../out/honglou.txt"));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class PrintCount extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    val count = spark.read.json("../out/wordcount").sort($"count".desc);
    count.show(40);
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class TestStop extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    print("Test Stop!!!!")
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}


class CountWords extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    val count = spark.read.textFile("../out/honglou.txt")
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    val tmpfile = File.createTempFile(this.getClass.getName + "-", "");
    tmpfile.delete();
    count.write.json(tmpfile.getAbsolutePath);
    tmpfile.renameTo(new File("../out/wordcount"));
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class PipedReadTextFile extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    val df = spark.read.json("../testdata/honglou.txt");
    out.write(df);
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class PipedCountWords extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    val df = in.read();
    val count = df.as[String]
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    out.write(count);
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}


class PipedPrintCount extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._

    val df = in.read();
    val count = df.sort($"count".desc);
    count.show(40);
    out.write(df);
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class PrintDataFrameStop extends Stop {
  def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();

    val df = in.read();
    df.show(40);
  }

  def initialize(ctx: ProcessContext): Unit = {

  }
}

class TestDataGeneratorStop(seq: Seq[String]) extends Stop {
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    out.write(seq.toDF());
  }
}

class ZipStop extends Stop {
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    out.write(in.read("data1").union(in.read("data2")));
  }
}

class ForkStop extends Stop {
  override def initialize(ctx: ProcessContext): Unit = {}

  override def perform(in: JobInputStream, out: JobOutputStream, pec: JobContext): Unit = {
    val ds = in.read();
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    out.write("data1", ds.as[String].filter(_.head % 2 == 0).toDF());
    out.write("data2", ds.as[String].filter(_.head % 2 == 1).toDF());
  }
}