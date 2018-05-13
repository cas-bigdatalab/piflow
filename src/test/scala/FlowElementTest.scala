import java.io.File

import cn.piflow.FlowElement
import org.junit.Test

class FlowElementTest {
  @Test
  def test1(): Unit = {
    val f = new File("./test1.json");
    val flowJson = new FlowElement();
    FlowElement.saveFile(flowJson, f);
    val flowJson2 = FlowElement.fromFile(f);
  }

}