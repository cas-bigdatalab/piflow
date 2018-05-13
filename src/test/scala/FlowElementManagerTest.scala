import cn.piflow._
import cn.piflow.spark._
import cn.piflow.element._
import org.junit.{Assert, Test}

class FlowElementManagerTest {
  @Test
  def testRAM(): Unit = {
    _testMgr(new InMemoryFlowElementManager().asInstanceOf[FlowElementManager]);
  }

  @Test
  def testSql(): Unit = {
    _testMgr(new SqlFlowElementManager().asInstanceOf[FlowElementManager]);
  }

  @Test
  def testDir(): Unit = {
    _testMgr(new FileSystemFlowElementManager().asInstanceOf[FlowElementManager]);
  }

  def _testMgr(man: FlowElementManager): Unit = {
    //clear all first
    man.list().foreach(x => man.delete(x._1));

    Assert.assertEquals(0, man.list().size);
    man.add("test", new FlowElement());
    Assert.assertEquals(1, man.list().size);
    Assert.assertEquals("test", man.list().head._1);
    Assert.assertNotNull(man.get("test"));
    Assert.assertNull(man.get("test2"));
    man.delete("test");
    Assert.assertEquals(0, man.list().size);
  }

}