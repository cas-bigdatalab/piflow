import cn.piflow._
import org.apache.spark.sql.SparkSession
import org.h2.tools.Server
import org.junit.Test


class ProjectTest {
  @Test
  def testProject() {
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


    val flow3 = new FlowImpl();
    flow3.addStop("TestStop", new TestStop());

    val flow4 = new FlowImpl();
    flow4.addStop("TestStop", new TestStop());

    val project = new ProjectImpl();

    project.addProjectEntry("flow3",flow3)
    project.addProjectEntry("flowGroup",fg,Condition.after("flow3"))
    project.addProjectEntry("flow4",flow4, Condition.after("flowGroup"))

    val h2Server = Server.createTcpServer("-tcp", "-tcpAllowOthers", "-tcpPort","50001").start()

    val spark = SparkSession.builder.master("local[4]")
      .getOrCreate();

    val process = Runner.create()
      .bind(classOf[SparkSession].getName, spark)
      .bind("checkpoint.path", "hdfs://10.0.86.89:9000/xjzhu/piflow/checkpoints/")
      .bind("debug.path","hdfs://10.0.86.89:9000/xjzhu/piflow/debug/")
      .start(project);

    process.awaitTermination();
    spark.close();
  }
}
