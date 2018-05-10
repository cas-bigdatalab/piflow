/**
  * Created by bluejoe on 2018/5/6.
  */

import java.io.File

import cn.piflow._
import cn.piflow.io.{Console, FileFormat, TextFile}
import org.apache.commons.io.FileUtils
import org.apache.spark.sql.SparkSession
import org.junit.Test

object SparkETLTest {
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
    val processCountWords = new SparkETLProcess();
    val s1 = processCountWords.loadStream(TextFile("./out/honglou.txt", FileFormat.TEXT));
    val s2 = processCountWords.transform(DoMap(ScriptEngine.logic(SCRIPT_1)), s1);
    val s3 = processCountWords.transform(DoFlatMap(ScriptEngine.logic(SCRIPT_2)), s2);
    val s4 = processCountWords.transform(ExecuteSQL(
      "select value, count(*) count from table_0 group by value order by count desc"), s3);

    processCountWords.writeStream(TextFile("./out/wordcount", FileFormat.JSON), s4);
    processCountWords;
  }

  def createProcessPrintCount() = {
    val processPrintCount = new SparkETLProcess();
    val s1 = processPrintCount.loadStream(TextFile("./out/wordcount", FileFormat.JSON));
    val s2 = processPrintCount.transform(ExecuteSQL(
      "select value from table_0 order by count desc"), s1);

    processPrintCount.writeStream(Console(40), s2);
    processPrintCount;
  }
}

class SparkETLTest {
  @Test
  def test1(): Unit = {
    FileUtils.deleteDirectory(new File("./out/wordcount"));

    val ctx = new ProcessContext(null);
    ctx.put[SparkSession](SparkSession.builder.master("local[4]")
      .getOrCreate());

    SparkETLTest.createProcessCountWords().run(ctx);
    SparkETLTest.createProcessPrintCount().run(ctx);
  }
}