import java.io.{File, FileInputStream, FileOutputStream}

import cn.piflow.{ChainImpl, Process, ProcessContext, RunnerImpl}
import org.apache.commons.io.{FileUtils, IOUtils}
import org.apache.spark.sql.SparkSession
import org.junit.Test

class ChainTest {
  @Test
  def test1() {
    val chain = new ChainImpl();
    val id1 = chain.addProcess("CopyTextFile", new CopyTextFile(), "comment");
    val id2 = chain.addProcess("CountWords", new CountWords());
    val id3 = chain.addProcess("PrintCount", new PrintCount());

    chain.scheduleAfter( id2,id1);
    chain.scheduleAfter(id3,id2);
    chain.scheduleAt(1000);

    val runner = new RunnerImpl();
    val exe = runner.run(chain, id1);

    FileUtils.deleteDirectory(new File("./out/wordcount"));
    FileUtils.deleteQuietly(new File("./out/honglou.txt"));
    exe.awaitComplete();
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