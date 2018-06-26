import java.io.File

import cn.piflow.element._
import org.junit.Test

class FlowElementTest {
  @Test
  def test1(): Unit = {
    val f = new File("./test1.json");
    val e = new FlowElement();
    FlowElement.saveFile(e, f);
    val e2 = FlowElement.fromFile(f);
  }

}