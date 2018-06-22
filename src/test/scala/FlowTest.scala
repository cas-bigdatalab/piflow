import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import cn.piflow.spark._
import cn.piflow.spark.io._
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  @Test
  def testProcess() {
    val flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    flow.addProcess("CountWords", new CountWords());
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addPath(Path.from("CleanHouse").to("CopyTextFile").to("CountWords").to("PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
  }

  @Test
  def testPipedProcess() {
    val flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("PipedReadTextFile", new PipedReadTextFile());
    flow.addProcess("PipedCountWords", new PipedCountWords());
    flow.addProcess("PipedPrintCount", new PipedPrintCount());

    flow.addPath(Path.from("CleanHouse").to("PipedReadTextFile").to("PipedCountWords").to("PipedPrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
  }

  @Test
  def testMergeProcess() {
    val flow = new FlowImpl();

    flow.addProcess("flow1", new TestDataGeneratorProcess(Seq("a", "b", "c")));
    flow.addProcess("flow2", new TestDataGeneratorProcess(Seq("1", "2", "3")));
    flow.addProcess("zip", new ZipProcess());
    flow.addProcess("print", new PrintDataFrameProcess());

    flow.addPath(Path.from("flow1").to("zip", "", "data1").to("print"));
    flow.addPath(Path.from("flow2").to("zip", "", "data2"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
  }

  @Test
  def testForkProcess() {
    val flow = new FlowImpl();

    flow.addProcess("flow", new TestDataGeneratorProcess(Seq("a", "b", "c", "d")));
    flow.addProcess("fork", new ForkProcess());
    flow.addProcess("print1", new PrintDataFrameProcess());
    flow.addProcess("print2", new PrintDataFrameProcess());

    flow.addPath(Path.from("flow").to("fork").to("print1", "data1", ""));
    flow.addPath(Path.from("fork").to("print2", "data2", ""));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
  }

  @Test
  def testSparkProcess() {
    val flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    //CountWords process is a SparkProcess
    flow.addProcess("CountWords", createProcessCountWords());
    //PrintCount process is a SparkProcess
    flow.addProcess("PrintCount", createProcessPrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addPath(Path.from("CleanHouse").to("CopyTextFile"));
    flow.addPath(Path.from("CopyTextFile").to("CountWords"));
    flow.addPath(Path.from("CountWords").to("PrintCount"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
  }

  @Test
  def testProcessError() {
    val flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    //CopyTextFile process will throw an error
    flow.addProcess("CopyTextFile", new Process() {
      def initialize(ctx: FlowExecutionContext): Unit = {

      }

      def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
        throw new RuntimeException("this is a bad process!");
      }
    });
    //CountWords should not be executed because CopyTextFile is failed
    flow.addProcess("CountWords", new CountWords());
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addPath(Path.from("CleanHouse").to("CopyTextFile"));
    flow.addPath(Path.from("CopyTextFile").to("CountWords"));
    flow.addPath(Path.from("CountWords").to("PrintCount"));

    //flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    flow.print();
    exe.start();
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
    val processCountWords = new SparkProcess();
    //SparkProcess = loadStream + transform... + writeStream
    val s1 = processCountWords.loadStream(TextFile("./out/honglou.txt", FileFormat.TEXT));
    //transform s1 using an map() operation
    val s2 = processCountWords.transform(DoMap(ScriptEngine.logic(SCRIPT_1)), s1);
    //transform s2 using a flatMap() operation
    val s3 = processCountWords.transform(DoFlatMap(ScriptEngine.logic(SCRIPT_2)), s2);
    //transform s3 using a SQL operation
    val s4 = processCountWords.transform(ExecuteSQL(
      "select value, count(*) count from table_0 group by value order by count desc"), s3);

    processCountWords.writeStream(TextFile("./out/wordcount", FileFormat.JSON), s4);
    processCountWords;
  }

  def createProcessPrintCount() = {
    val processPrintCount = new SparkProcess();
    val s1 = processPrintCount.loadStream(TextFile("./out/wordcount", FileFormat.JSON));
    val s2 = processPrintCount.transform(ExecuteSQL(
      "select value from table_0 order by count desc"), s1);

    processPrintCount.writeStream(Console(40), s2);
    processPrintCount;
  }
}

class PrintMessage extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    println("*****hello******" + new Date());
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class CleanHouse extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    FileUtils.deleteDirectory(new File("./out/wordcount"));
    FileUtils.deleteQuietly(new File("./out/honglou.txt"));
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class CopyTextFile extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val is = new FileInputStream(new File("./testdata/honglou.txt"));
    val tmpfile = File.createTempFile(this.getClass.getSimpleName, "");
    val os = new FileOutputStream(tmpfile);
    IOUtils.copy(is, os);
    tmpfile.renameTo(new File("./out/honglou.txt"));
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class PrintCount extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.json("./out/wordcount").sort($"count".desc);
    count.show(40);
    spark.close();
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class CountWords extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    val count = spark.read.textFile("./out/honglou.txt")
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    val tmpfile = File.createTempFile(this.getClass.getName + "-", "");
    tmpfile.delete();
    count.write.json(tmpfile.getAbsolutePath);
    spark.close();
    tmpfile.renameTo(new File("./out/wordcount"));
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class PipedReadTextFile extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();
    val df = spark.read.json("./testdata/honglou.txt");
    out.write(df);
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class PipedCountWords extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    val df = in.read();
    val count = df.as[String]
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    out.write(count);
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}


class PipedPrintCount extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._

    val df = in.read();
    val count = df.sort($"count".desc);
    count.show(40);
    out.write(df);
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class PrintDataFrameProcess extends Process {
  def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();

    val df = in.read();
    df.show(40);
  }

  def initialize(ctx: FlowExecutionContext): Unit = {

  }
}

class TestDataGeneratorProcess(seq: Seq[String]) extends Process {
  override def initialize(ctx: FlowExecutionContext): Unit = {}

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    out.write(seq.toDF());
  }
}

class ZipProcess extends Process {
  override def initialize(ctx: FlowExecutionContext): Unit = {}

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    out.write(in.read("data1").union(in.read("data2")));
  }
}

class ForkProcess extends Process {
  override def initialize(ctx: FlowExecutionContext): Unit = {}

  override def perform(in: ProcessInputStream, out: ProcessOutputStream, pec: ProcessExecutionContext): Unit = {
    val ds = in.read();
    val spark = pec.get[SparkSession]();
    import spark.implicits._
    out.write("data1", ds.as[String].filter(_.head % 2 == 0).toDF());
    out.write("data2", ds.as[String].filter(_.head % 2 == 1).toDF());
  }
}