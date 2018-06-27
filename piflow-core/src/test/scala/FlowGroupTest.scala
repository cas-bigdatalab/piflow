import cn.piflow._
import org.apache.spark.sql.SparkSession
import org.junit.Test

/**
  * Created by bluejoe on 2018/6/27.
  */
class FlowGroupTest {
  @Test
  def testProcessGroup() {
    val flow1 = new FlowImpl();

    flow1.addStop("CleanHouse", new CleanHouse());
    flow1.addStop("CopyTextFile", new CopyTextFile());
    flow1.addStop("CountWords", new CountWords());
    flow1.addPath(Path.of("CleanHouse" -> "CopyTextFile" -> "CountWords"));

    val flow2 = new FlowImpl();

    flow2.addStop("PrintCount", new PrintCount());

    val fg = new FlowGroupImpl();
    fg.addFlow("flow1", flow1);
    fg.addFlow("flow2", flow2, Condition.after("flow1"));

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .start(fg);

    process.awaitTermination();
    spark.close();
  }
}
