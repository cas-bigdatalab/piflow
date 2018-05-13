import java.io.{File, FileInputStream, FileOutputStream}
import java.util.Date

import cn.piflow._
import cn.piflow.io.{Console, FileFormat, TextFile}
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class FlowTest {
  private def runFlow(processes: Map[String, Process]) {
    val flow: Flow = new FlowImpl();
    processes.foreach(en => flow.addProcess(en._1, en._2));

    flow.addProcess("PrintMessage", new PrintMessage());

    flow.addTrigger("CopyTextFile", new DependencyTrigger("CleanHouse"));
    flow.addTrigger("CountWords", new DependencyTrigger("CopyTextFile"));
    flow.addTrigger("PrintCount", new DependencyTrigger("CountWords"));
    flow.addTrigger("PrintMessage", new TimerTrigger("0/5 * * * * ? "));

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
        override def onPrepare(pec: ProcessExecutionContext): Unit =
          throw new RuntimeException("this is a bad process!");

        override def onRollback(pec: ProcessExecutionContext): Unit = ???

        override def onFail(errorStage: ProcessStage, cause: Throwable, pec: ProcessExecutionContext): Unit = ???

        override def onCommit(pec: ProcessExecutionContext): Unit = ???
      },
      "CountWords" -> new CountWords(),
      "PrintCount" -> new PrintCount()));
  }

  @Test
  def testSparkProcess() {
    runFlow(Map(
      "CleanHouse" -> new CleanHouse(),
      "CopyTextFile" -> new CopyTextFile(),
      "CountWords" -> createProcessCountWords(),
      "PrintCount" -> createProcessPrintCount()));
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

class CountWords extends LazyProcess {
  override def onPrepare(pec: ProcessExecutionContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.textFile("./out/honglou.txt")
      .map(_.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", ""))
      .flatMap(s => s.zip(s.drop(1)).map(t => "" + t._1 + t._2))
      .groupBy("value").count.sort($"count".desc);

    val tmpfile = File.createTempFile(this.getClass.getSimpleName, "");
    pec.put("tmpfile", tmpfile);

    count.write.json(tmpfile.getAbsolutePath);
    spark.close();
  }

  override def onCommit(pec: ProcessExecutionContext): Unit = {
    pec.get("tmpfile").asInstanceOf[File].renameTo(new File("./out/wordcount"));
  }

  override def onRollback(pec: ProcessExecutionContext): Unit = {
    pec.get("tmpfile").asInstanceOf[File].delete();
  }
}

class PrintMessage extends LazyProcess {
  def onCommit(pc: ProcessExecutionContext): Unit = {
    println("*****hello******" + new Date());
  }
}

class CleanHouse extends LazyProcess {
  def onCommit(pc: ProcessExecutionContext): Unit = {
    FileUtils.deleteDirectory(new File("./out/wordcount"));
    FileUtils.deleteQuietly(new File("./out/honglou.txt"));
  }
}

class CopyTextFile extends LazyProcess {
  override def onPrepare(pec: ProcessExecutionContext): Unit = {
    val is = new FileInputStream(new File("/Users/bluejoe/testdata/honglou.txt"));
    val tmpfile = File.createTempFile(this.getClass.getSimpleName, "");
    pec.put("tmpfile", tmpfile);
    val os = new FileOutputStream(tmpfile);
    IOUtils.copy(is, os);
  }

  override def onCommit(pec: ProcessExecutionContext): Unit = {
    pec.get("tmpfile").asInstanceOf[File].renameTo(new File("./out/honglou.txt"));
  }

  override def onRollback(pec: ProcessExecutionContext): Unit = {
    pec.get("tmpfile").asInstanceOf[File].delete();
  }
}

class PrintCount extends LazyProcess {
  def onCommit(pc: ProcessExecutionContext): Unit = {
    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();
    import spark.implicits._
    val count = spark.read.json("./out/wordcount").sort($"count".desc);
    count.show(40);
    spark.close();
  }
}