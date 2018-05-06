/**
  * Created by bluejoe on 2018/5/6.
  */

import cn.piflow._
import org.junit.Test

class SparkETLTest {
  @Test
  def test1(): Unit = {
    val fg = new SparkETLProcess();
    val s1 = fg.loadStream(TextFile("./out/honglou.txt", "text"));
    val s2 = fg.transform(s1, DoMap(
      """
      function(s){
        return s.replaceAll("[\\x00-\\xff]|，|。|：|．|“|”|？|！|　", "");
      }"""));

    val s3 = fg.transform(s2, DoFlatMap(
      """
      function(s){
        return s.zip(s.drop(1)).map(t => "" + t._1 + t._2);
      }"""));

    fg.writeStream(s3, TextFile("./out/wordcount", "json"));

    fg.run(null);
  }
}
