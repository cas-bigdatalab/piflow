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
  def test1() {
    val flow: Flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    flow.addProcess("CountWords", new CountWords());
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());
    flow.addTrigger("CopyTextFile", new DependencyTrigger("CleanHouse"));
    flow.addTrigger("CountWords", new DependencyTrigger("CopyTextFile"));
    flow.addTrigger("PrintCount", new DependencyTrigger("CountWords"));
    flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    exe.start("CleanHouse");
    Thread.sleep(30000);
    exe.stop();
  }

  @Test
  def testProcessError() {
    val flow: Flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new PartialProcess() {
      override def perform(pec: ProcessExecutionContext): Unit =
        throw new RuntimeException("this is a bad process!");
    });
    flow.addProcess("CountWords", new CountWords());
    flow.addProcess("PrintCount", new PrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());
    flow.addTrigger("CopyTextFile", new DependencyTrigger("CleanHouse"));
    flow.addTrigger("CountWords", new DependencyTrigger("CopyTextFile"));
    flow.addTrigger("PrintCount", new DependencyTrigger("CountWords"));
    flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    exe.start("CleanHouse");
    Thread.sleep(30000);
    exe.stop();
  }

  @Test
  def testSparkProcess() {
    val flow: Flow = new FlowImpl();

    flow.addProcess("CleanHouse", new CleanHouse());
    flow.addProcess("CopyTextFile", new CopyTextFile());
    flow.addProcess("CountWords", createProcessCountWords());
    flow.addProcess("PrintCount", createProcessPrintCount());
    flow.addProcess("PrintMessage", new PrintMessage());
    flow.addTrigger("CopyTextFile", new DependencyTrigger("CleanHouse"));
    flow.addTrigger("CountWords", new DependencyTrigger("CopyTextFile"));
    flow.addTrigger("PrintCount", new DependencyTrigger("CountWords"));
    flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val exe = Runner.bind("localBackupDir", "/tmp/")
      .bind(classOf[SparkSession].getName, spark)
      .run(flow);

    exe.start("CleanHouse");
    Thread.sleep(30000);
    exe.stop();
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
    val s1 = processCountWords.loadStream(TextFile("./out/honglou.txt", FileFormat.TEXT));
    val s2 = processCountWords.transform(DoMap(ScriptEngine.logic(SCRIPT_1)), s1);
    val s3 = processCountWords.transform(DoFlatMap(ScriptEngine.logic(SCRIPT_2)), s2);
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

class CountWords extends Process {
  override def shadow(pec: ProcessExecutionContext) = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.textFile("./out/honglou.txt")
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    val tmpfile = File.createTempFile(this.getClass.getName + "-", "");
    tmpfile.delete();

    new Shadow {
      override def discard(pec: ProcessExecutionContext): Unit = {
        tmpfile.delete();
      }

      override def perform(pec: ProcessExecutionContext): Unit = {
        count.write.json(tmpfile.getAbsolutePath);
        spark.close();
      }

      override def commit(pec: ProcessExecutionContext): Unit = {
        tmpfile.renameTo(new File("./out/wordcount"));
      }
    };

  }

  def backup(pec: ProcessExecutionContext): Backup = {
    new Backup() {
      def undo(pec: ProcessExecutionContext) =
        FileUtils.deleteDirectory(new File("./out/wordcount"));
    };
  }
}

class PrintMessage extends PartialProcess {
  def perform(pc: ProcessExecutionContext): Unit = {
    println("*****hello******" + new Date());
  }
}

class CleanHouse extends PartialProcess {
  def perform(pc: ProcessExecutionContext): Unit = {
    FileUtils.deleteDirectory(new File("./out/wordcount"));
    FileUtils.deleteQuietly(new File("./out/honglou.txt"));
  }
}

class CopyTextFile extends Process {
  override def shadow(pec: ProcessExecutionContext) = {
    val is = new FileInputStream(new File("./testdata/honglou.txt"));
    val tmpfile = File.createTempFile(this.getClass.getSimpleName, "");

    new Shadow {
      override def discard(pec: ProcessExecutionContext): Unit = {
        tmpfile.delete();
      }

      override def perform(pec: ProcessExecutionContext): Unit = {
        val os = new FileOutputStream(tmpfile);
        IOUtils.copy(is, os);
      }

      override def commit(pec: ProcessExecutionContext): Unit = {
        tmpfile.renameTo(new File("./out/honglou.txt"));
      }
    };
  }

  def backup(pec: ProcessExecutionContext) = {
    new Backup() {
      def undo(pec: ProcessExecutionContext) =
        new File("./out/honglou.txt").delete();
    };
  }
}

class PrintCount extends PartialProcess {
  def perform(pc: ProcessExecutionContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.json("./out/wordcount").sort($"count".desc);
    count.show(40);
    spark.close();
  }
}